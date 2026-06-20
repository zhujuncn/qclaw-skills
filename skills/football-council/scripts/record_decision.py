"""
Football Council - Record Decision (for Evolver)
Records decisions to memory for Evolver self-optimization.
"""
import json
import os
from datetime import datetime
from pathlib import Path

class DecisionRecorder:
    """Records betting decisions for Evolver analysis."""
    
    MEMORY_DIR = r'C:\Users\zhuju\.qclaw\workspace\memory'
    DECISION_FILE = r'C:\Users\zhuju\.qclaw\skills\football-council\data\council_history.json'
    
    def __init__(self):
        os.makedirs(os.path.dirname(self.DECISION_FILE), exist_ok=True)
        os.makedirs(self.MEMORY_DIR, exist_ok=True)
        
        # Load existing history
        if os.path.exists(self.DECISION_FILE):
            with open(self.DECISION_FILE, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = []
    
    def record(self, decision_data: dict):
        """Record a council decision."""
        
        record = {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'timestamp': datetime.now().isoformat(),
            'match': decision_data.get('match_name', 'Unknown'),
            'market_id': decision_data.get('market_id', ''),
            'decision': decision_data.get('decision', 'UNKNOWN'),
            'bet_count': decision_data.get('bet_count', 0),
            'total_agents': decision_data.get('total_agents', 0),
            'weighted_confidence': decision_data.get('weighted_confidence', 0),
            'kelly_fraction': decision_data.get('kelly_fraction', 0),
            'votes': decision_data.get('votes', []),
            'outcome': 'PENDING',  # PENDING / WIN / LOSS
            'notes': ''
        }
        
        self.history.append(record)
        self._save()
        
        return record
    
    def update_outcome(self, record_id: str, outcome: str, notes: str = ''):
        """Update the outcome of a recorded decision."""
        
        for record in self.history:
            if record['id'] == record_id:
                record['outcome'] = outcome.upper()
                record['notes'] = notes
                record['updated_at'] = datetime.now().isoformat()
                self._save()
                return True
        
        return False
    
    def get_statistics(self) -> dict:
        """Get statistics from council history."""
        
        total = len(self.history)
        if total == 0:
            return {'total': 0, 'pending': 0, 'win': 0, 'loss': 0, 'win_rate': 0}
        
        settled = [r for r in self.history if r['outcome'] != 'PENDING']
        wins = [r for r in settled if r['outcome'] == 'WIN']
        losses = [r for r in settled if r['outcome'] == 'LOSS']
        
        return {
            'total': total,
            'pending': total - len(settled),
            'win': len(wins),
            'loss': len(losses),
            'win_rate': round(len(wins) / len(settled) * 100, 1) if settled else 0,
            'settled': len(settled)
        }
    
    def get_recent(self, limit: int = 10) -> list:
        """Get recent decisions."""
        return self.history[-limit:]
    
    def _save(self):
        """Save history to file."""
        with open(self.DECISION_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
    
    def generate_evolvers_input(self) -> str:
        """Generate Evolver-formatted input for self-optimization."""
        
        stats = self.get_statistics()
        recent = self.get_recent(5)
        
        # Analyze patterns
        decisions = [r['decision'] for r in recent]
        outcomes = [r['outcome'] for r in recent if r['outcome'] != 'PENDING']
        
        # Pattern analysis
        patterns = {
            'strong_wins': sum(1 for r in recent if r['decision'] == 'STRONG' and r['outcome'] == 'WIN'),
            'strong_losses': sum(1 for r in recent if r['decision'] == 'STRONG' and r['outcome'] == 'LOSS'),
            'value_wins': sum(1 for r in recent if r['decision'] == 'VALUE' and r['outcome'] == 'WIN'),
            'value_losses': sum(1 for r in recent if r['decision'] == 'VALUE' and r['outcome'] == 'LOSS'),
        }
        
        evolver_input = f"""
## Football Council - Evolver Self-Optimization Report
Generated: {datetime.now().isoformat()}

### Overall Statistics
- Total Decisions: {stats['total']}
- Pending: {stats['pending']}
- Settled: {stats['settled']}
- Win Rate: {stats['win_rate']}%

### Recent Decisions
"""
        
        for r in reversed(recent):
            emoji = {'WIN': '✅', 'LOSS': '❌', 'PENDING': '⏳'}.get(r['outcome'], '?')
            evolver_input += f"- [{emoji}] {r['match']}: {r['decision']} ({r['outcome']})\n"
        
        evolver_input += f"""
### Pattern Analysis
- STRONG bets: {patterns['strong_wins']}W / {patterns['strong_losses']}L
- VALUE bets: {patterns['value_wins']}W / {patterns['value_losses']}L

### Recommendations
"""
        
        # Generate recommendations based on patterns
        if patterns['strong_losses'] > patterns['strong_wins']:
            evolver_input += "- ⚠️ STRONG decisions losing more than winning - review threshold\n"
        if stats['win_rate'] < 60:
            evolver_input += "- ⚠️ Win rate below 60% - consider tightening voting thresholds\n"
        if patterns['value_losses'] > patterns['value_wins']:
            evolver_input += "- ⚠️ VALUE decisions underperforming - increase minimum Value% threshold\n"
        
        if stats['win_rate'] >= 70:
            evolver_input += "- ✅ Win rate healthy - maintain current strategy\n"
        
        return evolver_input


def main():
    """CLI interface for decision recorder."""
    import sys
    
    recorder = DecisionRecorder()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python record_decision.py record <json_data>")
        print("  python record_decision.py stats")
        print("  python record_decision.py recent [limit]")
        print("  python record_decision.py update <id> WIN|LOSS [notes]")
        print("  python record_decision.py evolver")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'record':
        data = json.loads(sys.argv[2])
        record = recorder.record(data)
        print(f"Recorded: {record['id']}")
    
    elif cmd == 'stats':
        stats = recorder.get_statistics()
        print(json.dumps(stats, indent=2))
    
    elif cmd == 'recent':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        recent = recorder.get_recent(limit)
        print(json.dumps(recent, indent=2))
    
    elif cmd == 'update':
        record_id = sys.argv[2]
        outcome = sys.argv[3]
        notes = sys.argv[4] if len(sys.argv) > 4 else ''
        recorder.update_outcome(record_id, outcome, notes)
        print(f"Updated {record_id} -> {outcome}")
    
    elif cmd == 'evolver':
        report = recorder.generate_evolvers_input()
        print(report)
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
