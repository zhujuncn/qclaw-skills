# Cash Out Guard Strategies

## Local API Interpretation

If recent Bet Angel API diagnostics show `getMarketPrices` fields such as `GREENING_PROFIT`, `CLOSE_TRADE_PROFIT`, `profIfWins`, or `closeProfGreen`, the system can preview cash-out outcomes.

If diagnostics do not show `greenAllSelections`, `closeTrade`, or their pending-result endpoints, treat the setup as monitoring-only until execution is explicitly added and authorized.

## Strategy Families

Before changing thresholds, check `evolution.md` for feedback records and promotion rules. Treat any newly observed outcome as input to the strategy, but keep unproven changes marked experimental.

### Stop-Loss Green

Close when `closeProfGreen` falls below a loss threshold.

Use a fixed RON threshold for tiny test stakes, but prefer bankroll percentage or R-multiple thresholds for production.

Example rule:

```text
if closeProfGreen <= -1.00 RON:
  recommend closeTrade with withGreening=true
```

Evolve this rule when losses repeatedly occur before the currency threshold is reached. In that case, add a tick-drift or percentage-drift trigger before the RON stop.

### Profit Lock

Green when the trade reaches a target profit.

Good defaults:

- Test stakes: lock at small positive RON once liquidity is acceptable.
- Production: lock at `+0.5R`, `+1R`, or model-defined expected-value decay.

Evolve this rule when profitable trades repeatedly reverse before the target. Add partial green at 25%, 50%, or 75% hedge instead of waiting for full target.

### Time-Based Exit

Use when the edge depends on timing.

Examples:

- Pre-kickoff odds move did not arrive by T-minus 5 minutes: close or cancel.
- In-play no-goal scenario reaches a planned minute: green if positive, stop if negative.
- Late match volatility increases: reduce exposure before suspension-prone periods.

Evolve this rule when user feedback says exits are consistently too early or too late for a league, match state, or strategy family.

### Price Drift Exit

Track entry price versus current exit price. Exit when the market moves against the trade by a defined number of ticks or percentage.

This often reacts faster than waiting for currency P/L thresholds.

### Partial Green

Do not assume every exit should be full cash out.

For a BACK entry hedged by a LAY:

```text
fullHedgeLayStake = backStake * backOdds / currentLayOdds
partialLayStake = fullHedgeLayStake * fraction
```

Use fractions such as 0.25, 0.50, or 0.75 to lock part of the profit while leaving upside.

### Free-Bet Style Exit

After a favorable BACK move, lay a smaller amount so the losing outcome is near break-even while the winning outcome keeps upside. Compute exact stakes from current odds and desired minimum losing-side P/L.

### Whole-Market Green

Use `greenAllSelections` when more than one selection has exposure or when the user wants the market flattened as a unit.

Do not close only one selection if that leaves hidden risk on another selection.

### Liquidity and Spread Protection

Avoid immediate best-price green when:

- spread is wide
- available size is below exit size
- market just returned from suspension
- in-play delay makes re-triggering likely

Use `BEST_MARKET_PRICE` for urgent exits. Consider reverse-price modes only when a better price is worth the fill risk.

Evolve this rule after poor fills by adding stricter spread, available-size, or delay-after-suspension requirements.

### Unmatched Bet Hygiene

Do not green over stale unmatched bets unless intentionally handled. Old unmatched bets can fill after the green and recreate exposure.

Preferred sequence:

1. Read unmatched count.
2. Cancel stale unmatched bets or wait for fill/kill expiry.
3. Refresh prices and P/L preview.
4. Green or close.

Evolve this rule to mandatory cancellation if stale unmatched bets recreate exposure more than once.

### CGMBet26 Integration

Use the research confidence to tune exit strictness:

- High-confidence value bet: allow wider profit run and partial green.
- Medium-confidence bet: lock profit earlier.
- Low-confidence or 1 RON test: use mechanical small stop-loss and small profit lock.

## Reporting Template

When giving advice, include:

- Market and selection
- Current matched/unmatched exposure
- `closeProfGreen` or nearest available preview value
- Recommended action
- Price mode
- Execution risk
- Exact confirmation needed before live action
- Feedback/evolution note when a rule changed or should be watched

## Sources to Prefer

Use official Bet Angel documentation when possible:

- Bet Angel API Betting Component: `https://www.betangel.com/api-guide/betting_component.html`
- Green All Profit condition: `https://www.betangel.com/user-guide/green_all_profit.html`
- Close Trade Profit condition: `https://www.betangel.com/user-guide/close_trade_profit.html`
- Number of Unmatched Bets condition: `https://www.betangel.com/user-guide/number_of_unmatched_bets.html`
