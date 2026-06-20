# Advanced Exit Strategy

Use this reference when tuning in-play football stop-loss, profit-lock, partial reduce, trailing exits, or late-game behaviour.

Do not treat the strategy as guaranteed profit maximisation. Treat it as a conservative rule stack for managing live exchange exposure under Bet Angel and Betfair market constraints.

## Five-Layer Exit Stack

Evaluate exits in this order:

1. Fixed stop-loss.
2. Fixed full profit-lock.
3. Partial reduce / scale-out.
4. Trailing profit lock.
5. Late-game lock or de-risk adjustment.

Never allow supplement / scale-in to run before all exit layers have been checked.

## Layer 1: Fixed Stop-Loss

Use fixed stop-loss as the hard damage limit for one managed position.

Recommended fields:

```json
{
  "stopLossRon": -2.0,
  "allowCashOut": true,
  "withGreening": true
}
```

Trigger:

```text
if closeProfGreen <= stopLossRon:
  CLOSE_TRADE
```

For market-level multi-selection exposure, use `GREEN_ALL` only when the intent is to flatten the whole market.

## Layer 2: Fixed Full Profit-Lock

Use full profit-lock when the trade has already reached the planned return and the aim is to remove event risk.

Recommended fields:

```json
{
  "profitLockRon": 2.0,
  "allowCashOut": true,
  "withGreening": true
}
```

Trigger:

```text
if closeProfGreen >= profitLockRon:
  CLOSE_TRADE
```

## Layer 3: Partial Reduce

Use partial reduce when the trade is positive but not yet strong enough for full exit.

Recommended fields:

```json
{
  "reduceOnProfitRon": 1.0,
  "reduceFraction": 0.5
}
```

Trigger:

```text
if closeProfGreen >= reduceOnProfitRon and closeProfGreen < profitLockRon:
  REDUCE_EXPOSURE
```

For a BACK entry, reduce with LAY. For a LAY entry, reduce with BACK.

## Layer 4: Trailing Profit Lock

Use trailing exit after the trade has moved into profit. Track the best seen green or close profit per plan label in state.

Recommended future fields:

```json
{
  "trailingStartProfitRon": 1.2,
  "trailingDrawdownRon": 0.6
}
```

Trigger:

```text
if bestProfit >= trailingStartProfitRon
and currentProfit <= bestProfit - trailingDrawdownRon:
  CLOSE_TRADE
```

Do not arm trailing stop while current profit is negative.

## Layer 5: Late-Game Lock

Use late-game rules to reduce exposure as football time decay increases and comeback windows shrink.

Recommended future fields:

```json
{
  "lateGameMinute": 75,
  "lateGameProfitLockRon": 0.8,
  "lateGameStopLossRon": -1.2
}
```

Trigger:

```text
if inPlayMinute >= lateGameMinute:
  use lateGameProfitLockRon instead of profitLockRon
  use lateGameStopLossRon instead of stopLossRon
```

When in-play minute is unavailable, do not apply late-game tightening.

## Safety Guards

Apply these guards before any real execution:

- Market status must be `OPEN`.
- Market must be `inPlay` when plan `inPlayOnly` is true.
- `selectionId` must be explicit for `CLOSE_TRADE` or `REDUCE_EXPOSURE`.
- Executable price must exist for any `placeBets` hedge.
- Cancel stale unmatched bets before exit when configured.
- Do not execute on `exposure_detected_without_plan`.
- Do not execute if Bet Angel market/selection data is stale or inconsistent.
- Do not supplement a manual or oversized position unless explicitly authorized.
- Use `--market-id` or `_market_id_filter` when enabling `--execute` for one live match.
- Respect human/AI authority boundaries in `Human and AI Control Balance`.

Recommended future guard fields:

```json
{
  "maxOddsDriftPct": 12.0,
  "minLiquidityRon": 200.0,
  "stalePriceMaxSeconds": 8,
  "suspendRecoverySeconds": 15
}
```

## Conservative Football Template

Use this for a small in-play BACK position when the user asks for automatic stop-loss and profit-lock only:

```json
{
  "label": "match-back-selection-live-exit",
  "marketId": "1.xxxxx",
  "selectionId": "12345",
  "selectionName": "Team Name",
  "side": "BACK",
  "entryPrice": 1.4,
  "targetStake": 10.0,
  "allowFreshEntry": false,
  "allowSupplement": false,
  "allowCashOut": true,
  "inPlayOnly": true,
  "reduceOnProfitRon": 1.0,
  "reduceFraction": 0.5,
  "profitLockRon": 2.0,
  "stopLossRon": -2.0,
  "greenWholeMarketIfMultipleExposures": false,
  "withGreening": true
}
```

Run live execution only with all of:

```text
config execute=true
config ai_automation_enabled=true
command includes --execute
```

For daily operation, use the global wrapper:

```powershell
.\ba.ps1 AI开
.\ba.ps1 AI关
```

Use `.\ba.ps1 AI开` to keep monitoring on and allow AI automatic live execution. Use `.\ba.ps1 AI关` immediately after manual intervention, oversized positions, or mixed human/AI books.

For one match, also use:

```text
--market-id MARKET_ID
```

or:

```json
"_market_id_filter": ["MARKET_ID"]
```

## Human and AI Control Balance

Apply these governance rules before live execution and after every position refresh:

- Human large positions: AI may monitor and alert only. Do not auto-close, auto-green, auto-reduce, or auto-supplement.
- AI small positions: AI may execute configured stop-loss, profit-lock, and one partial reduce when all hard gates pass.
- User says hold until full time: set the position to `manual_hold_until_end`; AI must alert only and must not trade that selection.
- Oversized position: if matched stake materially exceeds `targetStake`, downgrade to `monitor_only` unless the user explicitly re-authorizes automated exits for that full size.
- One reduce per market/selection: after `REDUCE_EXPOSURE`, do not reduce again until fresh Bet Angel orders confirm the new hedge state and the user or config explicitly permits another reduce stage.

Recommended plan fields:

```json
{
  "owner": "ai|human|mixed",
  "manualHoldUntilEnd": false,
  "monitorOnly": false,
  "oversizedStakeMultiplier": 2.0,
  "maxReduceExecutions": 1,
  "requiresPostReduceOrderRefresh": true
}
```

Execution policy:

```text
if owner == "human" and matchedStake > targetStake:
  monitor_only

if manualHoldUntilEnd:
  monitor_only_and_alert

if matchedStake >= targetStake * oversizedStakeMultiplier:
  monitor_only

if reduceExecutionCount >= maxReduceExecutions:
  block_reduce

if last action was REDUCE_EXPOSURE and no fresh order refresh:
  block_reduce
```

For mixed books, separate the explanation into:

- original human stake
- AI supplement stake
- AI hedge/reduce stake
- expected P/L for each outcome
- current cash-out / green figure

Never describe a mixed BACK/LAY book as profitable based only on score. Always reconcile the Bet Angel `profIfWins`, matched BACK, and matched LAY rows.
