---
name: football-trading-advisor
description: Unified football betting-advice workflow that combines CGMBet26 research, Bet Angel API market data, NameResolver matching, value/Kelly risk rules, and optional live-monitoring context. Use when the user asks for 足球下注建议, Bet Angel 下单建议, CGMBet26 价值扫描, football trading recommendations, daily picks, value bets, Lay/Back advice, or a consolidated football betting pipeline. Default behavior is advice only; never place bets unless the user explicitly asks and confirms execution.
---

# Football Trading Advisor

Use this skill as the single entrypoint for football betting recommendations. It consolidates the local football skills into one workflow:

`CGMBet26 database -> Bet Angel API -> value model -> risk gate -> recommendation report`

Default mode is **advice only**. Do not place bets by default.

For the local qclaw workflow, there is also a separate **force test probe** mode for manual testing. This mode is not the default strategy path. It is only for explicit user-authorized `1 RON` test orders that must still record the full decision trace even when normal gates fail.

## Core Workflow

1. Load candidates from CGMBet26:
   - Read `C:\Users\zhuju\AppData\Roaming\CGMBetSystem\CGMBetStats_v3.db`.
   - Query `Matches`, `Teams`, `Leagues`, `Odds`, and `Ratings`.
   - Prefer upcoming matches for the requested date range.
2. Pull Bet Angel market context when available:
   - `POST http://localhost:9000/api/markets/v1.0/getBalance`
   - `POST http://localhost:9000/api/markets/v1.0/getMarkets`
   - `POST http://localhost:9000/api/markets/v1.0/getMarketPrices`
3. Match teams conservatively:
   - Use Betfair/Bet Angel market display names as canonical names.
   - Build/update `references/betfair_name_index.json` from qclaw/Codex alias assets with `scripts/name_matcher.py`.
   - Map CGMBet26/Sofascore/DJYY/FlashScore names into Betfair canonical names before fuzzy matching.
   - Reject low-confidence matches.
4. Compute recommendation:
   - Use CGMBet26 ratings and odds as independent research inputs.
   - Estimate true probabilities from ELO/Form plus calibrated draw baseline.
   - Compare true probability with market implied probability.
   - Apply value and Kelly gates.
5. Output a report:
   - Recommended action: `BACK`, `LAY`, `WATCH`, or `SKIP`.
   - Selection, odds, value %, Kelly fraction, stake suggestion, confidence tier.
   - Clear reasons and risk flags.

## Daily Execution Guidance

Use this as the default daily betting instruction for the qclaw workflow:

1. Refresh the Betfair-first name index before scanning.
2. Run the full gate evaluation first; do not start from order placement.
3. Separate bets into three buckets:
   - `official`: passes the full hard-gate set.
   - `probe_failed_gate`: fails strategy gates but still has a safe market/selection match.
   - `skip`: no executable market, no selectionId, stale/unsafe price, or API uncertainty.
4. For `official` bets, prefer a staged execution ladder:
   - place a small probe-sized opener first,
   - confirm Bet Angel accepts it and that matching behavior is sane,
   - only then scale to the planned target stake/liability.
5. For `probe_failed_gate` bets, keep them separate from official strategy bets:
   - default stake `1 RON`,
   - record the original blocked reasons,
   - never let probe results alone relax the official gate set.
6. After the run, review the action-chain artifacts, not just the summary report:
   - `placebets`
   - `modifybets`
   - `resize`
   - `final status`
7. Treat settlement verification as part of execution quality:
   - if result/P&L cannot be verified, downgrade the next day to advice-first or reduced budget mode,
   - do not use unverified profits to increase stake.

Short version:

- Official bets: small probe -> confirm match/acceptance -> scale.
- Probe bets: keep for record and review, never as a substitute for official gates.
- Review: trust the action-chain JSON files first, then the summary report.
- Next-day bankroll: require verified settlement before upgrading size.

## Run The Advisor

Use the bundled script:

```powershell
$env:PYTHONIOENCODING='utf-8'
python scripts/advisor.py --date 2026-06-16 --days 2 --ba --max 20
```

Refresh the Betfair-first name index before daily scans or after Bet Angel markets change:

```powershell
python scripts/name_matcher.py
```

Useful modes:

```powershell
# Local CGMBet26-only recommendations
python scripts/advisor.py --date 2026-06-16 --days 2 --max 20

# Include Bet Angel balance and market matching
python scripts/advisor.py --date 2026-06-16 --days 2 --ba --max 20

# JSON output for automation
python scripts/advisor.py --date 2026-06-16 --days 2 --ba --json
```

## Risk Rules

Read `references/rules.md` for the full rulebook. The key gates are:

- Value `< 5%`: cancel.
- Value `5%-10%`: watch or half/quarter stake only.
- Value `>= 10%`: candidate keep.
- Kelly `< 0`: cancel.
- Odds `< 2.0`: default cancel for pre-match BACK bets.
- Odds `2.0-8.0`: preferred trading range.
- Odds `8.0-10.0`: reduce stake.
- Odds `> 10.0`: skip unless explicitly approved as a tiny speculative position.
- One bet per match.
- Batch exposure should stay under 10% of bankroll; prefer 3%-5% while testing.
- Use global draw baseline `26.2%` unless a league-calibrated rate is available.

## Execution Safety

Never place a bet from this skill unless all are true:

- The user explicitly asks to place bets.
- The recommendation has passed all risk gates.
- The Bet Angel market and selection are matched with high confidence.
- `selectionId` is converted to `int`.
- Payload uses `type: "BACK"` or `type: "LAY"`; never `betType`.
- Stake and price are numeric floats.
- The user confirms the final bet list.

Global Bet Angel live-execution switch for this workspace:

- Use `.\ba.ps1 AI开` to keep monitoring on and allow AI automatic live execution through Bet Angel when all gates pass.
- Use `.\ba.ps1 AI关` to keep monitoring on but disable AI automatic live execution and return to dry-run monitoring.
- Treat `AI开` and `AI关` as the global controls for automatic Bet Angel betting, reduce, close, and cash-out across all qclaw football skills.
- Do not use lower-level `ai-on`, `ai-off`, or direct `--execute` as the daily interface unless debugging the wrapper itself.

Execution discipline for this workspace:

- Do not jump straight from model output to full-size stake when a staged entry is possible.
- Do not treat a clean-looking summary report as authoritative if the per-action Bet Angel JSON chain disagrees.
- Do not let probe wins justify relaxing official thresholds without a larger verified sample.
- Do not increase the next day's budget unless settlement and P/L are verified.

## Force Test Probe Mode

Use this only when the user explicitly says they want to:

- force a `1 RON` test order,
- keep the decision trace for review,
- and allow execution to continue even when normal strategy gates fail.

Behavior:

- Normal gate evaluation must still run first.
- The output must preserve the full gate trace and the original `failure_reasons`.
- Forced execution should be labeled `force_test_probe`, not mixed into official bets.
- Default stake is `1 RON`.
- This mode may bypass strategy gates such as `tier`, `ba_match_score`, `raw_value_pct`, `odds_range`, or `risk_flags` for logging/testing purposes.
- It must still require basic execution primitives:
  - `marketId`
  - `selectionId`
  - explicit `BACK` or `LAY`
  - executable price
  - market status `OPEN`
  - healthy Bet Angel session
- If Bet Angel returns session/API errors, stop subsequent forced test orders and record the API failure reason.

Implementation note for this workspace:

- The governance runner reads `work/football-trading-system/force_test_probe.json`.
- Set `"enabled": true` to activate the mode.
- The runner records both the standard blocked reasons and the force-allow reason in the JSON output.

The current bundled `advisor.py` is advice-only and does not send `placeBets`.

## Existing Skill Roles

For the full current football skill map and routing rules, read `references/football-skill-map.md` when the user asks which football skills exist, asks to consolidate football workflows, or asks which skill should handle a task.

- `cgmbet26`: database, historical research, probabilities, P-value context.
- `cgmbet26-strategies`: value thresholds, Kelly, strategy tiers.
- `betangel-x2`: Bet Angel API execution format and market price access.
- `betangel-api`: low-level Bet Angel API requests, endpoint debugging, market/order reads, and GUI/API mismatch diagnosis.
- `betangel-live-order-engine`: live heartbeat monitoring, existing exposure management, stop-loss/profit-lock, reduce, supplement, cash out, and green-up under hard gates.
- `football-council`: NameResolver, multi-source arbitration.
- `match-analyzer` and `sofascore`: live xG/stat context.
- `guardian-automation` and `football-match-monitor`: goal detection and cash-out monitoring.
- `form-elo-divergence`: avoid favorites when Form contradicts ELO.
- `evolver`: post-trade review and parameter improvement, not direct execution.
