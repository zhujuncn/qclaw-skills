# Live Execution Runbook

Use this when the user asks to monitor `--status-line`, analyze a signal, and execute a real close/cash-out/green-up action.

## Status-Line Interpretation

Example:

```text
monitoring | 10:40:04 | mode=dry-run | balance=990.41 | markets=5 | inPlay=1 | actions=1 | suppressed=0 | executed=0
ACTION | Khovd Western v Khangarid | Khangarid | CLOSE | stake=10.0/15.0 | price=1.02 | p/l=0.69
WAIT | Cork City v Treaty United | The Draw | wait:in_play | stake=15.2/22.8 | price=7.8 | p/l=-5.37
```

Meanings:

- `ACTION`: the engine found an executable action under the current config.
- `WAIT`: no action should be taken yet.
- `wait:in_play`: market is not in-play, so live execution is blocked.
- `wait:price`: current executable price failed the plan's price gate.
- `exposure_detected_without_plan`: the API reports real matched/unmatched exposure, but there is no explicit plan for selection-level auto execution. Monitor only until a plan is added.
- `stake=current/target`: current matched stake versus target stake.
- `p/l`: current close/green preview used for threshold decisions.

## GUI Shows In-Play but Heartbeat Does Not

When the Bet Angel GUI shows live matches but heartbeat says `markets=0` or `inPlay=0`:

1. Inspect `_market_id_filter` in `work/football-trading-system/live_trade_manager.json`; stale IDs can hide planned markets.
2. Confirm `always_monitor_exposure=true`; real exposure should still appear even when `_market_id_filter` is present.
3. Refresh `getMarkets`, `getMarketPrices`, and `getMarketBets`. Compare the GUI match names with API market names and IDs.
4. Treat already-started football Match Odds markets with `OPEN` or `SUSPENDED` status as in-play-equivalent for monitoring. Execution remains blocked while `SUSPENDED`.
5. If a GUI market is absent from API `getMarkets`, do not auto execute. Record it as `API_NOT_VISIBLE` and use manual monitoring until Bet Angel API returns market ID, selection ID, status, and prices.

## Standard Real-Money Sequence

Daily global controls:

```powershell
.\ba.ps1 AI开
.\ba.ps1 AI关
```

Use `.\ba.ps1 AI开` to keep monitoring on and allow AI automatic live execution. Use `.\ba.ps1 AI关` to keep monitoring on but disable real automatic execution and return to dry-run monitoring. These are the preferred controls for all qclaw football skills.

Real execution requires all three gates:

- `live_trade_manager.json` has `"execute": true`
- `live_trade_manager.json` has `"ai_automation_enabled": true`
- command line includes `--execute`

Use low-level AI gate commands only when debugging the wrapper:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py ai-status
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py ai-on
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py ai-off
```

1. Refresh dry-run state:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_manager.py --cycles 1 --status-line
```

2. Execute only if the signal is still `ACTION` and the action is expected.

3. Temporarily set `work/football-trading-system/live_trade_manager.json`:

```json
"execute": true,
"ai_automation_enabled": true
```

4. Run one execution cycle:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_manager.py --execute --cycles 1 --status-line
```

5. Immediately restore:

```json
"ai_automation_enabled": false
```

6. Inspect the generated output JSON:

- `runs[0].actionLog[].action`
- `runs[0].actionLog[].result.payload`
- `runs[0].actionLog[].result.response.status`
- `runs[0].actionLog[].result.response.result.betPlaced.betRef`
- `priceMatched`
- `stakeMatched`

7. Run one post-execution dry-run:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_manager.py --cycles 1 --status-line
```

## Post-Execution Checks

For a successful `CLOSE_TRADE`, Bet Angel may show both the original BACK and the hedge LAY in matched bets. Treat that as expected.

The engine must not repeatedly close the same position after a hedge is matched. Confirm one of these is true:

- status-line no longer shows the same `ACTION`.
- the decision trace has `not_already_hedged=false`.
- reasons include `already_hedged`.

If the same close/cash-out `ACTION` repeats after a matched hedge, stop execution and patch duplicate-hedge detection before running live again.

## Reporting

After execution, report briefly:

- market and selection
- action
- Bet Angel response status
- betRef
- matched price
- matched stake
- balance before/after if available
- whether repeat-action guard passed

## Safety Notes

- Do not leave `"execute": true` after a one-off live action.
- Do not leave `"ai_automation_enabled": true` after a one-off live action.
- Do not execute repeated `--cycles 0 --execute` runs unless the user explicitly asks for continuous real-money automation.
- Prefer one-cycle execution plus post-check for close/cash-out actions.
- Do not cash out non-matching selections or markets with unclear `selectionId`.
- Use `.\ba.ps1 AI关` after manual intervention, mixed human/AI books, or oversized positions.
