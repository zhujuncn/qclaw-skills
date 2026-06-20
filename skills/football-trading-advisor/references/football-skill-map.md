# Football Skill Map

Use this reference when the user asks which football skills are available, asks to route a football trading task, or asks to update/reuse prior football workflow decisions.

## Primary Entry Points

- `football-trading-advisor`: default entrypoint for daily/ad hoc football betting advice, Bet Angel market matching, value/Kelly gates, dynamic bankroll, probe handling, and consolidated reports.
- `betangel-live-order-engine`: default entrypoint for live Bet Angel order and position management, heartbeat monitoring, exposure detection, reduce/close/cash-out/green-up decisions, and `AI开` / `AI关` live execution control.
- `betangel-api`: low-level Bet Angel API request construction, debugging, market/balance/order reads, and GUI/API mismatch diagnosis.

## Research And Strategy

- `cgmbet26`: CGMBet26 historical database, ratings, Poisson/ELO/Form analysis, value detection, P-value context, and statistical review.
- `cgmbet26-strategies`: executable strategy thresholds, Kelly sizing, confidence tiers, entry conditions, and stake management.
- `football-council`: multi-agent arbitration, NameResolver-style team matching, multi-source debate, and batch analysis when a single model is insufficient.
- `form-elo-divergence`: guardrail for favorite/underdog conflicts when form and ELO disagree.
- `match-analyzer`: single-match live or pre-match analysis combining live data and CGMBet26-style statistics.

## Live Data And Scores

- `match-fetch`: general fixture/result lookup by team or league.
- `sofascore`: Sofascore event, live score, statistics, timeline, and schedule access. In this environment, direct Sofascore may be blocked by challenge; verify before relying on it unattended.
- `flashscore` / `flashscore-skill`: FlashScore browser-based live score and schedule extraction.
- `openligadb`: OpenLigaDB German and supported league data.
- `football-match-monitor`: live football monitoring and match-state tracking when present.

## Bet Angel Execution And Automation

- `betangel-live-order-engine`: use for existing positions, in-play heartbeat, stop-loss/profit-lock, partial reduce, auto supplement, cash out, and green-up.
- `cash-out-guard`: use for conservative close/green-up reasoning, Betfair hedging math, and feedback-driven cash-out rule evolution.
- `guardian-automation`: Guardian `.baf` rule generation/parsing and Guardian/API automation guidance.
- `betangel-apply-rules`: attach existing Bet Angel `.baf` automation rules to markets.
- `betangel-x2`: legacy/alternate Bet Angel X2 API patterns when a workflow specifically references it.

## External Pipelines And Sources

- `betfair-pipeline`: DJYY ExchangeBets daily pipeline: DJYY picks -> CGMBet26 validation -> Bet Angel Guardian scan -> odds filter -> LAY execution -> goal/cash-out monitoring.
- `djyy-extract`: extract DJYY strategy picks from djyydata.com.
- `superbet`: Superbet.ro browsing, odds, and account checks.

## Review And Evolution

- `evolver`: post-trade learning, parameter improvement, and review notes. Do not use it as a direct betting executor.

## Routing Rules

- For normal "下单建议" or daily scans, start with `football-trading-advisor`.
- For "AI开", "AI关", "监控", "止盈", "止损", "cash out", "green up", or already-open Bet Angel positions, start with `betangel-live-order-engine`.
- For raw Bet Angel API payloads, endpoint debugging, or GUI/API mismatch, start with `betangel-api`.
- For score/live-stat requests, start with `match-fetch`, then use `sofascore`, `flashscore`, or API-Football helpers depending on availability.
- For CGMBet26 model questions, start with `cgmbet26`; for executable thresholds and staking, add `cgmbet26-strategies`.
- For uncertain team names or multiple conflicting signals, add `football-council` for arbitration.

## Safety Defaults

- Ad hoc betting is advice-only unless the user explicitly asks for real execution.
- The recurring Daily Football Trading Advisor automation may auto-execute only inside its official gates and bankroll caps.
- Live Bet Angel automation uses `.\ba.ps1 AI开` and `.\ba.ps1 AI关` as the global switch.
- GUI-visible but API-absent markets are `API_NOT_VISIBLE`; do not auto bet, close, reduce, or green until API market ID, selection ID, status, and prices are explicit.
- Existing exposure should still appear in heartbeat as `exposure_detected_without_plan` even without a plan; monitor-only until a safe plan exists.
