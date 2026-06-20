# Form-ELO Divergence Detection Skill v1.0

## Overview

A complete betting analysis system that detects when ELO ratings contradict recent Form ratings in football matches, creating value opportunities and risk warnings.

## What It Does

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  CGMBet26 DB    │────▶│  Divergence     │────▶│  Betting        │
│  (310K matches) │     │  Scanner        │     │  Recommendations│
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Tier 1/2/3     │
                        │  Classification │
                        └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Live Monitor   │
                        │  + Cash Out     │
                        └─────────────────┘
```

## Quick Start

```bash
# 1. Daily scan
python divergence_scanner.py --date 2026-04-21 --days 1

# 2. Full pipeline
python pipeline_divergence.py --date 2026-04-21 --stake 2

# 3. Live monitoring
python inplay_monitor.py --date 2026-04-21 --monitor
```

## Core Concept: Form-ELO Divergence

| Metric | Meaning | Example |
|--------|---------|---------|
| **ELO** | Long-term strength | "曼城是强队" (ELO +500) |
| **Form** | Recent performance | "但曼城最近5场输了3场" (Form -8) |

**Divergence** = ELO says win, but Form says lose

### Real Example from Today

```
La Coruna vs Mirandes
├── ELO: La Coruna +154 (长期实力强)
├── Form: Mirandes +11 (近期状态更好)
├── Odds: La Coruna 1.54 (热门)
└── Result: 0-1 HT (Mirandes 领先!)

→ ELO 高估了 La Coruna，Form 更准确
```

## Tier System

| Tier | Criteria | Action |
|------|----------|--------|
| **TIER 1** | \|ELO\|>100, \|Form\|>10 | Skip LAY热门, 反向下注, 全监控 |
| **TIER 2** | \|ELO\|>50, \|Form\|>5 | 半仓, 轻监控 |
| **TIER 3** | \|ELO\|>50, \|Form\|>3 | 仅记录 |

## Files

| File | Purpose | Lines |
|------|---------|-------|
| `divergence_scanner.py` | Core detection engine | ~300 |
| `inplay_monitor.py` | Live monitoring + Cash Out | ~320 |
| `pipeline_divergence.py` | Integrated execution | ~220 |
| `example_standalone.py` | Simple standalone demo | ~150 |

## Installation

```bash
# Copy to workspace
copy form-elo-divergence.skill %USERPROFILE%\.qclaw\workspace\
Expand-Archive form-elo-divergence.skill

# Requires CGMBet26 at:
# %APPDATA%\CGMBetSystem\CGMBetStats_v3.db
```

## Output Example

```
!!! [TIER 1 - STRONG]
  2026-04-20 1930 | La Coruna vs Mirandes
  ELO: 1572 vs 1418 (diff +154)
  Form: +0 vs +11 (diff -11)
  >> LAY La Coruna @ 1.55
     Home overvalued by ELO, Form contradicts
  >> BACK Over 1.5 @ 1.24
     Divergent matches tend to have open games
  [MONITORING: Cash Out enabled]
```

## Integration

- Auto-loads existing bets from JSON files
- Checks for divergence conflicts
- Suggests Cash Out when triggered
- Works with Bet Angel X2 Framework

## Performance

- Scan 100 matches: ~2 seconds
- Monitor cycle: ~3 seconds per 10 matches
- Database: 310K matches, 31% Form coverage

## Version

v1.0 — April 2026

## License

MIT — Use for betting analysis at your own risk.
