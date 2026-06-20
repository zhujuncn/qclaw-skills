"""
Football Council - Vote Aggregator
Aggregates votes from all council agents and produces final ruling.
"""
import json
from datetime import datetime
from typing import List, Dict, Any

class VoteAggregator:
    """Aggregates agent votes and produces final decision."""
    
    # Decision thresholds
    THRESHOLDS = {
        4: ("UNANIMOUS", "Bet immediately", 0.5),
        3: ("STRONG", "Bet immediately", 0.5),
        2: ("VALUE", "Standard position", 0.25),
        1: ("CAUTION", "Small test", 0.25),
        0: ("NO_BET", "Skip", 0)
    }
    
    # Confidence weights
    WEIGHTS = {
        'sofascore': 0.25,
        'cgmbet': 0.30,
        'analyzer': 0.25
    }
    
    def __init__(self):
        self.votes = []
        self.results = {}
    
    def add_vote(self, agent_id: str, signal: str, confidence: int, 
                 reason: str, extra_data: Dict = None):
        """Add a vote from an agent."""
        self.votes.append({
            'agent': agent_id,
            'signal': signal,
            'confidence': confidence,
            'reason': reason,
            'extra': extra_data or {},
            'timestamp': datetime.now().isoformat()
        })
        
        self.results[agent_id] = {
            'signal': signal,
            'confidence': confidence
        }
    
    def tally_votes(self) -> Dict[str, Any]:
        """Tally votes and produce ruling."""
        # Count BET votes
        bet_count = sum(1 for v in self.votes if v['signal'] == 'BET')
        
        # Get weighted confidence
        total_weight = 0
        weighted_conf = 0
        
        for v in self.votes:
            if v['signal'] == 'BET':
                weight = self.WEIGHTS.get(v['agent'], 0.25)
                total_weight += weight
                weighted_conf += v['confidence'] * weight
        
        avg_confidence = weighted_conf / total_weight if total_weight > 0 else 0
        
        # Determine decision
        decision_key = min(bet_count, 4)
        decision_text, action, kelly = self.THRESHOLDS[decision_key]
        
        # Build voting table
        vote_table = []
        for v in self.votes:
            vote_table.append({
                'agent': v['agent'].upper(),
                'signal': v['signal'],
                'confidence': v['confidence'],
                'reason': v['reason']
            })
        
        # Final ruling
        ruling = {
            'timestamp': datetime.now().isoformat(),
            'votes': vote_table,
            'bet_count': bet_count,
            'total_agents': len(self.votes),
            'decision': decision_text,
            'action': action,
            'kelly_fraction': kelly,
            'weighted_confidence': round(avg_confidence, 2),
            'signals': {
                v['agent']: v['signal'] for v in self.votes
            }
        }
        
        return ruling
    
    def format_report(self, ruling: Dict, match_name: str, 
                      market_id: str, kelly_frac: float = 0) -> str:
        """Format the decision report as markdown."""
        
        # Voting table
        vote_lines = []
        for v in ruling['votes']:
            emoji = "[YES]" if v['signal'] == 'BET' else "[NO]"
            stars = "⭐" * v['confidence']
            vote_lines.append(
                f"| {v['agent']} | {emoji} {v['signal']} | {stars} | "
                f"{v['reason'][:50]}... |"
            )
        
        # Decision
        decision_emoji = {
            'UNANIMOUS': '[****]',
            'STRONG': '[***]',
            'VALUE': '[**]',
            'CAUTION': '[*]',
            'NO_BET': '[NO]'
        }.get(ruling['decision'], '[?]')
        
        report = f"""# Football Council Decision Report

## Match: {match_name}
## Market ID: {market_id}
## Time: {ruling['timestamp']}

---

### Agent Voting

| Agent | Signal | Confidence | Reason |
|-------|--------|------------|--------|
{chr(10).join(vote_lines)}

**Vote Result**: {ruling['bet_count']}/{ruling['total_agents']} Agents Approved

---

### Main Agent Ruling

**Decision: {ruling['decision']}** {decision_emoji}

| Metric | Value |
|--------|-------|
| Action | {ruling['action']} |
| Kelly Fraction | {ruling['kelly_fraction']} |
| Weighted Confidence | {ruling['weighted_confidence']}/5 |

"""
        
        if ruling['decision'] != 'NO_BET':
            report += f"""---

### Recommended Action

| Field | Value |
|-------|-------|
| Direction | BACK / LAY |
| Odds | [Current market odds] |
| Stake | {kelly_frac:.0%} of bankroll |

"""
        
        report += f"""---

## Risk Warnings

- This decision is based on multi-agent consensus, not financial advice
- Adjust position size according to personal risk tolerance
- Maximum recommended per-match stake: 50 RON
- Review after 3 consecutive losses

"""
        
        return report
    
    def save_decision(self, ruling: Dict, match_name: str, market_id: str):
        """Save decision to file for Evolver analysis."""
        output_dir = r'C:\Users\zhuju\.qclaw\skills\football-council\data\decisions'
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(output_dir, filename)
        
        decision_data = {
            **ruling,
            'match_name': match_name,
            'market_id': market_id
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(decision_data, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Decision saved: {filepath}")
        return filepath


def demo_aggregation():
    """Demo: Show how aggregation works."""
    print("=" * 60)
    print("Football Council - Vote Aggregator Demo")
    print("=" * 60)
    
    agg = VoteAggregator()
    
    # Add demo votes
    agg.add_vote(
        'sofascore',
        'BET',
        4,
        'Strong xG advantage for home team, recent form W-W-W',
        {'xg_diff': 0.8, 'momentum': 'positive'}
    )
    
    agg.add_vote(
        'cgmbet',
        'BET',
        5,
        'Tier 1 signal, Value% = 18%, P-value < 5%',
        {'tier': 1, 'value_pct': 18.5, 'p_value': 0.03}
    )
    
    agg.add_vote(
        'analyzer',
        'BET',
        4,
        'All signals align, high confidence',
        {'risk_level': 'Medium'}
    )
    
    # Tally and report
    ruling = agg.tally_votes()
    report = agg.format_report(ruling, "Team A vs Team B", "1.234567", ruling.get('kelly_fraction', 0))
    
    # Skip print(report) to avoid encoding issues
    print("\n[Report generated - see JSON output below]")
    print(f"\nDecision: {ruling['decision']}")
    print(f"Vote: {ruling['bet_count']}/{ruling['total_agents']}")
    print(f"Kelly: {ruling['kelly_fraction']}")
    print(f"Confidence: {ruling['weighted_confidence']}/5")
    print("\nJSON Ruling:")
    print(json.dumps(ruling, indent=2))
    
    # Save
    agg.save_decision(ruling, "Team A vs Team B", "1.234567")


if __name__ == "__main__":
    demo_aggregation()
