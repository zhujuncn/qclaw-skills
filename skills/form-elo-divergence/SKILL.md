# Form-ELO Divergence Detection Skill

## Description

Detects Form-ELO divergence in football matches using CGMBet26 database. When ELO rating contradicts recent Form, it signals potential value betting opportunities or warns about risky positions.

**Keywords**: form-elo, divergence, value betting, football analysis, CGMBet26, ELO rating, form rating

## Installation

```bash
# Copy skill to workspace
copy %USERPROFILE%\.qclaw\skills\form-elo-divergence\* %USERPROFILE%\.qclaw\workspace\betangel\

# Requires CGMBet26 database at:
# C:\Users\<user>\AppData\Roaming\CGMBetSystem\CGMBetStats_v3.db
```

## Quick Start

```bash
# Scan for today's divergences
python betangel/divergence_scanner.py --date 2026-04-21 --days 1

# Full pipeline with divergence awareness
python betangel/pipeline_divergence.py --date 2026-04-21 --stake 2

# Monitor divergent matches in-play
python betangel/inplay_monitor.py --date 2026-04-21 --monitor --interval 120
```

## What is Form-ELO Divergence?

| Metric | Meaning | Timeframe |
|--------|---------|-----------|
| **ELO** | Long-term team strength | Years of data |
| **Form** | Recent performance | Last 5-6 matches |

**Divergence** = ELO says Team A should win, but Form says Team B is playing better recently.

### Why It Matters

Historical data shows ~30% of divergent matches produce unexpected results. This creates:
- **Value opportunities** (back the Form team when ELO overrates the favorite)
- **Risk warnings** (avoid LAY on ELO favorites with poor Form)

## Tier Classification

| Tier | Criteria | Action |
|------|----------|--------|
| **TIER 1** | \|ELO\|>100, \|Form\|>10, opposite | Skip LAY favorite, add reverse bets, enable monitoring |
| **TIER 2** | \|ELO\|>50, \|Form\|>5, opposite | Reduce stake 50%, flag for monitoring |
| **TIER 3** | \|ELO\|>50, \|Form\|>3, opposite | Log only, light monitoring |

## Files

- `divergence_scanner.py` — Core scanner, outputs JSON reports
- `inplay_monitor.py` — Live monitoring with Cash Out triggers
- `pipeline_divergence.py` — Integrated pipeline with Bet Angel X2

## Output Format

```json
{
  "scan_time": "2026-04-20T21:15:18",
  "target_date": "2026-04-20",
  "total_matches": 57,
  "divergences": [
    {
      "match_id": "20260420001",
      "home": "La Coruna",
      "away": "Mirandes",
      "elo_diff": 154,
      "form_diff": -11,
      "tier": 1,
      "recommendation": {
        "confidence": 1,
        "bets": [...],
        "monitoring": {"flag": true, "cash_out": true}
      }
    }
  ]
}
```

## Integration with Bet Angel X2

The skill automatically:
1. Loads existing bets from result files
2. Flags divergent matches in your portfolio
3. Suggests Cash Out when conditions met
4. Generates adjusted stake recommendations

## Dependencies

- Python 3.8+
- CGMBet26 with SQLite database
- Bet Angel X2 Framework (optional, for live monitoring)

## License

MIT — Use at your own risk for betting analysis.

---
depends_on:
  - football-council  # NameResolver v3 shared infra


### DJYY → BA 名称匹配

**Name Resolver v3** 是所有足球技能的统一底层组件，位于：
```
C:/Users/zhuju/.qclaw/skills/football-council/scripts/name_resolver.py
别名库: C:/Users/zhuju/.qclaw/skills/football-council/data/team_aliases.json (578条)
```

所有技能统一使用以下导入方式：
```python
import sys
sys.path.insert(0, 'C:/Users/zhuju/.qclaw/skills/football-council/scripts')
from name_resolver import NameResolver

nr = NameResolver()
nr.register_ba_markets(ba_markets_dict)  # {market_name: market_id}

result = nr.find_match('Bayern Munchen', 'Mainz 05')
# → {'ba_name': 'Bayern Munich v Mainz 05', 'score': 0.75, 'method': 'fuzzy'}

# v3 新增：一句话下单
result = nr.find_and_bet(home='Bodo Glimt', away='Molde',
                         side='BACK', max_price=1.5, stake=1.0)
```

#### Name Resolver v3 关键改进
- **匹配策略 5 层**: CGM_SHORTEN → DJYY_ALIASES (300+) → team_aliases.json (578条) → EXPANSIONS → fuzzy
- **CGM 缩写硬编码**: az→Az Alkmaar, fh→Hafnarfjordur, ibv→IBV, shamrock→Shamrock
- **去变音**: Genclerbirligi, Brondby, Malmo
- **性别过滤**: 男足≠女足，二队默认过滤
- **BA API 端点**: /api/betting/v1.0/placeBets | Price: back1.prc / lay1.prc
- **selectionId**: 必须是 INT，不是字符串

#### 关键别名映射（2026-05-03 验证）
| 外部名 | BA 队名 | 来源 |
|--------|---------|------|
| Paris | Paris St-G | DJYY |
| Koln | FC Koln | DJYY |
| AZ | Az Alkmaar | CGM |
| FH | Hafnarfjordur | CGM |
| Hearts | Heart of Midlothian | DJYY |
| Bodo Glimt | Bodo Glimt | DJYY |
| Shamrock | Shamrock | CGM |
| IBV | IBV | CGM |
| Flamengo | Flamengo | DJYY |
| Vasco da Gama | Vasco | DJYY |
| Duisburg | Duisburg | CGM |
| Cottbus | Cottbus | CGM |
| Rio Ave | Rio Ave | DJYY |
| Gil Vicente | Gil Vicente | DJYY |
| FC Twente | Twente | CGM |
| Mjallby | Mjallby | CGM |
| Brommapojkarna | Brommapojkarna | CGM |
## Evolver 学习记录 (2026-04-24)

### Value 阈值对齐

Form-ELO 背离检测的信号应与 Value 筛选阈值对齐：

| Form-ELO 背离 | Value 估算 | 综合动作 |
|-------------|-----------|----------|
| 强背离 + Value ≥ 20% | BLUE++ | 最高置信，标准仓位 |
| 强背离 + Value 10-20% | BLUE/BLUE+ | KEEP |
| 强背离 + Value 5-10% | BLUE- | MARGINAL |
| 强背离 + Value < 5% | GRAY | 取消（背离不足以覆盖赔率劣势）|
| 弱背离 + 任意 Value | — | 不下注（无明确方向）|

### Draw 信号

当双方平局率均 > 60% 时，Draw 信号极强 (Value 40-70%)：
- ELO 可能高估强队 → Form 显示大量平局 → **背离即信号**
- 适用联赛: 挪威/瑞典/爱尔兰/苏格兰低级别
- 对手样本 < 10 场时不可靠

### 关键规则

- 赔率 < 2.0 一律取消 (Kelly 必为负)
- 每场限 1 笔，单批次 ≤ 10% 银行余额
- Poisson xG (65%) + Form (35%) 混合模型优于纯形态估算
