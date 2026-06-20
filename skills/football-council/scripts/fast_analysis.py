# -*- coding: utf-8 -*-
"""
FC Petrzalka vs OFK Banik Lehota - Optimized Analysis Pipeline
Single script: CGMBet26 + Bet Angel API v1.0 (POST) + Sofascore in parallel
Saves team cache to avoid repeated DB queries
"""
import sqlite3, json, time, requests, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi import requests as cf_requests

CGMDB = r'C:\Users\zhuju\AppData\Roaming\CGMBetSystem\CGMBetStats_v3.db'
CACHE_FILE = r'C:\Users\zhuju\.qclaw\workspace\_team_stats_cache.json'
BA_BASE = "http://localhost:9000/api"

TODAY = '2026-04-22'

# =====================================================================
# PARALLEL WORKERS
# =====================================================================

def cgmbet_query(sql, params=()):
    """Run a CGMBet26 SQLite query. Thread-safe (each call gets own conn)."""
    conn = sqlite3.connect(CGMDB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def worker_cgmbet_teams(team1_name, team2_name):
    """Find team IDs and names in CGMBet26"""
    conn = sqlite3.connect(CGMDB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT Id, Name FROM Teams WHERE Name LIKE ? OR Name LIKE ?",
                (f"%{team1_name}%", f"%{team2_name}%"))
    teams = [dict(r) for r in cur.fetchall()]
    conn.close()
    return teams

def worker_cgmbet_stats(team_id):
    """Get full stats for a team from CGMBet26"""
    conn = sqlite3.connect(CGMDB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # All finished matches
    cur.execute(f"""
        SELECT m.Date, m.HomeTeamId, m.AwayTeamId, t1.Name as HomeName, t2.Name as AwayName,
               m.HomeGoals, m.AwayGoals, m.StatusCode,
               CASE WHEN m.HomeTeamId = '{team_id}' THEN 1 ELSE 0 END as is_home,
               CASE WHEN m.HomeTeamId = '{team_id}' THEN m.HomeGoals ELSE m.AwayGoals END as tg,
               CASE WHEN m.HomeTeamId = '{team_id}' THEN m.AwayGoals ELSE m.HomeGoals END as og
        FROM Matches m
        JOIN Teams t1 ON m.HomeTeamId = t1.Id
        JOIN Teams t2 ON m.AwayTeamId = t2.Id
        WHERE (m.HomeTeamId = '{team_id}' OR m.AwayTeamId = '{team_id}')
          AND m.StatusCode = 1
        ORDER BY m.Date DESC
        LIMIT 30
    """)
    matches = [dict(r) for r in cur.fetchall()]

    # Goals stats (season)
    cur.execute(f"""
        SELECT m.HomeGoals, m.AwayGoals,
               CASE WHEN m.HomeTeamId = '{team_id}' THEN m.HomeGoals ELSE m.AwayGoals END as tg,
               CASE WHEN m.HomeTeamId = '{team_id}' THEN m.AwayGoals ELSE m.HomeGoals END as og
        FROM Matches m
        WHERE (m.HomeTeamId = '{team_id}' OR m.AwayTeamId = '{team_id}')
          AND m.StatusCode = 1
          AND m.Date >= '2025-08-01'
    """)
    season = [dict(r) for r in cur.fetchall()]

    conn.close()
    return matches, season

def worker_cgmbet_h2h(id1, id2):
    """Get H2H matches"""
    conn = sqlite3.connect(CGMDB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"""
        SELECT m.Date, t1.Name as HomeName, t2.Name as AwayName,
               m.HomeGoals, m.AwayGoals, m.StatusCode
        FROM Matches m
        JOIN Teams t1 ON m.HomeTeamId = t1.Id
        JOIN Teams t2 ON m.AwayTeamId = t2.Id
        WHERE (m.HomeTeamId = '{id1}' AND m.AwayTeamId = '{id2}')
           OR (m.HomeTeamId = '{id2}' AND m.AwayTeamId = '{id1}')
        ORDER BY m.Date DESC
        LIMIT 10
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def worker_betangel_markets():
    """Get all available Bet Angel markets (POST method)"""
    try:
        r = requests.post(
            f"{BA_BASE}/markets/v1.0/getMarkets",
            json={"dataRequired": ["ID","NAME","MARKET_START_TIME","MARKET_INPLAY_STATUS"]},
            headers={"Content-Type":"application/json","Accept":"application/json"},
            timeout=6
        )
        data = r.json()
        if data.get("status") == "OK":
            return data.get("result", {}).get("markets", [])
    except Exception as e:
        return [{"error": str(e)}]

def worker_betangel_prices(market_ids):
    """Get prices for specific market IDs"""
    if not market_ids:
        return []
    try:
        r = requests.post(
            f"{BA_BASE}/markets/v1.0/getMarketPrices",
            json={
                "marketsFilter": {"filter": "SPECIFIED_IDS", "ids": market_ids},
                "dataRequired": ["BEST_THREE_PRICES","INPLAY_INFO","LAST_TRADED_PRICE"]
            },
            headers={"Content-Type":"application/json","Accept":"application/json"},
            timeout=6
        )
        data = r.json()
        if data.get("status") == "OK":
            return data.get("result", {}).get("markets", [])
    except Exception as e:
        return [{"error": str(e)}]

def worker_betangel_balance():
    """Get Betfair balance"""
    try:
        r = requests.post(
            f"{BA_BASE}/markets/v1.0/getBalance",
            json={},
            headers={"Content-Type":"application/json","Accept":"application/json"},
            timeout=5
        )
        data = r.json()
        return data.get("result", {}).get("balance", 0)
    except:
        return 0

def worker_sofascore_events(date):
    """Get Sofascore events for a date"""
    try:
        s = cf_requests.Session(impersonate='chrome')
        r = s.get(f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date}", timeout=6)
        return r.json().get("events", [])
    except:
        return []

def worker_sofascore_match(sf_id):
    """Get Sofascore match details"""
    try:
        s = cf_requests.Session(impersonate='chrome')
        r = s.get(f"https://api.sofascore.com/api/v1/event/{sf_id}/details", timeout=6)
        return r.json()
    except:
        return {}

# =====================================================================
# ANALYSIS HELPERS
# =====================================================================

def calc_form(matches):
    if not matches: return {'w':0,'d':0,'l':0,'gf':0,'ga':0,'form':'','n':0}
    w=d=l=gf=ga=0
    form = []
    for m in matches:
        tg = m.get('tg') or 0
        og = m.get('og') or 0
        gf += tg; ga += og
        if tg > og: w += 1; form.append('W')
        elif tg == og: d += 1; form.append('D')
        else: l += 1; form.append('L')
    return {'w':w,'d':d,'l':l,'gf':gf,'ga':ga,'form':''.join(form),'n':len(matches)}

def calc_goal_stats(matches):
    if not matches: return {}
    tgs = [m['tg'] for m in matches if m['tg'] is not None]
    ogs = [m['og'] for m in matches if m['og'] is not None]
    o25 = sum(1 for m in matches if m['tg'] is not None and m['og'] is not None and (m['tg']+m['og']) >= 3)
    btts = sum(1 for m in matches if m['tg'] is not None and m['og'] is not None and m['tg'] > 0 and m['og'] > 0)
    n = len(matches)
    return {
        'n': n,
        'avg_scored': round(sum(tgs)/len(tgs),2) if tgs else 0,
        'avg_conceded': round(sum(ogs)/len(ogs),2) if ogs else 0,
        'over25': f"{o25}/{n} ({100*o25/n:.0f}%)",
        'btts_yes': f"{btts}/{n} ({100*btts/n:.0f}%)",
        'clean_sheets': f"{ogs.count(0)}/{len(ogs)} ({100*ogs.count(0)/len(ogs):.0f}%)",
        'failed_to_score': f"{tgs.count(0)}/{len(tgs)} ({100*tgs.count(0)/len(tgs):.0f}%)",
    }

def kelly_fraction(odds, true_prob, kelly_mult=0.5):
    """Kelly Criterion: f* = (bp - q) / b"""
    if odds <= 1: return 0
    b = odds - 1
    p = true_prob
    q = 1 - p
    f = (b * p - q) / b
    return max(0, kelly_mult * f)

def estimate_true_odds_v2(t1_home, t1_away, t2_home, t2_away, t1_recent, t2_recent, t1_gstats, t2_gstats):
    """
    True odds using xG Poisson model + form adjustments.
    t1 = home team, t2 = away team.
    """
    # Expected goals at home for team 1
    t1_home_xg_scored = t1_home['gf'] / max(t1_home['n'], 1)
    t1_home_xg_conceded = t1_home['ga'] / max(t1_home['n'], 1)
    t2_away_xg_scored = t2_away['gf'] / max(t2_away['n'], 1)
    t2_away_xg_conceded = t2_away['ga'] / max(t2_away['n'], 1)

    # Adjust for recent form (last 5)
    t1_recent_n = min(t1_recent['n'], 5)
    t2_recent_n = min(t2_recent['n'], 5)
    t1_recent_wr = (t1_recent['w'] / max(t1_recent['n'], 1)) if t1_recent_n > 0 else 0.5
    t2_recent_wr = (t2_recent['w'] / max(t2_recent['n'], 1)) if t2_recent_n > 0 else 0.3

    # xG for this match: team 1 at home
    # team 1 scores: average of home xG scored + away xG conceded
    lam1 = max(0.5, min(3.5, (t1_home_xg_scored * 0.6 + t2_away_xg_conceded * 0.4)))
    # team 2 scores: average of away xG scored + home xG conceded
    lam2 = max(0.5, min(3.5, (t2_away_xg_scored * 0.6 + t1_home_xg_conceded * 0.4)))

    # Poisson probabilities
    import math
    def poisson(k, lam):
        return math.exp(-lam) * (lam ** k) / math.factorial(k)

    p1_win = 0.0
    p_draw = 0.0
    p2_win = 0.0
    for g1 in range(6):
        p_g1 = poisson(g1, lam1)
        for g2 in range(6):
            p_g2 = poisson(g2, lam2)
            if g1 > g2:
                p1_win += p_g1 * p_g2
            elif g1 == g2:
                p_draw += p_g1 * p_g2
            else:
                p2_win += p_g1 * p_g2

    # Normalize
    total_p = p1_win + p_draw + p2_win
    if total_p > 0:
        p1_win /= total_p
        p_draw /= total_p
        p2_win /= total_p

    # Form adjustment: if recent form strongly differs, adjust by up to 5%
    form_adj = (t1_recent_wr - t2_recent_wr) * 0.05
    p1_win = max(0.15, min(0.85, p1_win + form_adj))
    p2_win = max(0.05, min(0.60, p2_win - form_adj * 0.5))
    p_draw = 1.0 - p1_win - p2_win
    p_draw = max(0.10, min(0.45, p_draw))

    # Re-normalize
    total = p1_win + p_draw + p2_win
    p1_win /= total; p_draw /= total; p2_win /= total

    odds_1 = round(0.97 / p1_win, 2)
    odds_x = round(0.97 / p_draw, 2)
    odds_2 = round(0.97 / p2_win, 2)

    # Over 2.5: weighted historical average + Poisson blend (robust)
    def pct_from_str(s):
        """Parse 'N/MM (XX%)' -> float between 0 and 1. Handles '50%' or '50.0%' formats."""
        s = s.strip()
        if '(' in s:
            inner = s.split('(')[1].rstrip(')').rstrip('%')
        else:
            inner = s.rstrip('%')
        try:
            return float(inner) / 100.0
        except:
            return 0.50
    t1_o25 = pct_from_str(t1_gstats.get('over25', '0%'))
    t2_o25 = pct_from_str(t2_gstats.get('over25', '0%'))
    w1 = t1_gstats.get('n', 10); w2 = t2_gstats.get('n', 10)
    # Get lambda values from the return
    poisson_o25 = sum(
        poisson(g1, lam1) * poisson(g2, lam2)
        for g1 in range(7) for g2 in range(7) if g1 + g2 >= 3
    )
    combined_o25 = 0.35 * poisson_o25 + 0.65 * (t1_o25 * w1 + t2_o25 * w2) / (w1 + w2)
    combined_o25 = min(0.85, max(0.25, combined_o25))
    odds_o25 = round(0.97 / combined_o25, 2)
    prob_o25 = combined_o25

    # BTTS: weighted historical average (most reliable)
    t1_btts = pct_from_str(t1_gstats.get('btts_yes', '0%'))
    t2_btts = pct_from_str(t2_gstats.get('btts_yes', '0%'))
    combined_btts = (t1_btts * w1 + t2_btts * w2) / (w1 + w2)
    # Away team scoring probability reduces BTTS if they score few
    away_score_prob = 1 - pct_from_str(t2_gstats.get('failed_to_score', '0%'))
    combined_btts = 0.8 * combined_btts + 0.2 * away_score_prob * t1_btts
    combined_btts = min(0.85, max(0.25, combined_btts))
    odds_btts = round(0.97 / combined_btts, 2)
    prob_btts = combined_btts

    return {
        'odds_home': odds_1, 'odds_draw': odds_x, 'odds_away': odds_2,
        'prob_home': round(p1_win, 3), 'prob_draw': round(p_draw, 3), 'prob_away': round(p2_win, 3),
        'odds_over25': odds_o25, 'prob_over25': round(prob_o25, 3),
        'odds_btts': odds_btts, 'prob_btts': round(prob_btts, 3),
        'exp_total': round(lam1 + lam2, 2),
        'lam_home': round(lam1, 2), 'lam_away': round(lam2, 2),
    }

# =====================================================================
# MAIN ANALYSIS
# =====================================================================

def full_analysis(team1_name, team2_name, market_keywords=None, use_cache=True):
    """
    Single-call full analysis. Returns dict with all data.
    market_keywords: list of strings to filter Bet Angel markets
    """
    t0 = time.time()
    results = {}

    # --- Try cache first ---
    cache = {}
    if use_cache:
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
        except: pass

    team_ids = {}
    t1_stats, t2_stats = None, None
    h2h_matches = []

    # --- Parallel phase 1: CGMBet26 team lookup ---
    with ThreadPoolExecutor(max_workers=4) as ex:
        f1 = ex.submit(worker_cgmbet_teams, team1_name, team2_name)
        f2 = ex.submit(worker_betangel_markets)
        f3 = ex.submit(worker_betangel_balance)
        f4 = ex.submit(worker_sofascore_events, TODAY)
        f5 = ex.submit(worker_sofascore_events, (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d'))

        teams_raw = f1.result()
        ba_markets = f2.result()
        ba_balance = f3.result()
        sf_today = f4.result()
        sf_tomorrow = f5.result()

    results['ba_balance'] = ba_balance
    results['ba_markets'] = ba_markets
    results['sf_events'] = sf_today + sf_tomorrow

    # Find team IDs
    for t in teams_raw:
        nm = t['Name'].lower()
        if team1_name.lower() in nm and t1_stats is None:
            team_ids['team1'] = t['Id']
            team_ids['team1_name'] = t['Name']
        if team2_name.lower() in nm and t2_stats is None:
            team_ids['team2'] = t['Id']
            team_ids['team2_name'] = t['Name']

    if not team_ids:
        results['error'] = f"Teams not found: {team1_name}, {team2_name}"
        return results

    t1_id = team_ids['team1']
    t2_id = team_ids['team2']
    t1_display = team_ids.get('team1_name', team1_name)
    t2_display = team_ids.get('team2_name', team2_name)

    # --- Parallel phase 2: Stats + H2H ---
    with ThreadPoolExecutor(max_workers=4) as ex:
        f_t1 = ex.submit(worker_cgmbet_stats, t1_id)
        f_t2 = ex.submit(worker_cgmbet_stats, t2_id)
        f_h2h = ex.submit(worker_cgmbet_h2h, t1_id, t2_id)

        t1_raw = f_t1.result()
        t2_raw = f_t2.result()
        h2h_matches = f_h2h.result()

    t1_matches, t1_season = t1_raw
    t2_matches, t2_season = t2_raw

    # --- Process stats ---
    t1_form = calc_form(t1_matches)
    t2_form = calc_form(t2_matches)
    t1_home = calc_form([m for m in t1_matches if m['is_home']])
    t1_away = calc_form([m for m in t1_matches if not m['is_home']])
    t2_home = calc_form([m for m in t2_matches if m['is_home']])
    t2_away = calc_form([m for m in t2_matches if not m['is_home']])
    t1_gstats = calc_goal_stats(t1_season)
    t2_gstats = calc_goal_stats(t2_season)

    # --- True odds estimation using Poisson xG model ---
    true_odds = estimate_true_odds_v2(
        t1_home, t1_away, t2_home, t2_away,
        t1_form, t2_form, t1_gstats, t2_gstats
    )

    # --- Bet Angel market search ---
    keywords = market_keywords or [t1_display.split()[0], t2_display.split()[0]]
    found_markets = []
    if isinstance(ba_markets, list):
        for m in ba_markets:
            nm = m.get('name', '') + str(m.get('id', ''))
            if any(k.lower() in nm.lower() for k in keywords):
                found_markets.append(m)

    # --- Sofascore search ---
    sf_match = None
    if isinstance(sf_today, list):
        for e in sf_today + sf_tomorrow:
            h = e.get('homeTeam', {}).get('name', '').lower()
            a = e.get('awayTeam', {}).get('name', '').lower()
            if any(k.lower() in h or k.lower() in a for k in keywords):
                sf_match = e
                break

    # --- Compile results ---
    results.update({
        'elapsed_s': round(time.time() - t0, 2),
        'team1': {'id': t1_id, 'name': t1_display, 'form': t1_form, 'home': t1_home, 'away': t1_away, 'gstats': t1_gstats, 'matches': t1_matches[:10]},
        'team2': {'id': t2_id, 'name': t2_display, 'form': t2_form, 'home': t2_home, 'away': t2_away, 'gstats': t2_gstats, 'matches': t2_matches[:10]},
        'h2h': h2h_matches,
        'true_odds': {
            'home': true_odds['odds_home'], 'draw': true_odds['odds_draw'], 'away': true_odds['odds_away'],
            'prob_home': true_odds['prob_home'], 'prob_draw': true_odds['prob_draw'], 'prob_away': true_odds['prob_away'],
            'over25_odds': true_odds['odds_over25'], 'over25_prob': true_odds['prob_over25'],
            'btts_odds': true_odds['odds_btts'], 'btts_prob': true_odds['prob_btts'],
            'exp_total': true_odds['exp_total'],
            'lam_home': true_odds['lam_home'], 'lam_away': true_odds['lam_away'],
        },
        'ba_found_markets': found_markets,
        'sf_match': sf_match,
    })

    # --- Save to cache ---
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    except: pass

    return results

def kelly_recommendations(analysis, bankroll=10000, est_odds=None):
    """Generate Kelly staking recommendations.
    est_odds: dict with keys home/draw/away/over25/btts (market odds)
    True odds are compared against market odds to find value.
    """
    to = analysis.get('true_odds', {})
    # est_odds: actual market BACK odds from Bet Angel (e.g. from ba_markets/prices)
    # If None, we skip Kelly and just output true odds for external value calculation.
    # NOTE: Do NOT use true_odds * 1.07 as market estimate — this makes edge always ~6.5%
    #       and makes the Kelly analysis meaningless (bug fixed 2026-04-27).
    if est_odds is None:
        # No market odds provided — output only true odds, caller computes value externally
        to2 = analysis.get('true_odds', {})
        est_odds = {
            'home': to2.get('home', 0),
            'draw': to2.get('draw', 0),
            'away': to2.get('away', 0),
            'over25': to2.get('over25_odds', 0),
            'btts': to2.get('btts_odds', 0),
        }
    recs = []

    def kelly_value(market_odds, true_prob, kelly_mult=0.5):
        """
        Standard Kelly criterion for BACK bets.
        Returns the half-Kelly stake fraction (0 = no value).
        
        CRITICAL (fixed 2026-04-27):
        - edge = true_prob - implied_prob  (positive = model beats market)
        - Value% = (true_prob - implied_prob) / implied_prob * 100
        - Do NOT compare against a hardcoded market estimate — use actual BA prices!
        """
        if market_odds <= 1 or true_prob <= 0: return 0
        implied_prob = 1.0 / market_odds
        edge = true_prob - implied_prob
        b = market_odds - 1
        # Standard Kelly: f* = (b*p - q) / b where q = 1-p
        f = (b * true_prob - (1 - true_prob)) / b
        return max(0, kelly_mult * f)

    bets = [
        {'key': 'home', 'market': f"{analysis['team1']['name']} Win",
         'prob': to.get('prob_home', 0)},
        {'key': 'draw', 'market': 'Draw',
         'prob': to.get('prob_draw', 0)},
        {'key': 'away', 'market': f"{analysis['team2']['name']} Win",
         'prob': to.get('prob_away', 0)},
        {'key': 'over25', 'market': 'Over 2.5 Goals',
         'prob': to.get('over25_prob', 0)},
        {'key': 'btts', 'market': 'Both Teams To Score Yes',
         'prob': to.get('btts_prob', 0)},
    ]

    for bet in bets:
        mkt_odds = est_odds.get(bet['key'], 2.0)
        true_prob = bet['prob']
        true_odds = round(0.97 / true_prob, 2) if true_prob > 0 else 10.0
        kf = kelly_value(mkt_odds, true_prob)

        if mkt_odds < true_odds:
            notes = 'STRONG' if kf > 0.08 else ('VALUE' if kf > 0.03 else 'LOW')
            action = 'BACK'
        elif abs(mkt_odds - true_odds) < 0.05:
            notes = 'PARITY'; action = 'SKIP'
        else:
            notes = 'OVERPRICED'; action = 'LAY' if kf > 0.03 else 'SKIP'
            kf = kelly_value(true_odds, true_prob) * 0.5  # LAY Kelly

        recs.append({
            'market': bet['market'],
            'true_odds': true_odds,
            'market_odds': mkt_odds,
            'prob': f"{true_prob*100:.0f}%",
            'kelly_pct': f"{kf*100:.1f}%",
            'stake': round(bankroll * kf, 0) if kf > 0.01 else 0,
            'action': action,
            'notes': notes,
        })

    return recs

def monitor_market(keywords, timeout_min=30, interval_sec=30):
    """Poll Bet Angel until market appears, then return with prices"""
    print(f"[MONITOR] Checking every {interval_sec}s for up to {timeout_min}min...")
    deadline = time.time() + timeout_min * 60
    while time.time() < deadline:
        r = requests.post(
            f"{BA_BASE}/markets/v1.0/getMarkets",
            json={"dataRequired": ["ID","NAME","MARKET_START_TIME"]},
            headers={"Content-Type":"application/json"},
            timeout=6
        )
        markets = r.json().get("result", {}).get("markets", [])
        found = [m for m in markets if any(k.lower() in (m.get('name','')+str(m.get('id',''))).lower() for k in keywords)]
        if found:
            print(f"[MONITOR] FOUND {len(found)} market(s)!")
            mkt_ids = [m['id'] for m in found]
            prices = worker_betangel_prices(mkt_ids)
            return found, prices
        elapsed = int(time.time() - (deadline - timeout_min*60))
        print(f"[MONITOR] {elapsed}s elapsed, no market yet... retrying in {interval_sec}s")
        time.sleep(interval_sec)
    print("[MONITOR] Timeout - market not found")
    return [], []

# =====================================================================
# CLI
# =====================================================================

if __name__ == '__main__':
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else 'analyze'
    t0 = time.time()

    if cmd == 'analyze':
        t1n = sys.argv[2] if len(sys.argv) > 2 else 'Petrzalka'
        t2n = sys.argv[3] if len(sys.argv) > 3 else 'Lehota'
        print(f"=== Full Analysis: {t1n} vs {t2n} ===")
        a = full_analysis(t1n, t2n)

        # Parse --market-odds flag: --market-odds home=2.5,draw=3.2,away=3.8
        market_odds = None
        for arg in sys.argv[4:]:
            if arg.startswith('--market-odds='):
                raw = arg.split('=', 1)[1]
                parts = raw.split(',')
                market_odds = {}
                for p in parts:
                    kv = p.split('=')
                    if len(kv) == 2:
                        key = kv[0].strip().lower()
                        try:
                            market_odds[key] = float(kv[1].strip())
                        except ValueError:
                            pass
                break

        if market_odds:
            print(f"\n=== KELLY ANALYSIS (market odds provided) ===")
            recs = kelly_recommendations(a, bankroll=10000, est_odds=market_odds)
            for r in recs:
                implied_prob = 1.0 / r['market_odds'] if r['market_odds'] > 1 else 0
                true_prob = a.get('true_odds', {}).get(f"prob_{r['market'].split()[0].lower()}", 0)
                value_pct = (true_prob - implied_prob) / implied_prob * 100 if implied_prob > 0 else 0
                flag = "KEEP" if value_pct >= 10 else ("MARGINAL" if value_pct >= 5 else "CANCEL")
                if r['stake'] > 0:
                    print(f"  [{flag}] {r['action']} {r['market']}")
                    print(f"    True={r['true_odds']} Market={r['market_odds']} Value={value_pct:+.1f}% | Kelly={r['kelly_pct']} | Stake={r['stake']} RON")
                else:
                    print(f"  [CANCEL] {r['market']} | True={r['true_odds']} Market={r['market_odds']} Value={value_pct:+.1f}% | NO EDGE")
        t1 = a['team1']; t2 = a['team2']
        print(f"\nElapsed: {a.get('elapsed_s','?')}s")
        print(f"Balance: {a.get('ba_balance','?')} RON")
        print(f"\nCGMBet26: {t1['name']} (id={t1['id']}) vs {t2['name']} (id={t2['id']})")
        print(f"\n{t1['name']} - Form: {t1['form']['form'][-10:]} | {t1['form']['w']}W {t1['form']['d']}D {t1['form']['l']}L")
        print(f"  Home: {t1['home']['w']}W {t1['home']['d']}D {t1['home']['l']}L | GF:{t1['home']['gf']} GA:{t1['home']['ga']}")
        print(f"  Stats: avg {t1['gstats'].get('avg_scored','?')} scored / {t1['gstats'].get('avg_conceded','?')} conceded")
        print(f"  Over2.5: {t1['gstats'].get('over25','?')} | BTTS: {t1['gstats'].get('btts_yes','?')}")
        print(f"\n{t2['name']} - Form: {t2['form']['form'][-10:]} | {t2['form']['w']}W {t2['form']['d']}D {t2['form']['l']}L")
        print(f"  Away: {t2['away']['w']}W {t2['away']['d']}D {t2['away']['l']}L | GF:{t2['away']['gf']} GA:{t2['away']['ga']}")
        print(f"  Stats: avg {t2['gstats'].get('avg_scored','?')} scored / {t2['gstats'].get('avg_conceded','?')} conceded")
        print(f"  Over2.5: {t2['gstats'].get('over25','?')} | BTTS: {t2['gstats'].get('btts_yes','?')}")
        print(f"\nH2H: {len(a.get('h2h',[]))} matches")
        for h in a.get('h2h',[]):
            hg = h.get('HomeGoals', '?')
            ag = h.get('AwayGoals', '?')
            print(f"  {h.get('Date')} | {h.get('HomeName')} {hg}-{ag} {h.get('AwayName')}")
        to = a.get('true_odds', {})
        print(f"\nTRUE ODDS (Poisson xG):")
        print(f"  {t1['name']} Win = {to.get('home','?')} | prob = {to.get('prob_home','?')*100:.0f}%")
        print(f"  Draw = {to.get('draw','?')} | prob = {to.get('prob_draw','?')*100:.0f}%")
        print(f"  {t2['name']} Win = {to.get('away','?')} | prob = {to.get('prob_away','?')*100:.0f}%")
        print(f"\n  xG Model: lambda_home={to.get('lam_home','?')} lambda_away={to.get('lam_away','?')}")
        print(f"  Expected Total Goals = {to.get('exp_total','?')}")
        print(f"\nOVER 2.5: true={to.get('over25_odds','?')} prob={to.get('over25_prob','?')*100:.0f}%")
        print(f"BTTS YES: true={to.get('btts_odds','?')} prob={to.get('btts_prob','?')*100:.0f}%")
        markets = a.get('ba_found_markets', [])
        print(f"\nBet Angel: {len(markets)} markets found")
        for m in markets[:5]:
            print(f"  id={m.get('id')} name={m.get('name')} inplay={m.get('inPlayStatus')}")
        sf = a.get('sf_match')
        print(f"\nSofascore: {'FOUND sf_id=' + str(sf.get('id')) if sf else 'NOT FOUND'}")
        if sf:
            print(f"  {sf.get('homeTeam',{}).get('name')} vs {sf.get('awayTeam',{}).get('name')}")
            print(f"  {sf.get('tournament',{}).get('name')} | {sf.get('status',{}).get('description')} {sf.get('time',{}).get('minute','')}'")
        print("\n=== CGMBET26 TRUE ODDS (Poisson xG) ===")
        print("NOTE: Kelly requires actual market odds — run with --market-odds or use value_scan_and_bet.py")
        # Show true odds clearly for external value calculation
        to = a.get('true_odds', {})
        prob_h = to.get('prob_home', 0)
        prob_d = to.get('prob_draw', 0)
        prob_a = to.get('prob_away', 0)
        print(f"  {t1['name']} Win = {to.get('home','?')} (prob={prob_h*100:.0f}%)")
        print(f"  Draw = {to.get('draw','?')} (prob={prob_d*100:.0f}%)")
        print(f"  {t2['name']} Win = {to.get('away','?')} (prob={prob_a*100:.0f}%)")
        print(f"  xG Model: lambda_home={to.get('lam_home','?')} lambda_away={to.get('lam_away','?')}")
        print(f"  Expected Total Goals = {to.get('exp_total','?')}")
        print(f"  Over 2.5: true={to.get('over25_odds','?')} prob={to.get('over25_prob','?')*100:.0f}%")
        print(f"  BTTS YES: true={to.get('btts_odds','?')} prob={to.get('btts_prob','?')*100:.0f}%")
        print(f"\n  Value Formula (use with actual BA market prices):")
        print(f"    Value% = (1/true_odds - 1/market_back) / (1/market_back) * 100")
        print(f"    e.g. True=2.00, Market=2.50 -> Value=(0.50-0.40)/0.40*100 = +25%")
        print(f"    e.g. True=2.00, Market=1.85 -> Value=(0.50-0.54)/0.54*100 = -7%")
        print(f"\nTotal time: {time.time()-t0:.1f}s")

    elif cmd == 'monitor':
        kw = sys.argv[2:] if len(sys.argv) > 2 else ['Petrzalka', 'Lehota']
        markets, prices = monitor_market(kw)
        if markets:
            print(json.dumps({"markets": markets, "prices": prices}, indent=2, default=str))

    elif cmd == 'prices':
        mids = sys.argv[2].split(',') if len(sys.argv) > 2 else []
        prices = worker_betangel_prices(mids)
        print(json.dumps(prices, indent=2, default=str))

    elif cmd == 'quick':
        # Just output current Bet Angel markets + balance - FAST
        r = requests.post(
            f"{BA_BASE}/markets/v1.0/getMarkets",
            json={"dataRequired": ["ID","NAME","MARKET_INPLAY_STATUS"]},
            headers={"Content-Type":"application/json"},
            timeout=5
        )
        mkt = r.json().get("result", {}).get("markets", [])
        bal = worker_betangel_balance()
        print(f"Balance: {bal} RON | Markets: {len(mkt)}")
        for m in mkt[:10]:
            print(f"  {m.get('id')} | {m.get('name')} | inplay={m.get('inPlayStatus')}")
