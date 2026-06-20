"""
Football Council - Read BetAngel Live Markets
Reads all currently live/in-play markets from BetAngel Guardian.
"""
import sys
sys.path.insert(0, r'C:\Users\zhuju\.qclaw\workspace\betangel')
import x2_framework as xf
import json
from datetime import datetime

def get_live_markets():
    """Get all live (in-play) markets from BetAngel Guardian."""
    print("=" * 60)
    print("Football Council - Reading BetAngel Live Markets")
    print("=" * 60)
    
    # Step 1: Load FT Coupon
    print("\n[1/3] Loading FT Coupon...")
    result = xf.apply_coupon('FT')
    print(f"     FT Coupon loaded: {result.get('couponLoaded', 0)} markets")
    
    # Step 2: Get all markets
    print("\n[2/3] Fetching all markets...")
    markets = xf.get_guardian_markets()
    print(f"     Total markets: {len(markets)}")
    
    # Step 3: Filter live markets
    live_markets = []
    prematch_markets = []
    
    for m in markets:
        status = m.get('status', 'UNKNOWN')
        if status != 'PREMATCH':
            live_markets.append(m)
        else:
            prematch_markets.append(m)
    
    print(f"     Live/In-Play: {len(live_markets)}")
    print(f"     Pre-match: {len(prematch_markets)}")
    
    # Step 4: Get prices for live markets
    print("\n[3/3] Fetching live prices...")
    prices = xf.scan_prices_bulk()
    
    # Step 5: Format output
    print("\n" + "=" * 60)
    print("LIVE MARKETS FOR COUNCIL DISCUSSION")
    print("=" * 60)
    
    live_data = []
    
    for m in live_markets:
        mid = m['id']
        mdata = prices.get(mid, {})
        
        # Get selection names
        selections = m.get('selections', [])
        sel_names = {s['id']: s['name'] for s in selections}
        
        # Get prices
        market_prices = {}
        for sel_id, sel_data in mdata.get('selections', {}).items():
            name = sel_names.get(sel_id, f"Sel_{sel_id}")
            back1 = sel_data.get('back1', {})
            lay1 = sel_data.get('lay1', {})
            market_prices[sel_id] = {
                'name': name,
                'back1': back1.get('prc', 0),
                'lay1': lay1.get('prc', 0)
            }
        
        # Build display
        display = {
            'market_id': mid,
            'name': m.get('name', 'Unknown'),
            'status': m.get('status', 'UNKNOWN'),
            'selections': market_prices,
            'timestamp': datetime.now().isoformat()
        }
        live_data.append(display)
        
        # Print to console
        market_name = m.get('name', 'Unknown')[:50]
        status = m.get('status', '?')
        print(f"\n[{status}] {market_name}")
        print(f"  ID: {mid}")
        
        for sel_id, price_info in market_prices.items():
            b = price_info['back1']
            l = price_info['lay1']
            if b > 0 or l > 0:
                print(f"  - {price_info['name']}: BACK {b} | LAY {l}")
    
    # Save to file for council agents
    output_file = r'C:\Users\zhuju\.qclaw\skills\football-council\data\live_markets.json'
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(live_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Saved {len(live_data)} live markets to:")
    print(f"     {output_file}")
    print("=" * 60)
    
    return live_data

if __name__ == "__main__":
    try:
        live = get_live_markets()
        print(f"\nTotal live markets: {len(live)}")
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
