# Evolver Self-Improvement Report
## Session: 2026-05-02 | Focus: Balance Draw Strategy (BACK Draw)

---

## 📊 DATA SNAPSHOT

**87 BACK Draw bets placed today:**
- Stake: 165 RON total (Batch 1: 51 RON + Batch 2: 114 RON)
- Odds range: 3.50x ~ 8.00x
- EV range: +11.5% ~ +154.8%
- STRONG: 58 bets | VALUE: 29 bets
- All 87 succeeded (100% execution rate)
- BetRefs all "N/A" (live market matching)

**Historical reference:**
- X2 Strategy (LAY Draw): 82.14% win rate, avg odds 1.28 → used HR=31.85%
- Current BACK Draw uses same HR but flipped direction

---

## 🔍 CRITICAL FINDINGS

### Finding 1: HR=31.85% — The Hidden Assumption

The scan script uses:
```
EV% = market_odds × HR − 1   where HR = 0.3185
```

This is equivalent to saying: **"I believe every draw has exactly 31.85% probability, regardless of the match."**

**Breakeven analysis:**
- Threshold odds: 1/0.3185 = **3.139x**
- Below 3.139x → LAY Draw has value (historically what was done)
- Above 3.139x → BACK Draw has value (currently doing)
- At 3.139x → breakeven

**The circular logic problem:**
If the model uses market odds to derive its probability estimate, then:
```
true_odds = market_odds / (1 + EV/100)
1/HR = market_odds / (1 + EV/100)  →  HR = (1 + EV/100) / market_odds
```

Test: @4.0, EV=27.4% → HR = 1.274/4.0 = **31.85%** ✓ (matches perfectly)

This confirms: **HR=31.85% is derived from market odds + EV formula, not from external data.**
The "value" is simply: market odds are above 3.139x, so we back draws because the market prices them lower than the model's blanket assumption.

**Verdict:** This works as long as the market systematically underprices draws above 3.139x. But it's a market timing strategy, not a true probability estimate.

---

### Finding 2: The Kelly Loop Problem

Previous sessions revealed: calculating Kelly from market odds → edge ≈ 0 (circular).

**Correct approach:**
- External probability source: CGMBet26 / Poisson xG
- Compare external_prob vs market_prob (1/market_odds)
- Kelly = (market_odds × external_prob − 1) / (market_odds − 1) × 0.5

**Current gap:** CGMBet26 DB has no league-level foreign key. Can't get per-league draw rates.
Only team-level analysis available.

---

### Finding 3: bet_ref = "N/A" — Why Live Matching Fails

All 87 bets show `"bet_ref": "N/A"`. This means:
- The script reads the API response incorrectly
- `betRef` field exists inside `result.bets[0].betRef`
- But the script writes `"bet_ref": "N/A"` instead of extracting the real value

**Root cause:** `x2_framework.py` placeBet response parser writes "N/A" when the response is parsed as a string rather than JSON. Need to verify the actual response structure.

---

### Finding 4: getMarkets = 0 (Guardian GUI Issue)

- Guardian UI must display markets for `getMarkets` to return names
- Without this, signals have no match names, only market IDs
- Can never match the 87 bet market IDs back to actual matches

**Workaround:** Use `getMarketPrices` (returns prices but no names), or maintain a market ID → match name lookup table from a different data source.

---

### Finding 5: getMarketPrices Return Path Changed

**Old (broken):** `response['markets'][...]`
**New (correct):** `response['result']['markets'][...]`

This affected every scan script. All need updating.

---

### Finding 6: Cron Encoding Bug

PowerShell heredoc with Chinese characters causes `cp1252` UnicodeEncodeError.
Fix: Set `$env:PYTHONIOENCODING='utf-8'` before Python invocation.

---

## 🧬 EVOLUTION RECOMMENDATIONS

### Recommendation 1: Unified Draw Strategy (HIGH PRIORITY)

**Problem:** LAY Draw and BACK Draw are two separate scans that never run together.

**Solution:** Compute per-match draw probability from Poisson xG:
```python
# Get external draw probability
draw_prob = poisson_model.get_draw_prob(home_team, away_team)

# Market implied probability
market_prob = 1 / market_odds

# Compare
if draw_prob > market_prob:
    action = "BACK Draw"  # Model thinks draw is more likely than market
    edge = (draw_prob - market_prob) / market_prob * 100
elif draw_prob < market_prob:
    action = "LAY Draw"   # Model thinks draw is less likely than market
    edge = (market_prob - draw_prob) / draw_prob * 100
else:
    action = "SKIP"

# Kelly sizing
kelly = (market_odds * draw_prob - 1) / (market_odds - 1) * 0.5
stake = balance * kelly * 0.5  # Half Kelly cap
```

This eliminates the blanket HR=31.85% assumption and makes every bet match-specific.

### Recommendation 2: Add CGMBet26 Team Form to BACK Draw (MEDIUM PRIORITY)

Even without full Poisson, incorporate:
- Team's recent draw rate (last 10 home matches for home team, last 10 away for away)
- H2H draw rate between these two teams
- League average draw rate (requires scraping from another source)

### Recommendation 3: Fix Bet Ref Extraction (HIGH PRIORITY)

The bet_ref = "N/A" issue means we have no way to track/cancel these bets.

**Fix:**
```python
# In place_bet response handling:
resp = requests.post(f'{BASE}/api/betting/v1.0/placeBets', json=payload)
data = resp.json()

# New format (confirmed May 2):
if data.get('status') == 'OK':
    bet_ref = data.get('result', {}).get('bets', [{}])[0].get('betRef', '')
    price_matched = data.get('result', {}).get('bets', [{}])[0].get('priceMatched', 0)
    stake_matched = data.get('result', {}).get('bets', [{}])[0].get('stakeMatched', 0)
```

### Recommendation 4: Market ID → Match Name Lookup (MEDIUM PRIORITY)

Without Guardian names, we need an alternative. Options:
1. Use Sofascore API to search by time window (all 87 bets are from May 2)
2. Use CGMBet26 upcoming matches + match time to cross-reference
3. Maintain a daily cache of (market_id, market_name, start_time) from before markets close

### Recommendation 5: Add Result Tracking (HIGH PRIORITY)

After today's 87 bets settle:
- Check if each market is now CLOSED in getMarketPrices
- Fetch final prices to determine outcomes
- Record outcomes to `council_history.json` for Evolver learning

Script plan:
```python
# After matches complete (~3 hours):
for bet in bet_log:
    resp = getMarketPrices(market_id)
    market = resp['result']['markets'][0]
    if market['status'] == 'CLOSED':
        # Draw wins if draw selection has no back price (fully settled)
        outcome = determine_outcome(market)
        record_decision(bet, outcome)
```

---

## 📋 EVOLUTION PRIORITY STACK

| # | Action | Impact | Effort | Status |
|---|--------|--------|--------|--------|
| 1 | Fix bet_ref extraction in x2_framework.py | Trackable bets | Low | TODO |
| 2 | Update getMarketPrices path to `result.markets` | Accurate scanning | Low | TODO |
| 3 | Build Poisson xG unified draw strategy | Per-match probability | Medium | TODO |
| 4 | Add market_id → match name lookup cache | Meaningful logging | Medium | TODO |
| 5 | Build result tracking for settled bets | Evolver learning | Medium | TODO |
| 6 | Cron encoding fix with PYTHONIOENCODING | Reliability | Low | DONE |
| 7 | Update football-council SKILL.md | Documentation | Low | IN PROGRESS |

---

## 🔄 PROGRESS LOG

| Date | Action | Status |
|------|--------|--------|
| 2026-04-24 | Evolver initialized (73-bet value analysis) | DONE |
| 2026-04-25 | DJYY extraction + Name Resolver v2 | DONE |
| 2026-04-27 | CGMBet26 batch execution (86/86 success) | DONE |
| 2026-04-30 | CGMBet26 35-bet execution | DONE |
| 2026-05-02 | 87 BACK Draw bets (first major BACK Draw run) | DONE |
| 2026-05-02 | Evolver iteration (this session) | IN PROGRESS |

---

*Generated by Evolver | 2026-05-02 22:20 Bucharest*