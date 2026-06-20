# QClaw Skills Package

Local Codex skills for football research, Bet Angel execution, Betfair exchange workflows, travel helpers, and browser automation.

Updated 2026-06-20 from `C:\Users\zhuju\.codex\skills`.

## Total Entry Points

| Skill | Use |
| --- | --- |
| football-trading-advisor | Daily order advice, Bet Angel matching, CGMBet26 value scans, dynamic staking, probe rules, and combined reports. |
| betangel-live-order-engine | Live position monitoring, heartbeat, AI on/off, take-profit, stop-loss, reduction, cash out, and green up. |
| betangel-api | Bet Angel API debugging, balance/market/order reads, and GUI/API mismatch diagnosis. |

## Research And Strategy

| Skill | Use |
| --- | --- |
| cgmbet26 | CGMBet26 database, ELO/Form/Poisson, value detection, and historical statistics. |
| cgmbet26-strategies | Direct order strategies, Kelly sizing, confidence, and bankroll allocation. |
| football-council | Multi-model and multi-agent discussion, name matching, and signal arbitration. |
| match-analyzer | Single-match analysis combining live data and statistical models. |
| form-elo-divergence | Risk filtering when Form and ELO conflict. |

## Scores And Data Sources

| Skill | Use |
| --- | --- |
| match-fetch | Match lookup by team or league, schedules, and results. |
| sofascore | Sofascore live scores, statistics, and events; this machine may encounter challenges. |
| flashscore | FlashScore browser scraping. |
| flashscore-skill | FlashScore browser scraping variant; overlaps with `flashscore`. |
| openligadb | Germany and other supported league data. |
| football-match-monitor | Match state monitoring. |

## Bet Angel Execution And Automation

| Skill | Use |
| --- | --- |
| cash-out-guard | Conservative cash out / greening calculations and post-trade optimization. |
| guardian-automation | Generate and parse Guardian `.baf` rules. |
| betangel-apply-rules | Attach existing `.baf` rules to Bet Angel markets. |
| betangel-x2 | Old or fallback Bet Angel X2 API workflow. |

## External Sources And Pipelines

| Skill | Use |
| --- | --- |
| betfair-pipeline | DJYY to CGMBet26 to Bet Angel to LAY to goal-monitoring pipeline. |
| djyy-extract | Extract DJYY strategy picks. |
| superbet | Superbet.ro odds, balance, and browser automation. |

## Review And Evolution

| Skill | Use |
| --- | --- |
| evolver | Post-trade review, parameter optimization, and experience consolidation; does not place bets directly. |

## General Utilities

| Skill | Use |
| --- | --- |
| maps-travel-list | Google Maps travel-place list creation workflow. |
| playwright | Browser automation helper for real browser testing and scraping. |
| wizz-air-query | Wizz Air route and destination query workflow. |

## Simple Routing

| Request | Use |
| --- | --- |
| Order advice / today's scan / daily football | `football-trading-advisor` |
| AI on / AI off / monitoring / take-profit / stop-loss / cash out | `betangel-live-order-engine` |
| Bet Angel API error / market not visible / GUI and API mismatch | `betangel-api` |
| Scores / live data | Start with `match-fetch`, then use `sofascore` or `flashscore`. |
| CGMBet26 model / strategy | `cgmbet26` plus `cgmbet26-strategies` |

## Notes

- The repository mirrors reusable local skill code and documentation.
- Generated Python cache files, logs, env files, and OS metadata files are excluded.
- Money-moving workflows still require explicit user authorization at runtime.
