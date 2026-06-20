# Config

Runtime config file:

- `work/football-trading-system/live_trade_manager.json`

## Top-Level Fields

- `execute`: default `false`; real actions require this plus CLI `--execute`
- `ai_automation_enabled`: default `false`; simple AI execution gate. Real actions require this, `execute=true`, and CLI `--execute`
- `heartbeat_mode`: write rolling heartbeat files on each cycle
- `heartbeat_file`: latest heartbeat JSON path
- `heartbeat_log_file`: append-only JSONL heartbeat log path
- `state_file`: cooldown and last-action state
- `poll_seconds`: sleep interval between cycles
- `max_cycles`: `0` means run until interrupted; positive numbers mean bounded cycles
- `--status-line`: command-line option that prints one compact heartbeat line per cycle
- `--status-inplay-only`: only print in-play market hint lines after the summary
- `--status-limit N`: limit the number of market hint lines printed after the summary
- `--market-id MARKET_ID`: limit monitoring/execution to one market; repeatable
- `scripts/live_trade_daemon.py`: standalone foreground/background process manager for the heartbeat loop
- `_market_id_filter`: config-level market ID allowlist for explicit plans; it must not hide API-returned markets with real matched or unmatched exposure
- `watch_inplay_only`: only manage in-play markets by default
- `always_monitor_exposure`: default `true`; always include API-returned markets with matched or unmatched exposure in heartbeat monitoring, even when `_market_id_filter` is present
- `cancel_unmatched_before_exit`: cancel stale unmatched orders before exit actions
- `action_cooldown_seconds`: suppress duplicate live actions inside this window
- `single_action_balance_cap_pct`: max size for one new place-bet action as percent of balance
- `absolute_balance_cap_pct`: hard ceiling; do not place larger new exposure than this percentage
- `default_profit_lock_ron`: default full-exit profit trigger
- `default_stop_loss_ron`: default full-exit loss trigger
- `default_reduce_fraction`: default partial reduce fraction
- `default_close_price_option`: default `closeTrade` price option
- `default_green_price_option`: default `greenAllSelections` price option
- `default_max_supplement_price_drift_pct`: if `maxSupplementPrice` is omitted, derive it from `entryPrice`

## Plan Fields

Each plan is one managed position template.

Required practical fields:

- `label`
- `marketId`
- `selectionId`
- `side`: `BACK` or `LAY`

Common control fields:

- `entryPrice`
- `targetStake`
- `allowFreshEntry`
- `allowSupplement`
- `allowCashOut`
- `withGreening`
- `inPlayOnly`
- `greenWholeMarketIfMultipleExposures`

Supplement fields:

- `maxSupplementPrice`
- `minSupplementPrice`
- `maxSupplementPriceDriftPct`
- `maxActionStakeRon`

Reduce fields:

- `reduceOnProfitRon`
- `reduceFraction`

Exit fields:

- `profitLockRon`
- `stopLossRon`
- `closePriceOption`
- `greenPriceOption`
- `trailingStartProfitRon`: future advanced field; arm trailing lock only after profit reaches this value
- `trailingDrawdownRon`: future advanced field; close after profit falls this far from best seen profit
- `lateGameMinute`: future advanced field; minute threshold for late-game de-risking
- `lateGameProfitLockRon`: future advanced field; tighter profit-lock after `lateGameMinute`
- `lateGameStopLossRon`: future advanced field; tighter stop-loss after `lateGameMinute`

Advanced guard fields:

- `maxOddsDriftPct`: future guard for adverse odds drift
- `minLiquidityRon`: future guard for minimum executable liquidity
- `stalePriceMaxSeconds`: future guard for stale Bet Angel prices
- `suspendRecoverySeconds`: future guard after market suspension

Read `advanced-exit-strategy.md` before enabling these advanced exit fields.

## Example

```json
{
  "execute": false,
  "heartbeat_mode": true,
  "heartbeat_file": "outputs/live-order-engine-heartbeat-latest.json",
  "heartbeat_log_file": "outputs/live-order-engine-heartbeat.jsonl",
  "state_file": "work/football-trading-system/live_trade_manager_state.json",
  "poll_seconds": 10,
  "max_cycles": 0,
  "watch_inplay_only": true,
  "always_monitor_exposure": true,
  "cancel_unmatched_before_exit": true,
  "action_cooldown_seconds": 45,
  "single_action_balance_cap_pct": 3.0,
  "absolute_balance_cap_pct": 10.0,
  "default_profit_lock_ron": 1.0,
  "default_stop_loss_ron": -1.0,
  "default_reduce_fraction": 0.5,
  "plans": [
    {
      "label": "cork-draw-live",
      "marketId": "1.259126078",
      "selectionId": "58805",
      "side": "BACK",
      "entryPrice": 5.0,
      "targetStake": 20.0,
      "allowSupplement": true,
      "allowCashOut": true,
      "reduceOnProfitRon": 2.0,
      "reduceFraction": 0.5,
      "profitLockRon": 4.0,
      "stopLossRon": -2.0,
      "greenWholeMarketIfMultipleExposures": false
    }
  ]
}
```

## In-Play and Filter Rules

- Use `_market_id_filter` to reduce the number of planned markets, not to hide real exposure.
- Keep `always_monitor_exposure=true` for daily use. If the user or Bet Angel creates a new matched/unmatched position, the engine should display it as `exposure_detected_without_plan` instead of silently ignoring it.
- If Bet Angel omits `inPlay=true`, the engine may infer in-play for football Match Odds markets with `status` `OPEN` or `SUSPENDED` and `startTime <= now`.
- Automatic betting, reduce, close, cash-out, or green-up still requires `status=OPEN`, explicit `selectionId`, explicit side, executable price, AI enabled, and all plan gates.
- If the GUI shows a market but API `getMarkets` does not return it, mark it `API_NOT_VISIBLE`; monitor manually and do not auto execute from Codex.

## Standalone Daemon

The daemon wrapper lives at:

- `work/football-trading-system/scripts/live_trade_daemon.py`

It starts `live_trade_manager.py --cycles 0` as a long-running process.

Global daily live-execution switch:

```powershell
.\ba.ps1 AI开
.\ba.ps1 AI关
```

Use `.\ba.ps1 AI开` to keep monitoring on and allow AI automatic Bet Angel execution. Use `.\ba.ps1 AI关` to keep monitoring on but disable real automatic execution and return to dry-run monitoring. Prefer these two commands for daily use across all qclaw football skills.

Common commands:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py run --poll 10
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py start --poll 10
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py status
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py latest --lines 40
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py stop
```

Live execution through the daemon still requires both:

- config `"execute": true`
- config `"ai_automation_enabled": true`
- daemon command `--execute`

Low-level AI execution switch for wrapper debugging only:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py ai-status
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py ai-on
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py ai-off
```

For one live match, add:

```powershell
C:\Users\zhuju\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\football-trading-system\scripts\live_trade_daemon.py start --poll 10 --execute --market-id 1.259139301
```
