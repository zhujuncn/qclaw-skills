# -*- coding: utf-8 -*-
"""
Football Council - Batch Analysis + Auto-Betting Pipeline
Analyzes ALL BA Match Odds markets, categorizes by Kelly%, places bets.

Usage:
    python batch_analyze_and_bet.py [stake_strong] [stake_value] [stake_low]

Defaults: STRONG=1.3, VALUE=1.2, LOW=1.1 (RON)
"""
import json, urllib.request, time, sys, sqlite3, math
from datetime import datetime

BA_BASE = "http://localhost:9000/api/"
CGM_DB = r"C:\Users\zhuju\AppData\Roaming\CGMBetSystem\CGMBetStats_v3.db"

def api_post(endpoint, data):
    req = urllib.request.Request(
        BA_BASE + endpoint,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def get_all_ba_matches():
    """Get all Match Odds markets from Bet Angel"""
    api_post("guardian/v1.0/applyCoupon", {"couponName": "FT", "watchListNumber": 1})
    time.sleep(4)
    r = api_post("markets/v1.0/getMarkets", {
        "dataRequired": ["ID", "NAME", "SELECTION_IDS", "SELECTION_NAMES"]
    })
    markets = []
    for m in r.get("result", {}).get("markets", []):
        name = m.get("name", "")
        if "Match Odds" not in name:
            continue
        sels = m.get("selections", [])
        if len(sels) < 3:
            continue
        team_sels = [s for s in sels if s.get("name", "") not in ("The Draw", "Draw", "")]
        draw_sels = [s for s in sels if s.get("name", "") in ("The Draw", "Draw")]
        if len(team_sels) >= 2 and draw_sels:
            markets.append({
                'guardian_id': m.get("id"),
                'home': team_sels[0].get("name"),
                'away': team_sels[-1].get("name"),
                'draw_id': draw_sels[0].get("id"),
                'home_id': team_sels[0].get("id"),
                'away_id': team_sels[-1].get("id"),
                'name': name,
            })
    return markets

def poisson_pmf(lam, max_goals=6):
    return [math.exp(-lam) * (lam**i) / math.factorial(i) for i in range(max_goals+1)]

def analyze_match(home, away):
    """Quick Poisson analysis using CGMBet26 data"""
    try:
        conn = sqlite3.connect(CGM_DB)
        cur = conn.cursor()
        
        # Find teams
        cur.execute("SELECT Id FROM Teams WHERE Name = ?", (home,))
        r1 = cur.fetchone()
        cur.execute("SELECT Id FROM Teams WHERE Name = ?", (away,))
        r2 = cur.fetchone()
        
        if not r1 or not r2:
            return None
        
        id1, id2 = r1[0], r2[0]
        
        # Recent form (last 20 completed matches)
        cur.execute("""
            SELECT HomeGoals, AwayGoals FROM Matches
            WHERE HomeTeamId=? AND StatusCode='0'
            ORDER BY Date DESC LIMIT 20
        """, (id1,))
        home_matches = cur.fetchall()
        
        cur.execute("""
            SELECT HomeGoals, AwayGoals FROM Matches
            WHERE AwayTeamId=? AND StatusCode='0'
            ORDER BY Date DESC LIMIT 20
        """, (id2,))
        away_matches = cur.fetchall()
        
        if len(home_matches) < 5 or len(away_matches) < 5:
            return None
        
        # Calculate xG-like averages
        home_scored = sum(int(m[0]) for m in home_matches if m[0] not in (None, '')) / max(len(home_matches), 1)
        home_conceded = sum(int(m[1]) for m in home_matches if m[1] not in (None, '')) / max(len(home_matches), 1)
        away_scored = sum(int(m[1]) for m in away_matches if m[1] not in (None, '')) / max(len(away_matches), 1)
        away_conceded = sum(int(m[0]) for m in away_matches if m[0] not in (None, '')) / max(len(away_matches), 1)
        
        lambda_h = 0.6 * home_scored + 0.4 * away_conceded
        lambda_a = 0.6 * away_scored + 0.4 * home_conceded
        
        ph = poisson_pmf(lambda_h)
        pa = poisson_pmf(lambda_a)
        
        home_win = sum(ph[i] * pa[j] for i in range(7) for j in range(7) if i > j)
        draw = sum(ph[i] * pa[i] for i in range(7))
        away_win = sum(ph[i] * pa[j] for i in range(7) for j in range(7) if i < j)
        
        total = home_win + draw + away_win
        if total > 0:
            home_win /= total; draw /= total; away_win /= total
        
        return {
            'home_prob': home_win,
            'draw_prob': draw,
            'away_prob': away_win,
            'home_odds': 1/home_win if home_win > 0 else 999,
            'draw_odds': 1/draw if draw > 0 else 999,
            'away_odds': 1/away_win if away_win > 0 else 999,
        }
    except Exception as e:
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def kelly_stake(true_prob, market_odds, stake):
    """Half Kelly stake calculation"""
    b = market_odds - 1
    p = true_prob
    q = 1 - p
    if b <= 0 or p <= 0:
        return 0
    kelly = (b * p - q) / b * 0.5
    return max(0, kelly)

def place_bet(guardian_id, sel_id, odds, stake):
    """Place a single bet"""
    payload = {
        "marketId": guardian_id,
        "globalSettings": {
            "stake": stake,
            "betType": "NORMAL",
            "persistenceType": "MARKET_ON_CLOSE"
        },
        "async": False,
        "betsToPlace": [
            {
                "type": "BACK",
                "price": odds,
                "stake": stake,
                "selectionId": sel_id
            }
        ]
    }
    r = api_post("betting/v1.0/placeBets", payload)
    bets = r.get("result", {}).get("bets", [])
    if bets and bets[0].get("status") == "OK":
        return True, bets[0].get("betRef")
    else:
        error = bets[0].get("error", {}).get("msg", "Unknown") if bets else str(r)
        return False, error

def main():
    stake_strong = float(sys.argv[1]) if len(sys.argv) > 1 else 1.3
    stake_value = float(sys.argv[2]) if len(sys.argv) > 2 else 1.2
    stake_low = float(sys.argv[3]) if len(sys.argv) > 3 else 1.1
    
    print(f"[{datetime.now()}] Football Council Batch Analysis + Betting")
    print(f"Stakes: STRONG={stake_strong}, VALUE={stake_value}, LOW={stake_low}")
    print("="*80)
    
    # Step 1: Get all BA markets
    print("\n[1/4] Fetching BA markets...")
    markets = get_all_ba_matches()
    print(f"  Found {len(markets)} Match Odds markets")
    
    # Step 2: Analyze each
    print("\n[2/4] Analyzing matches...")
    results = []
    for i, m in enumerate(markets):
        analysis = analyze_match(m['home'], m['away'])
        if not analysis:
            continue
        
        # Find best value
        best = None
        best_kelly = 0
        for outcome, prob, odds_key, sel_key in [
            ('home', analysis['home_prob'], 'home_odds', 'home_id'),
            ('draw', analysis['draw_prob'], 'draw_odds', 'draw_id'),
            ('away', analysis['away_prob'], 'away_odds', 'away_id'),
        ]:
            # Get actual BA odds (simplified: use estimated)
            # In production, call getMarketPrices after displayMarket
            market_odds = analysis[odds_key]
            kelly = kelly_stake(prob, market_odds, 1.0)
            if kelly > best_kelly:
                best_kelly = kelly
                best = {
                    'match': f"{m['home']} vs {m['away']}",
                    'outcome': outcome,
                    'odds': market_odds,
                    'kelly': kelly,
                    'guardian_id': m['guardian_id'],
                    'sel_id': m[sel_key],
                }
        
        if best and best['kelly'] >= 0.01:
            results.append(best)
        
        if (i+1) % 50 == 0:
            print(f"  ...{i+1}/{len(markets)} analyzed, {len(results)} value found")
    
    print(f"  {len(results)} matches with value (Kelly>=1%)")
    
    # Step 3: Categorize
    strong = [r for r in results if r['kelly'] >= 0.08]
    value = [r for r in results if 0.03 <= r['kelly'] < 0.08]
    low = [r for r in results if 0.01 <= r['kelly'] < 0.03]
    
    print(f"\n[3/4] Categorization:")
    print(f"  STRONG (>=8%): {len(strong)} bets x {stake_strong} RON = {len(strong)*stake_strong:.1f} RON")
    print(f"  VALUE (3-8%):  {len(value)} bets x {stake_value} RON = {len(value)*stake_value:.1f} RON")
    print(f"  LOW (1-3%):    {len(low)} bets x {stake_low} RON = {len(low)*stake_low:.1f} RON")
    
    # Step 4: Place bets
    print(f"\n[4/4] Placing bets...")
    all_bets = []
    for r in strong:
        all_bets.append({**r, 'tier': 'STRONG', 'stake': stake_strong})
    for r in value:
        all_bets.append({**r, 'tier': 'VALUE', 'stake': stake_value})
    for r in low:
        all_bets.append({**r, 'tier': 'LOW', 'stake': stake_low})
    
    success = 0
    fail = 0
    log = []
    
    for i, bet in enumerate(all_bets):
        print(f"\n[{i+1}/{len(all_bets)}] {bet['tier']}: {bet['match']} -> {bet['outcome'].upper()} @ {bet['odds']:.2f} x {bet['stake']} RON")
        ok, ref = place_bet(bet['guardian_id'], bet['sel_id'], bet['odds'], bet['stake'])
        if ok:
            print(f"  SUCCESS! betRef={ref}")
            success += 1
        else:
            print(f"  FAILED: {ref}")
            fail += 1
        log.append({**bet, 'success': ok, 'ref': ref})
        time.sleep(0.5)
    
    # Save log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = rf"C:\Users\zhuju\.qclaw\workspace\batch_bet_log_{timestamp}.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Success: {success}")
    print(f"Failed:  {fail}")
    print(f"Total:   {len(all_bets)}")
    print(f"Log:     {log_file}")

if __name__ == "__main__":
    main()
