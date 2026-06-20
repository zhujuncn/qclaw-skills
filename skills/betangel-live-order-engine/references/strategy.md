# Strategy

Objective:

- maximize long-run expected value inside hard risk limits

Do not describe this engine as guaranteed profit maximization. Treat it as a rule-based manager for supplement, reduce, and exit decisions.

## Decision Order

1. Exit first when stop-loss or full profit-lock is already hit.
2. Reduce exposure second when profit is positive enough for a partial hedge.
3. Apply advanced exit layers such as trailing profit lock or late-game lock when configured.
4. Supplement only when no exit or reduce trigger has already fired.
5. Otherwise hold and keep heartbeat monitoring.

This order avoids contradictory actions in the same cycle.

For automatic football exits, follow the five-layer stack in `advanced-exit-strategy.md`:

1. Fixed stop-loss.
2. Fixed full profit-lock.
3. Partial reduce / scale-out.
4. Trailing profit lock.
5. Late-game lock or de-risk adjustment.

## Supplement Logic

For `BACK` plans:

- use current executable back-entry price from the best available lay
- do not supplement above `maxSupplementPrice`

For `LAY` plans:

- use current executable lay-entry price from the best available back
- do not supplement below `minSupplementPrice`

Supplement only toward the configured `targetStake`, never above it.

## Partial Reduce Logic

When `reduceOnProfitRon` is reached:

- place an opposing hedge bet
- default hedge fraction is `reduceFraction`
- use:
  - `BACK` entry -> reduce with `LAY`
  - `LAY` entry -> reduce with `BACK`

Approximate hedge stake:

```text
hedgeStake = matchedStake * entryPrice / currentOpposingPrice * reduceFraction
```

If `entryPrice` is missing, fall back to:

```text
hedgeStake = matchedStake * reduceFraction
```

This is a practical exposure reduction rule, not a perfect equalized hedge formula.

## Full Exit Logic

Use `GREEN_ALL` when:

- more than one selection in the market has exposure
- the user wants market-level flattening

Use `CLOSE_TRADE` when:

- one selection is the clear managed position
- selection-level closure is preferred

After a `CLOSE_TRADE`, Bet Angel normally records the hedge as an opposing matched bet. Do not repeat close/cash-out if the opposing matched stake already covers most of the original exposure. The engine uses an `already_hedged` style guard for this case.

## Hard Risk

- market must be `OPEN`
- prefer `in-play` only unless explicitly overridden
- `selectionId` must exist for selection-level actions
- executable price must exist
- use `--market-id` or `_market_id_filter` when enabling live execution for a single running match
- respect balance caps on any new `placeBets` action
- suppress repeated live actions inside the cooldown window
- cancel stale unmatched bets before exit when configured
- verify post-execution state before allowing another close/cash-out on the same selection
- never execute on `exposure_detected_without_plan`
- human large positions and oversized positions default to monitor-only
- if the user says to hold until full time, do not trade that selection automatically
- after one `REDUCE_EXPOSURE`, block repeated reduce until a fresh Bet Angel order refresh confirms the new hedge state
