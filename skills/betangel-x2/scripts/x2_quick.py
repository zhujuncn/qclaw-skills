#!/usr/bin/env python3
"""
Bet Angel X2 Quick Start
========================
一键执行 X2 策略：扫描 → 显示 → 下单

Usage:
  python x2_quick.py --scan              # 只扫描，不下单
  python x2_quick.py --bet "Falkirk"     # 对指定比赛下注
  python x2_quick.py --bet-all           # 对所有合格比赛下注（默认 stake=5）
  python x2_quick.py --stake 10 --bet-all  # 自定义金额
"""

import sys
import argparse
sys.path.insert(0, r'C:\Users\zhuju\.qclaw\skills\betangel-x2\scripts')
import x2_framework as xf

def scan_matches():
    """Scan and display all qualifying X2 matches."""
    print("=" * 60)
    print("  BET ANGEL X2 策略扫描")
    print("=" * 60)
    
    balance = xf.api_get_balance()
    print(f"\nBalance: GBP {balance:.2f}")
    
    # Load all markets
    all_markets_resp = xf.api_post(xf.MARKETS + '/getMarkets', payload={
        'dataRequired': ['ID', 'NAME', 'SELECTION_IDS', 'SELECTION_NAMES']
    })
    all_markets = all_markets_resp.get('result', {}).get('markets', [])
    
    print(f"Markets loaded: {len(all_markets)}")
    
    # Find Match Odds with Under 5.5
    results = []
    for m in all_markets:
        name = m.get('name', '')
        if 'match odds' not in name.lower():
            continue
        
        home, away = xf.extract_teams(name)
        if not home or not away:
            continue
        
        # Check for Under 5.5
        if not xf.has_under_market(all_markets, home, away):
            continue
        
        # Get selections
        selections = m.get('selections', [])
        if not selections:
            continue
        
        # Find home team selection
        home_sel = None
        for s in selections:
            if home.lower() in s.get('name', '').lower():
                home_sel = s
                break
        
        if not home_sel:
            continue
        
        # Get LAY price (need to fetch from prices)
        mid = m.get('id')
        # For display, just show market info
        results.append({
            'market_id': mid,
            'home': home,
            'away': away,
            'home_sel_id': home_sel['id'],
            'home_sel_name': home_sel['name']
        })
    
    print(f"\nFound {len(results)} qualifying matches:")
    print(f"{'#':<3} {'Match':<35} {'Home Selection ID':<15}")
    print("-" * 60)
    for i, r in enumerate(results, 1):
        print(f"{i:<3} {r['home']} vs {r['away']:<20} {r['home_sel_id']:<15}")
    
    return results

def place_bet_on_match(market_id: str, selection_id: str, home_name: str, stake: float = 5.0):
    """Place LAY bet on a single match."""
    print(f"\n--- Placing bet on {home_name} ---")
    
    # 1. Display market (REQUIRED!)
    print("Step 1: Displaying market...")
    xf.display_market(market_id)
    
    # 2. Get current prices
    print("Step 2: Getting current LAY price...")
    prices = xf.get_market_prices(market_id)
    
    # Find LAY price for selection
    lay_price = None
    for sel in prices.get('result', {}).get('runnerLines', []):
        if str(sel.get('selectionId')) == str(selection_id):
            lay_prices = sel.get('layPrices', [])
            if lay_prices:
                lay_price = lay_prices[0].get('price')
            break
    
    if not lay_price:
        print(f"ERROR: No LAY price available for {home_name}")
        return False
    
    print(f"Current LAY price: {lay_price}")
    
    # 3. Place bet
    print(f"Step 3: Placing LAY bet @ {lay_price} with stake {stake}...")
    resp = xf.place_lay_bet(market_id, selection_id, lay_price, stake)
    
    if 'betRef' in str(resp):
        print(f"✓ SUCCESS! BetRef: {resp.get('betRef', 'N/A')}")
        return True
    else:
        print(f"✗ FAILED: {resp}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Bet Angel X2 Quick Start')
    parser.add_argument('--scan', action='store_true', help='Scan only, no bets')
    parser.add_argument('--bet-all', action='store_true', help='Bet on all qualifying matches')
    parser.add_argument('--bet', type=str, help='Bet on specific team (home team name)')
    parser.add_argument('--stake', type=float, default=5.0, help='Stake amount (default: 5.0)')
    
    args = parser.parse_args()
    
    # Always scan first
    matches = scan_matches()
    
    if args.scan:
        print("\n[Scan complete - no bets placed]")
        return
    
    if args.bet:
        # Find matching match
        for m in matches:
            if args.bet.lower() in m['home'].lower():
                place_bet_on_match(m['market_id'], m['home_sel_id'], m['home'], args.stake)
                return
        print(f"Match not found: {args.bet}")
        return
    
    if args.bet_all:
        print(f"\nPlacing bets on {len(matches)} matches with stake {args.stake}...")
        success_count = 0
        for m in matches:
            if place_bet_on_match(m['market_id'], m['home_sel_id'], m['home'], args.stake):
                success_count += 1
        
        print(f"\n{'='*60}")
        print(f"SUMMARY: {success_count}/{len(matches)} bets placed successfully")
        print(f"{'='*60}")
        return
    
    # Default: just show help
    print("\n" + "="*60)
    print("Use --scan to see qualifying matches")
    print("Use --bet-all to bet on all qualifying matches")
    print("Use --bet 'TeamName' to bet on a specific match")
    print("="*60)

if __name__ == '__main__':
    main()
