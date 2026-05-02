# QClaw Skills Package

Bet Angel X2 automated trading system — Skills for football betting research and execution.

**Updated 2026-05-02**: Probability calibration fix — global Draw rate corrected from 31.85% (circular reasoning) to **26.2%** (CGMBet26, n=217,585).

## Skills

| Skill | Version | Description |
|-------|---------|-------------|
| etangel-x2 | v7.0.0 | Bet Angel API wrapper + X2 LAY strategy |
| ootball-council | v1.8 | Multi-agent analysis (CGMBet26 + Poisson + Kelly) |
| cgmbet26 | v1.1.0 | CGMBet26 database access |
| cgmbet26-strategies | v1.4.0 | Direct betting signal library |
| evolver | v1.1.0 | Self-improving decision system |
| guardian-automation | v1.1.0 | Guardian signal detection |
| match-analyzer | v1.3.0 | Match analysis workflow |
| openligadb | — | German football data API |

## Key Fix (2026-05-02)

**Circular reasoning removed**: 87 BACK Draw bets failed because market-implied probability was used as independent estimate. 
Correct approach: CGMBet26 historical data → true probability → compare vs Betfair market.

See [calibration data](https://github.com/zhujuncn/qclaw-skills) for league-specific rates.