"""
Football Council - Spawn Council Script
Convenience script to spawn multiple agents for a specific match.
Usage: python spawn_council.py [market_id] [match_name]
"""
import sys
import json
import os

def spawn_council(match_name, market_id, agent_ids=None):
    """
    Spawn the Football Council agents for a match.
    Returns the spawned agent session keys for monitoring.
    """
    # Default agents if not specified
    if agent_ids is None:
        agent_ids = ['sofascore', 'cgmbet', 'analyzer']
    
    # Agent tasks
    tasks = {
        'sofascore': f"""You are Sofascore football data analyst.
Read C:\\Users\\zhuju\\.qclaw\\skills\\sofascore\\SKILL.md for API details.

Target match: {match_name}
Market ID: {market_id}

Fetch real-time data for this match:
1. GET https://api.sofascore.com/api/v1/event/{{event_id}}/ (basic info)
2. GET https://api.sofascore.com/api/v1/event/{{event_id}}/statistics (stats)
3. GET https://api.sofascore.com/api/v1/event/{{event_id}}/incidents (events)

Output JSON:
{{"signal": "BET" or "NO_BET", "confidence": 1-5, "data": {{...}}, "reason": "..."}}

Key metrics to extract: score, xG, shots, possession, key events (goals, cards).
Focus on momentum and recent form.
""",
        'cgmbet': f"""You are CGMBet26 statistical strategist.
Read C:\\Users\\zhuju\\.qclaw\\skills\\cgmbet26-strategies\\SKILL.md for strategy details.

Target match: {match_name}
Market ID: {market_id}

Analyze using CGMBet26 SQLite DB:
Path: C:\\Users\\zhuju\\AppData\\Roaming\\CGMBetSystem\\CGMBetStats_v3.db

Query for:
1. Historical H2H record
2. Home team home performance
3. Away team away performance  
4. Current season stats
5. Tier rating and Value%

Output JSON:
{{"signal": "BET" or "NO_BET", "tier": 1-3, "value_pct": float, "kelly": float, "confidence": 1-5, "reason": "..."}}

Use Kelly Criterion (Half Kelly = 0.5). Recommend stake = bankroll * kelly * 0.5.
""",
        'analyzer': f"""You are Match Analyzer comprehensive judge.
Read C:\\Users\\zhuju\\.qclaw\\skills\\match-analyzer\\SKILL.md for framework.

Target match: {match_name}
Market ID: {market_id}

Synthesize data from Sofascore and CGMBet agents.
The other agents will provide their analysis separately.

Output JSON:
{{"signal": "BET" or "NO_BET", "confidence": 1-5, "recommendation": {{"market": "...", "direction": "BACK/LAY", "odds": float, "stake": float}}, "risk_level": "Low/Medium/High", "reason": "..."}}

Consider: Are signals consistent across sources? Is Value positive?
Apply risk management: max 50 RON per match.
"""
    }
    
    # Note: Actual spawning done by main agent via sessions_spawn tool
    print("=" * 60)
    print("Football Council - Agent Spawn Config")
    print("=" * 60)
    print(f"\nMatch: {match_name}")
    print(f"Market ID: {market_id}")
    print(f"\nAgents to spawn:")
    for agent_id in agent_ids:
        print(f"  - {agent_id.upper()}: {tasks[agent_id][:100]}...")
    
    print("\n" + "=" * 60)
    print("To spawn agents, the main agent will call sessions_spawn")
    print("with mode='run' and runtime='subagent' for each.")
    print("=" * 60)
    
    return tasks

if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 2:
        market_id = sys.argv[1]
        match_name = sys.argv[2]
    else:
        # Load from latest live markets file
        live_file = r'C:\Users\zhuju\.qclaw\skills\football-council\data\live_markets.json'
        if os.path.exists(live_file):
            with open(live_file, 'r') as f:
                markets = json.load(f)
            if markets:
                m = markets[0]
                market_id = m['market_id']
                match_name = m['name']
            else:
                print("No live markets found.")
                sys.exit(1)
        else:
            print("Usage: python spawn_council.py [market_id] [match_name]")
            sys.exit(1)
    
    tasks = spawn_council(match_name, market_id)
