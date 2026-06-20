"""
Football Council - Main Runner
Complete workflow to run the football council discussion.

Usage:
    python run_council.py [market_id]

If no market_id provided, reads from latest live_markets.json
"""
import sys
import os
import json
from datetime import datetime

# Add paths
sys.path.insert(0, r'C:\Users\zhuju\.qclaw\workspace\betangel')
sys.path.insert(0, r'C:\Users\zhuju\.qclaw\skills\football-council\scripts')

import x2_framework as xf
from vote_aggregator import VoteAggregator
from record_decision import DecisionRecorder

def run_council(market_id=None, match_name=None):
    """Run the complete Football Council workflow."""
    
    print("=" * 70)
    print("🏛️  FOOTBALL COUNCIL - Multi-Agent Discussion System")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    
    # Step 1: Get market info
    print("\n[Step 1] Loading BetAngel Guardian...")
    xf.apply_coupon('FT')
    markets = xf.get_guardian_markets()
    
    if market_id:
        # Find specific market
        target = next((m for m in markets if m['id'] == market_id), None)
        if not target:
            print(f"[ERROR] Market {market_id} not found")
            return None
    else:
        # Get first live market
        live = [m for m in markets if m.get('status') != 'PREMATCH']
        if not live:
            print("[ERROR] No live markets found")
            return None
        target = live[0]
        market_id = target['id']
    
    match_name = match_name or target.get('name', 'Unknown Match')
    print(f"    Match: {match_name}")
    print(f"    Market ID: {market_id}")
    print(f"    Status: {target.get('status', '?')}")
    
    # Step 2: Get prices
    print("\n[Step 2] Fetching market prices...")
    prices = xf.scan_prices_bulk()
    mprices = prices.get(market_id, {}).get('selections', {})
    
    # Map selection names
    selections = target.get('selections', [])
    sel_map = {s['id']: s['name'] for s in selections}
    
    print("    Selections:")
    for sel_id, sel_data in mprices.items():
        name = sel_map.get(sel_id, f"Sel_{sel_id}")
        b = sel_data.get('back1', {}).get('prc', 0)
        l = sel_data.get('lay1', {}).get('prc', 0)
        if b > 0 or l > 0:
            print(f"      - {name}: BACK {b} | LAY {l}")
    
    # Step 3: Now spawn sub-agents (called by main agent)
    print("\n[Step 3] Council Discussion")
    print("-" * 70)
    print("NOTE: To actually spawn sub-agents, use the sessions_spawn tool")
    print("This script shows the workflow structure.\n")
    
    # For demo, we'll show what each agent would do
    agents = {
        'sofascore': {
            'role': 'Data Analyst',
            'task': 'Fetch live match data from Sofascore API',
            'focus': 'xG, shots, momentum, events'
        },
        'cgmbet': {
            'role': 'Statistical Strategist',
            'task': 'Query CGMBet26 database for patterns',
            'focus': 'Value%, Tier rating, Kelly stake'
        },
        'analyzer': {
            'role': 'Comprehensive Judge',
            'task': 'Synthesize all data and provide recommendation',
            'focus': 'Confidence, risk, final recommendation'
        }
    }
    
    for agent_id, info in agents.items():
        print(f"\n🤖 Agent: {agent_id.upper()}")
        print(f"   Role: {info['role']}")
        print(f"   Task: {info['task']}")
        print(f"   Focus: {info['focus']}")
        print("   Status: [Would spawn via sessions_spawn in actual execution]")
    
    # Step 4: Vote aggregation (would collect results from agents)
    print("\n" + "-" * 70)
    print("[Step 4] Vote Aggregation")
    print("-" * 70)
    print("\nWaiting for agent responses...")
    print("In actual execution, results would be collected here.")
    
    # Demo: Create sample voting
    aggregator = VoteAggregator()
    
    print("\n[STEP 5] Would spawn sub-agents via sessions_spawn tool...")
    print("\nTo run the actual multi-agent discussion:")
    print("1. Tell me '启动足球委员会分析' or 'run football council'")
    print("2. I will spawn 3 sub-agents using sessions_spawn")
    print("3. Each agent will analyze the match from their perspective")
    print("4. I will aggregate votes and make final ruling")
    print("5. If BET decision, execute via BetAngel API")
    
    print("\n" + "=" * 70)
    print("Council Session Complete")
    print("=" * 70)
    
    return {
        'market_id': market_id,
        'match_name': match_name,
        'status': 'ready_for_discussion'
    }


if __name__ == "__main__":
    market_id = sys.argv[1] if len(sys.argv) > 1 else None
    result = run_council(market_id)
    
    if result:
        print("\nResult:")
        print(json.dumps(result, indent=2))
