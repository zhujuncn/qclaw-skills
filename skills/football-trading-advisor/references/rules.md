# Football Trading Advisor Rules

## Probability Integrity

- Never use the market price as the independent probability estimate.
- Use CGMBet26, league calibration, ELO/Form, Poisson/xG, or verified external data as the independent source.
- Global draw baseline is `26.2%`, based on CGMBet26 historical data.

## Value

Use:

```text
market_probability = 1 / market_odds
value_pct = (true_probability - market_probability) / market_probability * 100
```

Decision:

- `value_pct >= 20`: high edge, standard stake if all other gates pass.
- `10 <= value_pct < 20`: keep, normal candidate.
- `5 <= value_pct < 10`: marginal; watch or reduced stake.
- `value_pct < 5`: cancel.

## Kelly

For BACK:

```text
b = odds - 1
q = 1 - p
kelly = (b * p - q) / b
half_kelly = max(0, kelly * 0.5)
```

Use Half Kelly by default. Use Quarter Kelly for uncertain data, weak matching, or odds above 8.

## Dynamic Daily Bankroll Budget

Let:

```text
B = current Bet Angel balance
P = yesterday verified net P/L
R = P / prior-day starting balance
```

Default policy:

- Start from a `3%` base daily stake/liability budget.
- If yesterday was profitable and verified, add a bounded profit overlay: `min(50% of P, 2% of B)`.
- If yesterday was losing, reduce the base budget; never increase stake to recover losses.
- `10%` of B is the absolute hard stop, not the normal daily target.
- For LAY bets, count liability (`stake * (price - 1)`), not stake, toward the same daily budget.
- Do not use a flat 1 RON stake except for dry-run probes, API tests, or explicit user instruction.

Budget ladder:

| Yesterday state | Daily budget |
|---|---:|
| Result unverified, API errors, or weak settlement data | `1%` of B, advice-first |
| Loss worse than `-2%` of prior bankroll | `0.5%` of B or pause live betting |
| Loss between `-1%` and `-2%` | `1%` of B |
| Loss between `0%` and `-1%` | `2%` of B |
| Flat day, no verified edge | `3%` of B |
| Profit up to `+1%`, CLV not negative | `3% of B + min(50% of P, 1% of B)` |
| Profit `+1%` to `+3%`, positive CLV/calibration acceptable | `3% of B + min(50% of P, 2% of B)` |
| Profit above `+3%` plus positive CLV and no execution errors | up to `6%` of B |
| Three verified profitable days in a row, positive 7-day CLV, drawdown under `3%` | up to `8%` of B |
| Explicit user approval only | up to `10%` of B |

Allocation across accepted bets:

- Allocate by relative signal strength: conservative edge, value edge, Kelly fraction after haircut, confidence tier, name-match confidence, odds risk, and correlation.
- For two accepted BACK bets, use `70% / 30%` when one signal is materially stronger, or `60% / 40%` when both are comparable.
- Apply a correlation penalty before allocation: same league, same kickoff cluster, same country, or same model failure mode must reduce the weaker leg.
- Cap any single BACK stake at `70%` of the daily budget unless there is only one accepted bet.
- Cap any single LAY liability at `3%` of B even when the daily budget is higher.

## Failed-Gate Probe Bets

When the user enables probe mode, candidates that were selected by CGMBet26/advisor but failed the official hard gate may receive a separate `1 RON` probe bet for record and review.

Probe rules:

- Probe bets are not official strategy bets and must be labeled `probe_failed_gate`.
- Probe stake is fixed at `1 RON` per candidate; do not scale it with bankroll.
- Probe bets are excluded from the dynamic official stake allocation, but still count toward real cash exposure and P/L review.
- Place a probe only when Bet Angel market and selection are matched with high confidence, market status is OPEN, and the side/selection is explicit.
- Do not place a probe when there is no Bet Angel market match, no selectionId, wrong competition/team category, or API uncertainty.
- Keep the original failed-gate reason in the journal, such as `RISK_FLAG`, `LOW_ODDS_TRAP`, `MARGINAL`, `NO_BA_MATCH`, or `FORM_ELO_DIVERGENCE`.
- In review, compare probe results against official hard-gate decisions to decide whether a gate is too strict, too loose, or correctly rejecting noise.

## Auto-Execution Authorization

The user has pre-authorized the scheduled `Daily Football Trading Advisor` automation to place bets automatically after the daily model run.

Auto-execution scope:

- Applies only to the configured recurring automation, not arbitrary manual/ad hoc requests.
- Official bets may be placed automatically when every official hard gate passes.
- Probe bets may be placed automatically under the separate `probe_failed_gate` rules.
- No additional human confirmation is required for in-scope automated official/probe bets.

Hard limits:

- Total official stake/liability must stay inside the selected dynamic daily budget.
- Total official stake/liability must never exceed `10%` of current Bet Angel balance.
- LAY liability, not stake, counts toward all exposure caps.
- Any market/name/selection uncertainty cancels auto-execution for that bet.
- Odds above `8.0`, relaxed gates, discretionary overrides, or speculative bets require explicit user approval.

## Odds Gate

- `< 2.0`: default skip for pre-match BACK bets.
- `2.0-4.0`: preferred.
- `4.0-8.0`: acceptable if value is strong.
- `8.0-10.0`: reduce stake.
- `> 10.0`: skip unless explicitly approved as speculative.

## Form-ELO Divergence

When ELO favors Team A but recent Form favors Team B:

- Avoid LAY on the Form-strong side.
- Reduce stake by 50% if betting the ELO favorite.
- Consider `BACK Draw` or `BACK Form team` only when value is positive.
- Strong divergence requires `abs(ELO diff) > 100` and `abs(Form diff) > 10`.
- Weak divergence is a warning, not a bet.

## Draw Strategy

Use draw bets only when at least two signals agree:

- CGMBet26 draw probability above market implied probability by at least 10%.
- Both teams have high recent draw tendency.
- Poisson/xG draw probability agrees.
- DJYY Balance Draw pick agrees.

Do not use old `31.85%` draw baseline for general calculations.

## Bet Angel Safety

Required payload shape:

```json
{
  "marketId": "1.xxxxx",
  "async": false,
  "globalSettings": {"accountId": "DEFAULT"},
  "betsToPlace": [{
    "selectionId": 12345,
    "type": "BACK",
    "price": 3.5,
    "stake": 1.0
  }]
}
```

Rules:

- `selectionId` must be `int`.
- `type` must be `BACK` or `LAY`.
- `stake` and `price` must be floats.
- Do not assume Draw selection is always `58805`.
- Confirm market is monitored/available before reading prices.
- One bet per match.
