"""
Quick scan: show all qualifying X2 matches without placing bets.
Run from the betangel-x2/scripts/ directory.

Usage:
  python run_scan.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import x2_framework as xf

def run_scan():
    print("=" * 65)
    print("X2 Strategy Scanner | " + xf.datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 65)

    bal = xf.api_get_balance()
    print(f"Balance: GBP{bal:.2f}  |  Odds range: {xf.CONFIG['min_lay_odds']}-{xf.CONFIG['max_lay_odds']}")
    print()

    markets    = xf.get_guardian_markets()
    match_odds = [m for m in markets if "match odds" in m.get("name", "").lower()]

    if not markets:
        print("No markets in Guardian. Load via apply_coupon().")
        return

    print(f"Scanning {len(markets)} markets ({len(match_odds)} Match Odds)...")
    print()

    results = []
    for m in match_odds:
        r = xf.evaluate_match(m, markets)
        if r:
            results.append(r)

    results.sort(key=lambda x: x["lay_price"])

    if not results:
        print("No qualifying matches found.")
        print()
        print("Markets with Match Odds but no Under 5.5:")
        for m in match_odds:
            name = m.get("name", "")
            h, a = xf.extract_teams(name)
            has_u5 = xf.has_under_market(markets, h, a)
            if not has_u5:
                print(f"  {h} vs {a} -- missing Under 5.5")
        return

    print(f"Qualifying matches ({len(results)}):")
    print()
    print(f"  {'HOME LAY':>10}  {'STAKE':>10}  {'MATCH'}")
    print(f"  {'-'*10}  {'-'*10}  {'-'*50}")
    for r in results:
        print(f"  {r['lay_price']:>10.2f}  GBP{xf.CONFIG['default_stake']:>10.1f}  {r['home']} vs {r['away']}")

    print()
    print(f"Best value: {results[0]['home']} vs {results[0]['away']} @ {results[0]['lay_price']}")

if __name__ == "__main__":
    run_scan()
