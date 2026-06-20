# Decision Rules Configuration

## Voting Thresholds

| Vote Count | Decision | Action | Kelly Fraction |
|------------|----------|--------|----------------|
| 4/4 | UNANIMOUS | Bet immediately | Full Kelly (0.5) |
| 3/4 | STRONG | Bet immediately | Half Kelly (0.5) |
| 2/4 | VALUE | Standard position | Quarter Kelly (0.25) |
| 1/4 | CAUTION | Small test | Quarter Kelly (0.25) |
| 0/4 | NO BET | Skip | - |

---

## Signal Strength Matrix

| Source | Strong Signal | Weak Signal | No Signal |
|--------|--------------|-------------|-----------|
| Sofascore | xG diff > 0.5, momentum +, recent form W/W/W | xG diff < 0.2 | stale data |
| CGMBet | Tier 1 + Value% > 15% + P < 5% | Tier 2 + Value% > 5% | Tier 3 or no Value |
| Match Analyzer | Confidence >= 4 stars | Confidence 3 stars | Confidence < 3 stars |

---

## Market Selection Priority

| Priority | Market | Reason |
|----------|--------|--------|
| 1 | Over/Under 0.5 | Highest certainty, most stable |
| 2 | 1X2 (popular options) | Better liquidity |
| 3 | Over/Under 1.5 | Medium certainty |
| 4 | HT Over 0.5 | First half scoring rate stable |
| 5 | Over/Under 2.5 | Rich value but higher sample needed |
| 6 | BTTS | Higher uncertainty, use caution |
| 7 | Correct Score | Very low win rate, avoid |

---

## Risk Limits

| Limit Type | Value | Description |
|------------|-------|-------------|
| Per Match Max | 50 RON | Never exceed per single match |
| Per Market Max | 25 RON | Per specific market within match |
| Daily Max | 500 RON | Total daily exposure |
| Loss Limit | 100 RON | Stop if daily loss exceeds |
| Consecutive Loss Limit | 3 | Pause and review after 3 losses |

---

## Time-Based Rules

| Match Phase | Action |
|-------------|--------|
| Pre-match | Use CGMBet analysis only |
| 0-15 min | Sofascore momentum primary |
| 15-30 min | Cross-reference CGMBet |
| 30-60 min | Match Analyzer synthesis critical |
| 60-90 min | Reduced value, smaller stakes |
| Extra time | Avoid unless strong signal |

---

## Evolver Self-Optimization Rules

### Decision Quality Scoring

| Score | Criteria |
|-------|----------|
| 9-10 | Perfect: All agents agreed, high Value%, successful outcome |
| 7-8 | Good: 3+ agents agreed, reasonable Value%, successful |
| 5-6 | Neutral: Mixed signals, outcome neutral |
| 3-4 | Poor: 1-2 agents agreed, poor Value%, failed |
| 1-2 | Bad: No consensus, significant loss |

### Evolution Triggers

| Trigger | Action |
|---------|--------|
| 3 consecutive losses | Review and adjust thresholds |
| Win rate < 60% over 20 bets | Re-evaluate strategy |
| Value% consistently off | Recalibrate model |
| New league patterns | Add to CGMBet database |

### Memory Update Rules

- Log every decision regardless of outcome
- Tag with: market type, teams, odds, stake, result
- Monthly review of patterns
- Archive failed strategies, keep successful ones

---

## ⚠️ Critical Technical Rules (Hard-Won Lessons)

### CGMBet26 Database

| Rule | Value | Error |
|------|-------|-------|
| Completed match | StatusCode = `0` (NOT `1`) | Using `StatusCode=1` returns pending matches with 0-0 scores |
| Team IDs | TEXT (not integer) | SQL with `WHERE Id = 33001` fails, use `WHERE Id = '33001'` |
| Pending match | StatusCode = `'S'` | (string, not integer) |
| Cyprus league | ZERO data | Do not attempt Cyprus analysis |
| Tomorrow schedule | ~33 matches only | Most important matches not in CGM schedule |
| Team name lookup | Use `LIKE '%name%'` | Exact match often fails |

### Name Resolution

| Rule | Why |
|------|-----|
| Team-level aliases over match-level | Match-level fails when same team plays different opponent |
| Bilateral constraint (home+away same market) | Prevents Spartak Moscow → FK Spartak 错配 |
| Gender filter (no `(W)` skip women's BA) | Prevents Barcelona → Espanyol (W) 错配 |
| Alias threshold ≥ 0.75 | Below this, wrong match probability too high |
| Auto-learn ≥ 0.75 results | Continuous improvement, no manual maintenance needed |

### Bet Angel API

| Rule | Value |
|------|-------|
| placeBets endpoint | `/api/betting/v1.0/placeBets` (NOT `/api/bets/v1.0/`) |
| stake type field | `"type": "BACK"` or `"LAY"` (NOT `"betType"`) |
| stake value type | float, NOT string (`"stake": "5.0"` fails) |
| price field name | `back1.prc` / `lay1.prc` (NOT `back.price`) |
| getMarketPrices | Must call `displayMarket` first, else empty |
| applyCoupon | Only `"FT"` works; "Tomorrow", "FT Tomorrow" all FAIL |
| marketStartTime | NOT returned by `getMarkets` — cannot filter by date |
| Balance | Check with `getAccountAvailableToBetBalance` (NOT `/api/balance`) |

### Kelly Criterion

| Rule | Why |
|------|-----|
| Market odds MUST be higher than true odds | If market < true_odds (e.g. true_odds × 0.95), everything is SKIP |
| Estimate market as true_odds × 1.07 | 7% margin above fair value |
| Half Kelly cap always | Never bet full Kelly, max 50% of calculated stake |
| Minimum edge 1% | Below this, transaction costs eat the value |

### Poisson Model

| Rule | Why |
|------|-----|
| Lambda home | `0.6 * t1_home_xG_scored + 0.4 * t2_away_xG_conceded` |
| Lambda away | `0.6 * t2_away_xG_scored + 0.4 * t1_home_xG_conceded` |
| O2.5 probability | `65% * historical_over25_rate + 35% * poisson_over25` |
| BTTS probability | Weighted historical + away_scoring_rate_adjustment |
| True odds no margin | `1 / probability` (no bookmaker cut in true odds) |

### Known Problematic Matches

| Match | Issue | Workaround |
|-------|-------|-----------|
| Al Bataeh v Al Ain | Name clash with Saudi league | Verify league context |
| FC Barcelona (W) | Women's team name same as men's | Filter by `(W)` suffix |
| FK Spartak Subotica | Spartak name collides with Moscow | Use bilateral constraint |
| FC Iberia 1999 v FC Spaeri | Two matches same teams different leagues | League context needed |
| Narva Trans II | Reserve team, may not be in BA | Filter out `II`, `Reserves` |