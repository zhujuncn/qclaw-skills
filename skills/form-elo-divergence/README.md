# Form-ELO Divergence Detection System

A complete betting analysis system that detects when ELO ratings contradict recent Form ratings in football matches.

## System Components

```
form-elo-divergence/
├── SKILL.md                    # Skill documentation
├── README.md                   # This file
├── divergence_scanner.py       # Core detection engine
├── inplay_monitor.py          # Live match monitoring
├── pipeline_divergence.py     # Integrated execution pipeline
└── examples/                  # Usage examples
    ├── scan_example.json
    └── monitor_example.log
```

## What It Does

1. **Scans** CGMBet26 database for upcoming matches
2. **Compares** ELO rating vs Form rating for each team
3. **Detects** divergence (when they point in opposite directions)
4. **Classifies** by severity (Tier 1/2/3)
5. **Recommends** betting adjustments
6. **Monitors** in-play for Cash Out opportunities

## Quick Commands

```bash
# Daily scan
python divergence_scanner.py --date $(date +%Y-%m-%d) --days 1

# Full analysis
python pipeline_divergence.py --date 2026-04-21 --stake 2.0

# Live monitoring (2-min intervals)
python inplay_monitor.py --date 2026-04-21 --monitor --interval 120
```

## Example Output

```
!!! [TIER 1 - STRONG]
  2026-04-20 1930 | La Coruna vs Mirandes
  ELO: 1572 vs 1418 (diff +154)
  Form: +0 vs +11 (diff -11)
  >> LAY La Coruna @ 1.55
     Home overvalued by ELO, Form contradicts
  [MONITORING: Cash Out enabled]
```

## Database Schema Used

```sql
-- Matches table
MatchId, Date, Time, HomeTeamId, AwayTeamId, Status

-- Ratings table  
EloHome, EloAway, EloDiffHome, EloDiffAway, FormHome, FormAway

-- Odds table
Odd1, OddX, Odd2, OddO05, OddO25, OddGG, etc.
```

## Divergence Logic

```python
# Detection condition
is_diverge = (elo_diff > 50 and form_diff < -3) or (elo_diff < -50 and form_diff > 3)

# Tier classification
if abs(elo) > 100 and abs(form) > 10: tier = 1  # Strong
elif abs(elo) > 50 and abs(form) > 5: tier = 2   # Moderate  
else: tier = 3                                     # Weak
```

## Betting Adjustments

| Tier | ELO Favorite | Form Team | Stake | Monitoring |
|------|-------------|-----------|-------|------------|
| 1 | Skip LAY | Add BACK | 50% | Full |
| 2 | Reduce | Normal | 50% | Light |
| 3 | Normal | Normal | 100% | Log only |

## Cash Out Triggers

- **O0.5 goal scored** → Immediate Cash Out (99% certain)
- **Goal against ELO favorite** → Consider Cash Out
- **Match 70min+** → Evaluate position

## Integration

Works with Bet Angel X2 Framework:
- Loads placed bets from result JSON files
- Finds markets in Guardian by team name
- Executes Cash Out via API when triggered

## Performance

- Scan 100 matches: ~2 seconds
- Live monitoring cycle: ~3 seconds per 10 matches
- Database: 310K matches, ~31% Form coverage

## License

MIT — For educational and analysis purposes.
