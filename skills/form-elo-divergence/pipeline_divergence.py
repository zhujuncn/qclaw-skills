"""
Pipeline Integration: Divergence-Aware Execution v1.0
======================================================
Wraps the standard execution pipeline with Form-ELO divergence awareness.

Flow:
1. Run divergence_scanner.py -> get flagged matches
2. For each match in execution plan:
   a. Check if match is flagged as divergent
   b. If YES: adjust strategy (skip risky bets, add hedging, flag for monitoring)
   c. If NO: execute normally
3. After execution: start inplay_monitor.py for divergent matches
"""

import sys, io, json, os, time
if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, r'C:\Users\zhuju\.qclaw\skills\betangel-x2')
sys.path.insert(0, r'C:\Users\zhuju\.qclaw\workspace\betangel')

from divergence_scanner import scan_divergence, save_results, print_results
from inplay_monitor import quick_status_check, monitor_divergent_matches

WORKSPACE = r'C:\Users\zhuju\.qclaw\workspace'


def load_divergence_map(date_str):
    """Load divergence scan and build a quick lookup map."""
    filepath = f"{WORKSPACE}\\divergence_scan_{date_str}.json"
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        div_map = {}
        for d in data.get('divergences', []):
            key = f"{d['home'].lower()}|{d['away'].lower()}"
            div_map[key] = d
        return div_map
    except FileNotFoundError:
        return {}


def check_divergence(home, away, div_map):
    """Check if a match is in the divergence map."""
    key = f"{home.lower()}|{away.lower()}"
    # Also try with partial matching (different name sources)
    for k, v in div_map.items():
        h, a = k.split('|')
        home_ok = any(len(p) > 4 and p in home.lower() for p in h.split() if len(p) > 4)
        away_ok = any(len(p) > 4 and p in away.lower() for p in a.split() if len(p) > 4)
        if home_ok and away_ok:
            return v
    return None


def adjust_strategy_for_divergence(bet_plan, divergence):
    """Adjust bet strategy based on divergence info."""
    tier = divergence.get('tier', 0)
    rec = divergence.get('recommendation', {})
    elo_diff = divergence.get('elo_diff', 0)
    form_diff = divergence.get('form_diff', 0)

    adjustments = []

    if tier == 1:
        # STRONG divergence - high caution
        adjustments.append({
            'level': 'WARNING',
            'message': f'STRONG ELO-Form divergence detected! ELO={elo_diff:+.0f} Form={form_diff:+.0f}',
        })
        # Skip LAY on ELO favorite (risky)
        if elo_diff > 0:
            adjustments.append({
                'action': 'SKIP_LAY_HOME',
                'reason': 'ELO favorite but Form contradicts - LAY is risky'
            })
        # Add Draw or Away backing
        for bet in rec.get('bets', []):
            if bet.get('selection') in ['Draw', divergence['away']]:
                adjustments.append({
                    'action': 'ADD_BET',
                    'bet': bet,
                    'reason': 'Divergence-based value bet'
                })

    elif tier == 2:
        # MODERATE divergence
        adjustments.append({
            'level': 'CAUTION',
            'message': f'Moderate ELO-Form divergence. ELO={elo_diff:+.0f} Form={form_diff:+.0f}',
        })
        # Reduce stake on ELO favorite bets
        adjustments.append({
            'action': 'REDUCE_STAKE',
            'factor': 0.5,
            'reason': 'Moderate divergence - half stake for safety'
        })

    elif tier == 3:
        # WEAK divergence - just flag
        adjustments.append({
            'level': 'INFO',
            'message': f'Weak ELO-Form divergence. ELO={elo_diff:+.0f} Form={form_diff:+.0f}',
        })

    # Always enable monitoring for divergent matches
    adjustments.append({
        'action': 'ENABLE_MONITORING',
        'cash_out': True,
        'reason': 'Divergent match - higher variance expected'
    })

    return adjustments


def run_pipeline_with_divergence(target_date, stake=2.0):
    """Run the full pipeline with divergence awareness."""

    print("=" * 70)
    print("DIVERGENCE-AWARE BETTING PIPELINE")
    print(f"Date: {target_date} | Stake: {stake} RON")
    print("=" * 70)

    # Step 1: Scan for divergences
    print("\n[STEP 1] Scanning for Form-ELO divergences...")
    results = scan_divergence(target_date=target_date, days_ahead=1)
    print_results(results)

    div_map = load_divergence_map(target_date)
    div_count = len(results['divergences'])

    if div_count > 0:
        print(f"\n>>> {div_count} divergent matches detected!")
        print(">>> Adjusting strategy accordingly...\n")

    # Step 2: Check existing bets against divergence map
    print("[STEP 2] Checking existing bets against divergence map...")

    bet_files = [f for f in os.listdir(WORKSPACE) if f.endswith('_results.json') or f.endswith('_bets.json')]

    affected_bets = 0
    for bf in bet_files:
        try:
            with open(os.path.join(WORKSPACE, bf), 'r', encoding='utf-8') as f:
                bets = json.load(f)
            if not isinstance(bets, list):
                continue
            for bet in bets:
                match = bet.get('match', '')
                if ' vs ' in match:
                    parts = match.split(' vs ')
                    if len(parts) == 2:
                        div = check_divergence(parts[0], parts[1], div_map)
                        if div:
                            affected_bets += 1
                            adj = adjust_strategy_for_divergence(bet, div)
                            for a in adj:
                                if a.get('level'):
                                    print(f"  [{a['level']}] {match}: {a['message']}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    if affected_bets == 0:
        print("  No existing bets affected by divergences.")
    else:
        print(f"\n  {affected_bets} bets potentially affected by divergences.")

    # Step 3: Summary and monitoring setup
    print(f"\n[STEP 3] Pipeline Summary")
    print(f"  Divergent matches: {div_count}")
    print(f"  Tier 1 (Strong): {sum(1 for d in results['divergences'] if d['tier'] == 1)}")
    print(f"  Tier 2 (Moderate): {sum(1 for d in results['divergences'] if d['tier'] == 2)}")
    print(f"  Tier 3 (Weak): {sum(1 for d in results['divergences'] if d['tier'] == 3)}")

    if div_count > 0:
        print(f"\n  Recommendations:")
        for d in results['divergences']:
            rec = d['recommendation']
            match = f"{d['home']} vs {d['away']}"
            for bet in rec.get('bets', []):
                print(f"    >> {bet['action']} {bet['selection']} @ {bet['price']}")
                print(f"       {bet['reason']}")

        # Run quick status check for currently live divergent matches
        print(f"\n[STEP 4] Checking live status of divergent matches...")
        active_divs = [d for d in results['divergences'] if d['tier'] <= 2]
        if active_divs:
            quick_status_check(active_divs)
        else:
            print("  No Tier 1-2 divergent matches to monitor right now.")

    return results


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Divergence-Aware Pipeline')
    parser.add_argument('--date', default=None, help='Target date (YYYY-MM-DD)')
    parser.add_argument('--stake', type=float, default=2.0, help='Stake per bet')
    args = parser.parse_args()

    target = args.date or time.strftime('%Y-%m-%d')
    run_pipeline_with_divergence(target, stake=args.stake)
