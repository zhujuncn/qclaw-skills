# Cash Out Guard Evolution

## Goal

Improve Cash Out Guard from actual feedback, trade outcomes, API errors, and user corrections while keeping live-money permissions strict and auditable.

## Non-Evolvable Rules

Never evolve away these controls:

- Require explicit authorization before real-money place, cancel, modify, green, or close operations.
- Require exact `marketId` and `selectionId` when selection-specific.
- Report price mode and execution risk before live action.
- Do not hide failed exits, unmatched bets, or suspended-market risks.
- Do not optimize only for profit while ignoring drawdown, fill risk, and duplicated exposure.

## Feedback Signals

Treat any of the following as evolution input:

- User says a recommendation was good, bad, late, too early, too risky, or missed.
- A cash-out action fails, partially fills, times out, or executes at a poor price.
- BA API logs show repeated unmatched bets, duplicate triggers, suspended-market calls, or missing pending-result polling.
- Settlement or trading records show repeated losses after a specific rule.
- User changes risk preference, stake size, league focus, or CGMBet confidence thresholds.

## Evolution Loop

Use this loop after every relevant feedback event:

1. Capture the event.
2. Classify it.
3. Decide whether it is a one-off, a caution, or a rule change.
4. Update the recommendation for the current task.
5. If the feedback is strong enough, patch the skill reference files.
6. Report what changed and what remains experimental.

## Event Capture Schema

When writing a feedback record, use JSONL with this shape:

```json
{
  "ts": "2026-06-17T12:00:00+03:00",
  "source": "user|api_log|settlement|manual_review",
  "marketId": "1.xxxxx",
  "selectionId": 58805,
  "strategy": "stop_loss_green|profit_lock|time_exit|price_drift|partial_green|whole_market_green",
  "signal": "success|failure|warning|preference|api_error",
  "summary": "short factual description",
  "evidence": "log path, bet ref, user quote, or settlement summary",
  "proposed_change": "candidate rule update",
  "status": "captured|promoted|rejected|needs_more_data"
}
```

Prefer storing feedback in the active workspace under `outputs/cash_out_guard_feedback.jsonl` unless the user asks for a different location.

## Classification

Use these classes:

- `execution_failure`: endpoint failed, market suspended, timeout, partial fill, duplicate trigger.
- `price_quality`: exit filled too poorly, spread too wide, liquidity insufficient.
- `timing_error`: green too early, too late, or missed planned minute.
- `risk_preference`: user wants more aggressive or conservative exits.
- `model_error`: CGMBet confidence or value estimate did not match outcome behavior.
- `process_gap`: missing API field, missing pending poll, missing unmatched-bet check.

## Promotion Rules

Patch strategy guidance when any condition is met:

- Same failure class appears at least 3 times.
- A single event created material loss or dangerous exposure.
- User explicitly says to change the rule.
- API behavior contradicts an existing instruction.

For weaker evidence, keep it as a captured note and mark the change experimental in current-task advice only.

## Solidify Changes

When promoting feedback into the skill:

1. Patch `references/strategies.md` for strategy thresholds, formulas, or operational cautions.
2. Patch `SKILL.md` only for core workflow, trigger description, or safety boundary updates.
3. Keep edits small and evidence-based.
4. Preserve official Bet Angel source links unless a newer official source replaces them.
5. Re-run a lightweight structure validation after editing.

## Default Evolution Heuristics

Apply these unless user feedback overrides them:

- Repeated poor fills: add stricter spread/liquidity checks before `BEST_MARKET_PRICE`.
- Repeated duplicate exits: require `async=true`, pending-result polling, and a cooldown.
- Repeated stale exposure: make unmatched-bet cancellation mandatory before green.
- Repeated early profit giveback: add tiered partial green at 25%, 50%, or 75% hedge.
- Repeated late stop-loss: shift stop from currency P/L to tick drift or hybrid trigger.
- Repeated small test losses: tighten rules for 1 RON experiments before changing production logic.

## Reporting Evolution

When feedback changes the strategy, report:

- What feedback was captured.
- Whether it changed current advice only or the persistent skill.
- Exact file updated when persistent.
- What evidence is still needed before stronger automation.
