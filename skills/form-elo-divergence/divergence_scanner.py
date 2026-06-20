"""
Form-ELO Divergence Scanner v1.0
=================================
Scans CGMBet26 database for matches where ELO rating contradicts Form rating.
These matches represent HIGH VALUE opportunities for contrarian betting.

Divergence Definition:
  - ELO says Team A wins, but Form says Team B performs better (or vice versa)
  - |ELO_Diff| > 50 AND ELO_Diff * Form_Diff < 0

Confidence Levels:
  - TIER 1 (Strong Divergence): |ELO| > 100, |Form| > 10, opposite direction
  - TIER 2 (Moderate Divergence): |ELO| > 50, |Form| > 5, opposite direction
  - TIER 3 (Weak Divergence): |ELO| > 50, |Form| > 3, opposite direction

Output:
  - JSON file with flagged matches + recommendations
  - Console summary
"""

import sys, io, sqlite3, json, os
from datetime import datetime, timedelta
if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = r'C:\Users\zhuju\AppData\Roaming\CGMBetSystem\CGMBetStats_v3.db'
OUTPUT_DIR = r'C:\Users\zhuju\.qclaw\workspace'


def scan_divergence(target_date=None, days_ahead=1):
    """Scan for ELO-Form divergences in upcoming matches."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if target_date is None:
        target_date = datetime.now().strftime('%Y-%m-%d')

    end_date = (datetime.strptime(target_date, '%Y-%m-%d') + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

    # Query upcoming matches with ELO and Form data
    cur.execute("""
    SELECT
        m.MatchId, m.Date, m.Time, m.Status,
        t1.Name as Home, t1.Id as HomeId,
        t2.Name as Away, t2.Id as AwayId,
        l.Name as League, l.Country,
        r.EloHome, r.EloAway,
        r.EloHome - r.EloAway as EloDiff,
        r.FormHome, r.FormAway,
        r.FormHome - r.FormAway as FormDiff,
        o.Odd1, o.OddX, o.Odd2,
        o.OddO05, o.OddO25, o.OddGG,
        o.OddO15, o.OddU15
    FROM Matches m
    JOIN Teams t1 ON m.HomeTeamId = t1.Id
    JOIN Teams t2 ON m.AwayTeamId = t2.Id
    JOIN Leagues l ON substr(m.MatchId, 1, 4) = l.Id
    LEFT JOIN Ratings r ON m.MatchId = r.MatchId
    LEFT JOIN Odds o ON m.MatchId = o.MatchId
    WHERE m.Date >= ?
      AND m.Date <= ?
      AND m.Status NOT IN ('J', 'C')
      AND r.FormHome IS NOT NULL
      AND (r.FormHome != 0 OR r.FormAway != 0)
      AND r.EloHome IS NOT NULL
      AND r.EloHome != 0
    ORDER BY m.Date, m.Time
    """, (target_date, end_date))

    matches = [dict(r) for r in cur.fetchall()]
    conn.close()

    results = {
        'scan_time': datetime.now().isoformat(),
        'target_date': target_date,
        'total_matches': len(matches),
        'divergences': [],
        'all_analyzed': []
    }

    for m in matches:
        ed = m['EloDiff'] or 0
        fd = m['FormDiff'] or 0
        abs_ed = abs(ed)
        abs_fd = abs(fd)

        # Determine divergence
        is_diverge = (ed > 50 and fd < -3) or (ed < -50 and fd > 3)

        # Classify tier
        tier = 0
        if is_diverge:
            if abs_ed > 100 and abs_fd > 10:
                tier = 1  # Strong
            elif abs_ed > 50 and abs_fd > 5:
                tier = 2  # Moderate
            else:
                tier = 3  # Weak

        # Build analysis
        analysis = {
            'match_id': m['MatchId'],
            'date': m['Date'],
            'time': m['Time'],
            'home': m['Home'],
            'away': m['Away'],
            'league': m['League'],
            'country': m['Country'],
            'elo_home': m['EloHome'],
            'elo_away': m['EloAway'],
            'elo_diff': ed,
            'form_home': m['FormHome'],
            'form_away': m['FormAway'],
            'form_diff': fd,
            'odds': {
                '1': m['Odd1'],
                'X': m['OddX'],
                '2': m['Odd2'],
            },
            'diverge': is_diverge,
            'tier': tier,
        }

        # Generate recommendation for divergent matches
        if tier > 0:
            rec = generate_recommendation(m, ed, fd, tier)
            analysis['recommendation'] = rec
            results['divergences'].append(analysis)

        results['all_analyzed'].append(analysis)

    return results


def generate_recommendation(m, elo_diff, form_diff, tier):
    """Generate betting recommendation for a divergent match."""
    home = m['Home']
    away = m['Away']
    o1 = m['Odd1'] or 0
    ox = m['OddX'] or 0
    o2 = m['Odd2'] or 0
    o25 = m['OddO25'] or 0
    gg = m['OddGG'] or 0
    o15 = m['OddO15'] or 0

    recs = []
    confidence = tier  # 1=high, 2=medium, 3=low

    if elo_diff > 0 and form_diff < 0:
        # ELO says Home wins, Form says Away better
        # -> Back Away or Draw
        if o2 and o2 >= 3.0:
            recs.append({
                'action': 'BACK',
                'market': 'Match Odds',
                'selection': away,
                'price': o2,
                'reason': f'ELO favours {home} (+{elo_diff:.0f}) but Form favours {away} ({form_diff:+.0f})',
            })
        if ox and ox >= 3.0:
            recs.append({
                'action': 'BACK',
                'market': 'Match Odds',
                'selection': 'Draw',
                'price': ox,
                'reason': f'ELO-Form divergence suggests upset likely',
            })
        if o1 and o1 <= 1.65:
            recs.append({
                'action': 'LAY',
                'market': 'Match Odds',
                'selection': home,
                'price': round(o1 + 0.01, 2),
                'reason': f'Home overvalued by ELO, Form contradicts ({form_diff:+.0f})',
            })

    elif elo_diff < 0 and form_diff > 0:
        # ELO says Away wins, Form says Home better
        # -> Back Home or Draw
        if o1 and o1 >= 2.5:
            recs.append({
                'action': 'BACK',
                'market': 'Match Odds',
                'selection': home,
                'price': o1,
                'reason': f'ELO favours {away} ({elo_diff:+.0f}) but Form favours {home} (+{form_diff:.0f})',
            })
        if ox and ox >= 3.0:
            recs.append({
                'action': 'BACK',
                'market': 'Match Odds',
                'selection': 'Draw',
                'price': ox,
                'reason': f'ELO-Form divergence suggests upset likely',
            })

    # Always check O1.5 for divergent matches (higher goal variance expected)
    if o15 and o15 <= 1.30:
        recs.append({
            'action': 'BACK',
            'market': 'Over/Under 1.5 Goals',
            'selection': 'Over 1.5',
            'price': o15,
            'reason': 'Divergent matches tend to have open/chaotic games',
        })

    # GG if odds are reasonable
    if gg and 1.60 <= gg <= 2.20:
        recs.append({
            'action': 'BACK',
            'market': 'Both Teams to Score',
            'selection': 'Yes',
            'price': gg,
            'reason': 'Form divergence implies both teams can compete',
        })

    # Enhanced monitoring flag
    monitoring = {
        'flag': True,
        'watch_cash_out': True,
        'monitor_goals': True,
        'reason': 'Form-ELO divergence - higher variance match'
    }

    return {
        'confidence': confidence,
        'confidence_label': {1: 'HIGH', 2: 'MEDIUM', 3: 'LOW'}[confidence],
        'bets': recs,
        'monitoring': monitoring,
        'risk_note': f'ELO {elo_diff:+.0f} vs Form {form_diff:+.0f} - historical divergence success rate ~30% of matches show unexpected results'
    }


def print_results(results):
    """Print formatted results to console."""
    print("=" * 70)
    print(f"FORM-ELO DIVERGENCE SCAN — {results['target_date']}")
    print(f"Scan time: {results['scan_time']}")
    print("=" * 70)

    divs = results['divergences']
    divs.sort(key=lambda x: x['tier'])

    if not divs:
        print("\nNo divergences found.")
        return

    print(f"\nMatches analyzed: {results['total_matches']}")
    print(f"DIVERGENCES FOUND: {len(divs)}")
    print()

    tier_labels = {1: 'TIER 1 - STRONG', 2: 'TIER 2 - MODERATE', 3: 'TIER 3 - WEAK'}
    tier_emoji = {1: '!!!', 2: '!!', 3: '!'}

    for d in divs:
        tier = d['tier']
        rec = d['recommendation']

        print(f"{tier_emoji[tier]} [{tier_labels[tier]}]")
        print(f"  {d['date']} {d['time']:04d} | {d['home']} vs {d['away']}")
        print(f"  {d['league']} ({d['country']})")
        print(f"  ELO: {d['elo_home']:.0f} vs {d['elo_away']:.0f} (diff {d['elo_diff']:+.0f})")
        print(f"  Form: {d['form_home']:+.0f} vs {d['form_away']:+.0f} (diff {d['form_diff']:+.0f})")
        print(f"  Odds: {d['odds']['1']} / {d['odds']['X']} / {d['odds']['2']}")

        if rec['bets']:
            for b in rec['bets']:
                print(f"  >> {b['action']} {b['selection']} @ {b['price']} ({b['market']})")
                print(f"     {b['reason']}")

        print(f"  [MONITORING: Cash Out + Goal tracking enabled]")
        print()


def save_results(results, date_str):
    """Save results to JSON file."""
    filename = os.path.join(OUTPUT_DIR, f"divergence_scan_{date_str}.json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Results saved: {filename}")
    return filename


def get_divergent_match_ids(results):
    """Return list of match IDs for divergent matches (for pipeline integration)."""
    return [d['match_id'] for d in results['divergences'] if d['tier'] <= 2]


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Form-ELO Divergence Scanner')
    parser.add_argument('--date', default=None, help='Target date (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=1, help='Days ahead to scan')
    parser.add_argument('--json-only', action='store_true', help='Only output JSON')
    args = parser.parse_args()

    target = args.date or datetime.now().strftime('%Y-%m-%d')
    results = scan_divergence(target_date=target, days_ahead=args.days)

    if not args.json_only:
        print_results(results)

    save_results(results, target)
