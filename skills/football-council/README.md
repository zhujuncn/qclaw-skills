# Football Council Skill

Multi-agent roundtable discussion system for football betting decisions.

## Quick Start

```
"启动足球委员会" / "run football council"
```

## Structure

```
football-council/
├── SKILL.md                    # Main skill file
├── scripts/
│   ├── run_council.py          # Main runner
│   ├── read_betangel_live.py   # Read live markets
│   ├── spawn_council.py        # Spawn config
│   ├── vote_aggregator.py      # Vote tallying
│   └── record_decision.py      # Decision logging
└── references/
    ├── agent_prompts.md        # Agent prompts
    └── decision_rules.md       # Voting rules
```

## Agents

1. **Sofascore** - Real-time data analyst (25%)
2. **CGMBet26** - Statistical modeler (30%)
3. **Match Analyzer** - Comprehensive judge (25%)
4. **Evolver** - Self-optimization (20%)

## Voting

| Votes | Decision | Action |
|-------|----------|--------|
| 3-4/4 | STRONG | Bet immediately (Half Kelly) |
| 2/4 | VALUE | Standard position (Quarter Kelly) |
| 1/4 | CAUTION | Small test |
| 0/4 | NO BET | Skip |

## Usage

```python
# Run the council
import sys
sys.path.insert(0, r'C:\Users\zhuju\.qclaw\skills\football-council\scripts')
from run_council import run_council

# Analyze specific market
result = run_council(market_id="1.234567")
```
