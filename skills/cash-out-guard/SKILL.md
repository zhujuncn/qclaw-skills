---
name: cash-out-guard
description: Bet Angel Professional and Betfair cash-out / greening guard workflow with feedback-driven strategy evolution. Use when the user asks about Cash Out Guard, cash out, green up, greening, closeTrade, greenAllSelections, closeProfGreen, profIfWins, Bet Angel API position exits, Betfair exchange hedging, football trading exits, stop-loss, profit lock, safe automation around closing open Betfair positions, or asks to learn from outcomes, feedback, trade history, failed exits, strategy iteration, or auto-evolve cash-out rules. This skill provides advice and API request construction only; require explicit user authorization before any real-money betting, greening, closing, canceling, or modifying action.
---

# Cash Out Guard

## Purpose

Use this skill to inspect Bet Angel positions, explain cash-out / greening choices, and recommend safe exit actions for Betfair exchange trades.

Treat Cash Out as a hedge using opposing exchange bets. Bet Angel exposes this mainly through `getMarketPrices` previews plus `greenAllSelections` and `closeTrade` execution endpoints.

Run the feedback evolution loop whenever the user provides new results, complaints, corrections, missed exits, settlement outcomes, API errors, or asks to improve the strategy.

## Safety Boundary

Never execute real-money actions silently.

Before calling any endpoint that places, cancels, modifies, greens, closes, or otherwise changes Betfair exposure, require explicit confirmation of:

- `marketId`
- `selectionId` when selection-specific
- action: `greenAllSelections`, `closeTrade`, cancel, modify, or place
- greening mode: `withGreening=true/false` when applicable
- price mode or fixed price
- stake or exposure effect when known
- whether async execution is allowed

Advice-only analysis may read API data without this confirmation.

The safety boundary is non-evolvable. Never weaken or remove explicit authorization requirements as an optimization.

## Core Workflow

1. Load the `betangel-api` skill when Bet Angel endpoint details or live API calls are needed.
2. Read current positions with `getMarketPrices`; request at least:
   - `PROFIT`
   - `CLOSE_TRADE_PROFIT`
   - `GREENING_PROFIT`
   - `MATCHED_BET_SUMMARY`
   - `UNMATCHED_BET_SUMMARY`
   - best-price and in-play fields if available.
3. Check market status. Do not propose execution on closed or suspended markets except as a delayed/monitoring plan.
4. Check unmatched bets. Prefer canceling stale unmatched bets or waiting until unmatched count is zero before greening, unless the chosen Bet Angel green-up rules explicitly handle them.
5. Select exit mode:
   - Use `greenAllSelections` for whole-market equalized P/L.
   - Use `closeTrade` for one selection.
   - Use `closeTrade` with `withGreening=true` to distribute P/L across outcomes.
   - Use `closeTrade` with `withGreening=false` only when the user intentionally wants selection-level closure without full green.
6. For in-play actions, prefer `async=true` and poll the pending-result endpoint to avoid duplicate triggers.
7. Report the recommended action and the risks before requesting execution confirmation.
8. After any user feedback or observed outcome, run the evolution workflow in `references/evolution.md`.

## Endpoint Patterns

Preview:

```json
POST /api/markets/v1.0/getMarketPrices
{
  "dataRequired": [
    "PROFIT",
    "CLOSE_TRADE_PROFIT",
    "GREENING_PROFIT",
    "MATCHED_BET_SUMMARY",
    "UNMATCHED_BET_SUMMARY"
  ]
}
```

Whole-market green:

```json
POST /api/betting/v1.0/greenAllSelections
{
  "marketId": "1.xxxxx",
  "priceOption": "BEST_MARKET_PRICE",
  "async": true
}
```

Selection close:

```json
POST /api/betting/v1.0/closeTrade
{
  "marketId": "1.xxxxx",
  "selectionId": 58805,
  "withGreening": true,
  "priceOption": "BEST_PRICE",
  "async": true
}
```

## Strategy Reference

For detailed exit strategies, thresholds, partial hedging formulas, and implementation cautions, read `references/strategies.md`.

For feedback capture, strategy iteration, and auto-evolution rules, read `references/evolution.md`.
