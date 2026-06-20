---
name: betangel-live-order-engine
description: Bet Angel live order and position management engine for the qclaw football workflow. Use when Codex needs to monitor in-play Bet Angel exposure with heartbeat polling, inspect matched and unmatched orders, manage supplement or scale-in actions, reduce exposure, cash out, or green up under hard risk limits, or tune the local live trade manager behavior.
---

# Bet Angel Live Order Engine

Use this skill as the local entrypoint for Bet Angel real-time order and position management inside the qclaw workflow.

Execution entrypoint:

- `scripts/engine.py`

Runtime config:

- `C:\Users\zhuju\Documents\Codex\2026-06-16\qclaw-skill\work\football-trading-system\live_trade_manager.json`

Standalone daemon wrapper:

- `C:\Users\zhuju\Documents\Codex\2026-06-16\qclaw-skill\work\football-trading-system\scripts\live_trade_daemon.py`

## Core Workflow

1. Read current Bet Angel market state:
   - balance
   - loaded markets
   - market prices
   - matched and unmatched bets
2. Restrict focus to active exposure and explicit plans:
   - prefer `in-play` markets
   - always monitor API-returned markets with matched or unmatched exposure, even when `_market_id_filter` is set
   - keep unmatched cleanup ahead of exit actions
   - never treat a missing `selectionId` or missing executable price as tradable
3. Evaluate decisions in this order:
   - stop-loss or profit-lock exit
   - partial reduce / scale-out
   - supplement / scale-in
   - hold and continue heartbeat monitoring
4. Record the full decision trace:
   - market snapshot
   - gate trace
   - proposed actions
   - live execution payload and response when enabled

## Live Execution Runbook

When asked to monitor, analyze, and execute an in-play close/cash-out action, use this order:

1. Run one dry-run status check with `--status-line`.
2. Read the compact hints:
   - `ACTION` means the engine found an executable supplement, reduce, close, or green signal.
   - `WAIT` means the engine is holding; use the `wait:*` reason as the blocker.
3. Before executing, confirm the action still passes:
   - market is `OPEN`
   - market is `inPlay` when required
   - selection is explicit
   - price exists
   - close/cash-out preview still meets the configured threshold
4. For one-off real execution, temporarily set config `"execute": true`, run with `--execute --cycles 1 --status-line`, then restore `"execute": false`.
5. Read the output JSON `actionLog` and report:
   - action type
   - Bet Angel payload
   - response status
   - betRef
   - matched price and matched stake
6. Run one more dry-run `--status-line` after execution to verify:
   - no repeated close/cash-out signal remains
   - balance and exposure changed as expected
   - `already_hedged` or equivalent guard blocks duplicate close when a hedge is matched

For the detailed operational checklist, read `references/live-execution-runbook.md`.

## Safety Boundary

Global daily live-execution switch for all qclaw football skills:

```powershell
.\ba.ps1 AI开
.\ba.ps1 AI关
```

Use `.\ba.ps1 AI开` to keep monitoring on and allow AI automatic live execution through Bet Angel. It restarts the live daemon with `--execute`.

Use `.\ba.ps1 AI关` to keep monitoring on but disable AI automatic live execution. It restarts the live daemon in dry-run monitoring.

Do not use lower-level `ai-on`, `ai-off`, or direct `--execute` as the daily interface unless debugging the wrapper itself.

Default mode is dry-run.

Do not execute real-money actions unless both are true:

- config has `"execute": true`
- config has `"ai_automation_enabled": true`
- command line includes `--execute`

Use `live_trade_daemon.py ai-on` to enable the AI execution gate and `live_trade_daemon.py ai-off` to disable it. Keep AI off by default after manual or mixed-position incidents.

Keep these hard gates:

- market status must be `OPEN`
- prefer `in-play` monitoring unless the plan explicitly says otherwise; when Bet Angel omits `inPlay=true`, infer in-play only for already-started football Match Odds markets with status `OPEN` or `SUSPENDED`
- `selectionId` must be explicit for selection-level actions
- executable price must be present
- single new place-bet action must stay inside the configured balance cap
- use cooldown state to avoid repeated duplicate actions

## In-Play API/GUI Diagnostics

When the Bet Angel GUI shows in-play matches but `--status-line` reports `markets=0` or `inPlay=0`, diagnose in this order:

1. Check whether `_market_id_filter` is still pinned to stale market IDs. It should never hide API-returned markets with real matched or unmatched exposure.
2. Query `getMarkets` plus `getMarketPrices` and compare Match Odds names, `status`, `inPlay`, and `startTime` against the GUI.
3. Treat `OPEN` or `SUSPENDED` football Match Odds markets with `startTime <= now` as in-play-equivalent for monitoring. Real execution still requires `status=OPEN`.
4. Query `getMarketBets` directly for known market IDs. If bets are readable but prices/metadata are absent, downgrade to monitor-only and do not auto close/add/reduce.
5. If a market is visible in the GUI but absent from API `getMarkets`, mark it `API_NOT_VISIBLE`; do not auto execute until the market appears in API output with explicit selection IDs and prices.

## Heartbeat Mode

Heartbeat mode means periodic polling plus rolling status artifacts.

Use it to:

- monitor in-play exposure every few seconds
- keep a latest heartbeat snapshot in `outputs/`
- append a lightweight heartbeat log for later review

Read `references/config.md` when changing:

- polling interval
- heartbeat files
- cooldown behavior
- in-play filtering
- per-plan thresholds

## Action Types

The engine can emit or execute:

- `SUPPLEMENT`
- `REDUCE_EXPOSURE`
- `CANCEL_UNMATCHED`
- `GREEN_ALL`
- `CLOSE_TRADE`

`REDUCE_EXPOSURE` is the partial scale-out path. It places an opposing hedge bet using the configured reduce fraction and current executable price.

Read `references/strategy.md` before changing supplement, reduce, stop-loss, or profit-lock behavior.

Read `references/advanced-exit-strategy.md` before configuring automatic in-play stop-loss, profit-lock, partial reduce, trailing stop, late-game lock, human/manual holds, oversized positions, or live execution for a single running football match.

## Commands

Dry-run one cycle:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\engine.py --cycles 1
```

Heartbeat monitoring:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\engine.py --cycles 0 --poll 10
```

Heartbeat monitoring with chat-visible terminal feedback:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\engine.py --cycles 0 --poll 10 --status-line
```

Heartbeat monitoring with only in-play match feedback once per minute:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\engine.py --cycles 0 --poll 60 --status-line --status-inplay-only
```

Standalone daemon foreground monitoring:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py run --poll 10
```

Standalone daemon background monitoring:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py start --poll 10
```

Check or stop the background daemon:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py status
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py stop
```

AI execution gate:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py ai-status
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py ai-on
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py ai-off
```

Short control commands:

Daily simplified interface:

```powershell
.\ba.ps1 AI开
.\ba.ps1 AI关
.\ba.ps1 状态
.\ba.ps1 最新
```

Keep monitoring always on. `AI开` enables real automatic live execution by restarting the daemon with `--execute`. `AI关` disables real automatic execution and restarts the daemon in dry-run monitoring. `状态` and `最新` are read-only inspection commands. Legacy commands such as `monitor`, `auto-on`, and `auto-off` still work, but daily use should prefer `AI开` and `AI关`.

```powershell
.\ba.ps1 监控
.\ba.ps1 AI开
.\ba.ps1 AI关
.\ba.ps1 自动开
.\ba.ps1 自动关
.\ba.ps1 状态
.\ba.ps1 最新

.\work\football-trading-system\scripts\ba-live.ps1 monitor
.\work\football-trading-system\scripts\ba-live.ps1 ai-on
.\work\football-trading-system\scripts\ba-live.ps1 ai-off
.\work\football-trading-system\scripts\ba-live.ps1 auto-on
.\work\football-trading-system\scripts\ba-live.ps1 auto-off
.\work\football-trading-system\scripts\ba-live.ps1 status
.\work\football-trading-system\scripts\ba-live.ps1 latest
```

Use `监控` / `monitor` for dry-run monitoring only. Use `自动开` / `auto-on` only when real automatic stop-loss, profit-lock, reduce, supplement, close, or cash-out is intended and all plan rules are correct. Use `自动关` / `auto-off` to immediately disable AI execution and restart dry-run monitoring. In chat, interpret the short Chinese commands the same way:

- `监控`: dry-run monitoring, AI off
- `AI开`: enable AI and restart daemon with `--execute`; allow real automatic betting, reduce, close, and cash-out when all gates pass
- `AI关`: disable AI live execution and restart dry-run monitoring
- `自动开`: enable AI and restart daemon with `--execute`
- `自动关`: disable AI and restart dry-run monitoring
- `状态`: show pid and heartbeat
- `最新`: show heartbeat plus log tail

Status-line output includes one summary line plus up to three compact market hints:

```text
monitoring | 09:22:44 | mode=dry-run | balance=990.41 | markets=5 | inPlay=0 | actions=0 | suppressed=0 | executed=0
WAIT | Cork City v Treaty United | The Draw | wait:in_play | stake=15.2/22.8 | price=950.0 | p/l=-15.12
```

Live execution:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\engine.py --execute --cycles 1
```

## References

- Read `references/config.md` for config and plan fields.
- Read `references/strategy.md` for decision order, reduce formulas, and hard-risk guidance.
- Read `references/advanced-exit-strategy.md` for the five-layer in-play exit stack, human/AI control balance, oversized-position rules, and conservative football templates.
- Read `references/live-execution-runbook.md` before running a real close/cash-out or green-up from status-line signals.
