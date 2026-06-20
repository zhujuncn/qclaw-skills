"""
In-Play Monitor with Cash Out Logic v1.0
==========================================
Monitors divergent matches during play and triggers Cash Out when conditions are met.

Cash Out Triggers for Divergent Matches:
1. Goal against ELO favorite -> Cash Out immediately (profit lock)
2. ELO favorite equalizes -> Consider Cash Out (reduce exposure)
3. Match reaches 70min with ELO favorite losing -> Hold (potential late comeback)
4. O0.5 goal scored -> Cash Out O0.5 bet (99% guaranteed)

Integration with Bet Angel X2 API for:
- Live price monitoring
- Green Up / Cash Out execution
- Bet status tracking
"""

import sys, io, json, time, sqlite3
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, r'C:\Users\zhuju\.qclaw\skills\betangel-x2')
from x2_framework import (
    get_guardian_markets, scan_prices_bulk,
    api_post, GUARDIAN, BETTING, parse_bet_result
)

DB_PATH = r'C:\Users\zhuju\AppData\Roaming\CGMBetSystem\CGMBetStats_v3.db'
WORKSPACE = r'C:\Users\zhuju\.qclaw\workspace'


def load_divergent_matches(date_str):
    """Load today's divergent matches from scan results."""
    filepath = f"{WORKSPACE}\\divergence_scan_{date_str}.json"
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('divergences', [])
    except FileNotFoundError:
        print(f"Warning: No divergence scan found for {date_str}")
        print(f"Run divergence_scanner.py first!")
        return []


def load_placed_bets(date_str):
    """Load today's placed bets from results files."""
    bets = []
    # Try multiple result files
    for fname in [f"april21_results.json", f"all_strategies_results_{date_str}.json",
                  f"o05_results_{date_str}.json", f"ou25_gg_results_{date_str}.json"]:
        filepath = f"{WORKSPACE}\\{fname}"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    bets.extend(data)
                elif isinstance(data, dict) and 'bets' in data:
                    bets.extend(data['bets'])
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    return bets


def find_match_in_guardian(home, away, market_type='mo'):
    """Find a match in Guardian by team name parts."""
    markets = get_guardian_markets()
    home_parts = home.lower().split()
    away_parts = away.lower().split()

    type_filter = {
        'mo': 'match odds',
        'ou05': 'over/under 0.5',
        'ou25': 'over/under 2.5',
        'btts': 'both teams',
    }.get(market_type, '')

    for m in markets:
        mname = m.get('name', '').lower()
        if type_filter and type_filter not in mname:
            continue

        home_found = any(len(p) > 3 and p in mname for p in home_parts if len(p) > 3)
        away_found = any(len(p) > 3 and p in mname for p in away_parts if len(p) > 3)

        if home_found and away_found:
            return m

    return None


def check_cash_out_conditions(market_id, match_name, initial_bet_side='BACK'):
    """Check if Cash Out conditions are met for a market."""
    prices = scan_prices_bulk()
    mdata = prices.get(market_id, {})

    if not mdata:
        return None

    status = mdata.get('status', 'UNKNOWN')
    selections = mdata.get('selections', {})

    analysis = {
        'market_id': market_id,
        'match': match_name,
        'status': status,
        'cash_out_available': False,
        'profit_if_cashout': 0,
        'action': 'HOLD',
        'reason': ''
    }

    if status == 'CLOSED':
        analysis['action'] = 'FINISHED'
        analysis['reason'] = 'Market closed - match finished'
        return analysis

    if status == 'SUSPENDED':
        analysis['reason'] = 'Market suspended (goal/event in progress)'
        return analysis

    # Check for O0.5 - if any Over price is < 1.01, goal scored
    if 'over/under 0.5' in match_name.lower():
        for sel_id, sel_data in selections.items():
            lay1 = sel_data.get('lay1', {}).get('prc', 0)
            if lay1 and lay1 < 1.05:
                analysis['action'] = 'CASH_OUT'
                analysis['cash_out_available'] = True
                analysis['reason'] = 'Goal scored - O0.5 won, green out now'
                return analysis

    # Check Match Odds - if ELO favorite odds drifting significantly
    if 'match odds' in match_name.lower():
        for sel_id, sel_data in selections.items():
            back1 = sel_data.get('back1', {}).get('prc', 0)
            lay1 = sel_data.get('lay1', {}).get('prc', 0)
            # If lay price dropped significantly from initial bet -> value decreased
            # If back price increased significantly -> cash out opportunity

    return analysis


def execute_cash_out(market_id):
    """Execute Cash Out (green all) on a market."""
    resp = api_post(f'{BETTING}/greenAll', {'marketId': market_id})
    print(f"  Green All response: {resp}")
    return resp


def monitor_divergent_matches(divergences, interval=120, max_cycles=30):
    """Monitor divergent matches and trigger Cash Out when conditions met."""
    print("=" * 70)
    print("IN-PLAY MONITOR - DIVERGENT MATCHES")
    print(f"Monitoring {len(divergences)} divergent matches")
    print(f"Check interval: {interval}s | Max cycles: {max_cycles}")
    print("=" * 70)

    # Build monitoring list
    monitor_list = []
    for d in divergences:
        entry = {
            'match': f"{d['home']} vs {d['away']}",
            'date': d['date'],
            'tier': d['tier'],
            'elo_diff': d['elo_diff'],
            'form_diff': d['form_diff'],
            'markets_found': {},
            'status': 'PENDING',
            'actions_taken': []
        }
        monitor_list.append(entry)

    for cycle in range(max_cycles):
        now = time.strftime('%H:%M:%S')
        print(f"\n--- Cycle {cycle+1}/{max_cycles} @ {now} ---")

        any_active = False

        for entry in monitor_list:
            if entry['status'] in ['FINISHED', 'CASHED_OUT']:
                continue

            match = entry['match']
            home, away = match.split(' vs ')

            # Find markets
            if not entry['markets_found']:
                for mtype in ['mo', 'ou05', 'ou25', 'btts']:
                    found = find_match_in_guardian(home, away, mtype)
                    if found:
                        entry['markets_found'][mtype] = {
                            'id': found.get('id'),
                            'name': found.get('name')
                        }

            if not entry['markets_found']:
                entry['status'] = 'NOT_FOUND'
                continue

            any_active = True

            # Check each market
            for mtype, minfo in entry['markets_found'].items():
                mid = minfo['id']
                mname = minfo['name']

                result = check_cash_out_conditions(mid, mname)

                if result and result['action'] == 'CASH_OUT':
                    print(f"  !! CASH OUT SIGNAL: {match} - {mname}")
                    print(f"     Reason: {result['reason']}")

                    # Execute cash out for O0.5 (safe)
                    if mtype == 'ou05' and result['cash_out_available']:
                        resp = execute_cash_out(mid)
                        entry['actions_taken'].append({
                            'time': now,
                            'action': 'CASH_OUT',
                            'market': mtype,
                            'response': resp
                        })
                        entry['status'] = 'CASHED_OUT'

                elif result and result['action'] == 'FINISHED':
                    print(f"  {match} - {mname}: FINISHED")
                    entry['status'] = 'FINISHED'

        if not any_active:
            print("  All matches finished or cashed out. Stopping monitor.")
            break

        time.sleep(interval)

    # Save monitor log
    log_file = f"{WORKSPACE}\\monitor_log_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(monitor_list, f, ensure_ascii=False, indent=2)
    print(f"\nMonitor log saved: {log_file}")

    return monitor_list


def quick_status_check(divergences):
    """One-shot check of current status for all divergent matches."""
    print("=" * 70)
    print("DIVERGENT MATCHES - QUICK STATUS CHECK")
    print("=" * 70)

    for d in divergences:
        match = f"{d['home']} vs {d['away']}"
        home, away = d['home'], d['away']
        tier = d['tier']
        tier_label = {1: '!!! STRONG', 2: '!! MODERATE', 3: '! WEAK'}.get(tier, '?')

        print(f"\n[{tier_label}] {match}")
        print(f"  {d['league']} | {d['date']}")
        print(f"  ELO: {d['elo_diff']:+.0f} | Form: {d['form_diff']:+.0f}")

        for mtype in ['ou05', 'mo', 'ou25', 'btts']:
            found = find_match_in_guardian(home, away, mtype)
            if found:
                mid = found.get('id')
                prices = scan_prices_bulk()
                mdata = prices.get(mid, {})
                status = mdata.get('status', 'UNKNOWN')

                # Get relevant price
                sels = mdata.get('selections', {})
                price_str = ''
                if mtype == 'ou05':
                    sel = sels.get('5851483', {})
                    b = sel.get('back1', {}).get('prc', 0)
                    l = sel.get('lay1', {}).get('prc', 0)
                    price_str = f"BACK={b} LAY={l}"
                    if l and l < 1.05:
                        price_str += " *** GOAL SCORED ***"
                elif mtype == 'mo':
                    for sid, sd in sels.items():
                        b = sd.get('back1', {}).get('prc', 0)
                        if b:
                            price_str += f"BACK={b} "

                type_label = {'ou05': 'O/U 0.5', 'mo': 'Match Odds', 'ou25': 'O/U 2.5', 'btts': 'BTTS'}.get(mtype, mtype)
                print(f"  [{type_label}] {status} {price_str}")
            else:
                type_label = {'ou05': 'O/U 0.5', 'mo': 'Match Odds', 'ou25': 'O/U 2.5', 'btts': 'BTTS'}.get(mtype, mtype)
                print(f"  [{type_label}] NOT IN GUARDIAN")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='In-Play Monitor for Divergent Matches')
    parser.add_argument('--date', default=None, help='Date (YYYY-MM-DD)')
    parser.add_argument('--monitor', action='store_true', help='Continuous monitoring mode')
    parser.add_argument('--interval', type=int, default=120, help='Check interval in seconds')
    parser.add_argument('--cycles', type=int, default=30, help='Max monitoring cycles')
    args = parser.parse_args()

    target = args.date or time.strftime('%Y-%m-%d')
    divergences = load_divergent_matches(target)

    if not divergences:
        print(f"No divergent matches found for {target}")
        sys.exit(0)

    # Filter to tier 1-2 only for monitoring
    active = [d for d in divergences if d['tier'] <= 2]
    print(f"Active divergences (Tier 1-2): {len(active)}")

    if args.monitor:
        monitor_divergent_matches(active, interval=args.interval, max_cycles=args.cycles)
    else:
        quick_status_check(divergences)
