---
name: cgmbet26
version: 1.1.2
last_updated: 2026-05-07
status: active
depends_on:
  - football-council  # NameResolver v3 shared infra
description: |
  CGMBet26 System 足球数据分析软件知识库。当用户提到 CGMBet、cgmbet、足球数据分析、赛前研究、泊松模型、ELO评分、价值投注检测、进球统计、比分演进、A.G.S.、Rating V、Rating M、Advanced Poisson、Suggestions AI、足球统计回测、P-value 策略验证时使用此技能。支持：赛前价值扫描、赛中条件概率分析、策略回测与统计显著性检验、xG公式优化、与Bet Angel Pro X2流水线协同。
---

# CGMBet26 System v1.1.2 — 足球数据分析技能

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
## ⚠️ 概率校准数据（2026-05-02）

全局 Draw 率 = **26.2%**（来自 CGMBet26 数据库 217,585 场）。
校准文件：`C:\Users\zhuju\.self-improving\calibration\league_calibration.json`


## 系统定位

CGMBet26 v2.16 是 Windows 桌面足球数据研究引擎，核心定位：**数据研究 + 价值发现**（不直接下单）。

许可证层级：Free / VIP / VIP Plus（自定义公式列+全量导出需 VIP Plus）

## 核心模块速查

| 模块 | 定位 | 关键产出 | 详情 |
|------|------|---------|------|
| Tables | 联赛积分榜+ELO走势 | 状态趋势判断 | [references/tables.md](references/tables.md) |
| H2H | 交锋对比+进球时段 | 主客优劣势 | [references/h2h.md](references/h2h.md) |
| Statistics | 跨联赛统计+连续模式 | 趋势热点/回归信号 | [references/statistics.md](references/statistics.md) |
| Upcoming | 27自定义列+Alerts | 比赛筛选核心工作区 | [references/upcoming.md](references/upcoming.md) |
| Suggestions (AI) | 自动预测+价值检测 | 高置信+有Value的比赛 | [references/suggestions.md](references/suggestions.md) |
| A.G.S. | 深度历史研究+赛中 | Yield+P-value策略验证 | [references/ags.md](references/ags.md) |
| Goals Statistics | 分钟概率网格 | 赛中实时概率 | [references/goals-stats.md](references/goals-stats.md) |
| Score Evolution | 比分演进树 | 最可能比分路径 | [references/score-evolution.md](references/score-evolution.md) |
| Poisson | 单场泊松计算器 | xG→概率+赔率 | [references/poisson.md](references/poisson.md) |
| Advanced Poisson | 批量泊松+公式回测 | xG公式Yield优化 | [references/advanced-poisson.md](references/advanced-poisson.md) |
| Rating V | 经验频率概率+价值 | Back/Lay Value信号 | [references/rating-v.md](references/rating-v.md) |
| Rating M | 单场条件分析 | 赛中场景概率 | [references/rating-m.md](references/rating-m.md) |
| AI Export | 数据导出给外部AI | ChatGPT综合分析 | [references/ai-export.md](references/ai-export.md) |
| Calculators | 9个投注计算器 | P-value/Kelly/套利等 | [references/calculators.md](references/calculators.md) |

## 工作流

### 赛前研究（推荐顺序）

```
1. Upcoming → 筛选今日比赛（27自定义列 + Alerts 自动触发）
2. Suggestions (AI) → 快速扫价值（Strong ≥70% + Value filter ON）
3. Statistics → H2H + 连续趋势（正向/负向连续模式）
4. A.G.S. → 深度回测（Yield% + P-value < 5% 验证显著性）
5. Rating V / Advanced Poisson → 概率计算 + 价值确认
6. Calculators → Kelly 算最优投注额
```

### 赛中研究

```
1. Goals Statistics → 实时分钟概率（ELO匹配历史）
2. Score Evolution → 比分演进可视化（最可能路径）
3. Rating M → 条件分析（若X比分于Y分钟 → Z市场概率）
4. A.G.S. Live Game → 自动刷新赛中查询（15/30/60秒）
```

## 与 Bet Angel Pro X2 协同

| 维度 | CGMBet26 | Bet Angel Pro X2 |
|------|----------|-----------------|
| 赛前价值发现 | **核心强项** | 需手动 |
| 统计显著性检验 | **P-value 内置** | 无 |
| Yield回测 | **A.G.S./Adv.Poisson** | 无 |
| 自动下注 | 不支持 | **核心功能** |
| 赛中实时监控 | Goals Stats/Rating M | Guardian |

**协同模式：CGMBet26 做研究 + 价值发现 → Bet Angel 做执行**

### DJYY ExchangeBets 交叉验证

DJYY 提供每日 7 个策略 picks，可作为 CGMBet26 分析的第三方验证：
- **DJYY Balance Draw** 命中 + CGMBet26 A.G.S. Draw Yield > 5% → 极高置信 Draw
- **DJYY Home Win B** 命中 + CGMBet26 Suggestions Home ≥ 70% → 高置信 Home
- **多策略交集**: DJYY + CGMBet26 + Poisson 三方一致 = T1 级信号

DJYY 提取: xbrowser `eval focus(button[N])` + `press Enter`
按钮索引: HW-A=3, HW-B=5, BD=7, AW=9, X2=11, O2.5=13, CU9.5=15

**DJYY → BA 名称匹配** (匹配率 93.8%):
```python
from name_resolver import NameResolver
nr = NameResolver()
nr.register_ba_markets(ba_markets_dict)
result = nr.find_match("Bayern Munchen", "Mainz 05")
```
关键映射: Paris→PSG, Koln→FC Koln, Hearts→Heart of Midlothian, FK Bodo-Glimt→Bodo/Glimt

### X2 LAY 主队策略增强

1. **A.G.S. 验证策略**：设联赛+赛季范围+ELO过滤 → 查看 Home Win 的 Yield% + P-value
2. **Suggestions 快速扫描**：Strong ≥70% + Value filter → 找 Home Win 高置信+有Value的比赛
3. **Rating V 二次确认**：Highlight %≥70% + Lay Value -70%~-15% → 粉格=支持LAY
4. **Advanced Poisson 优化xG**：切换公式变体 → 对比 Home Win Yield%

## 概念速查

- **Value = (O(R)/O(C)-1) x 100**：O(R)=实际赔率，O(C)=公平赔率。正=Back价值，负=Lay价值
- **P-value < 5%**：统计显著，策略非运气；>10% 不显著
- **Suggestions 价值检测**：统计概率比赔率隐含概率高 ≥10% 才标绿
- **ELO 容差**：±75（默认），范围越窄越精确但样本越小
- **Dixon-Coles 调整**：修正泊松低估低分平局(0-0, 1-0, 0-1, 1-1)的倾向
- **Kelly 公式**：始终用 Half(0.5) 或 Quarter(0.25) Kelly，Full Kelly 波动过大
- **BACK↔LAY 赔率换算**：LAY price = BACK price + 1

## 模块间数据流

```
Upcoming ──→ Suggestions ──→ Statistics/H2H ──→ A.G.S. ──→ Rating V/Adv.Poisson ──→ Calculators
                  │                                    │
                  ↓                                    ↓
           Goals Statistics ←── Score Evolution ←── Rating M ←── A.G.S. Live Game
```

右键菜单快速跳转：Upcoming → H2H / Tables / Poisson / Rating M / Goals / Score Evolution

---

## Evolver 学习记录 (2026-04-24)

### Value 筛选阈值 (73场实单验证)

| Value | 信号 | 动作 |
|-------|------|------|
| ≥20% | BLUE++ | 强信号，标准仓位 |
| 15-20% | BLUE+ | 强信号，KEEP |
| 10-15% | BLUE | 标准信号，KEEP |
| 5-10% | BLUE- | 弱信号，MARGINAL |
| -5%~5% | GRAY | 无价值，CANCEL |
| <-15% | PINK++ | 强负价值，立即取消 |

### Poisson xG 混合模型 (经验证优于纯形态)

```python
lambda_home = 0.6 * h_xg_scored + 0.4 * a_xg_conceded
lambda_away = 0.6 * a_xg_scored + 0.4 * h_xg_conceded
nest = Poisson(65%) + Form(35%)
```

### Draw 信号 (高价值发现)

当双方 15 场平局率均 > 60% → Draw Value 40-70%

适用联赛: 挪威/瑞典/爱尔兰/苏格兰低级别
注意: 对手样本 < 10 场时不可靠

### 关键规则

- 赔率 < 2.0 的 BACK 注 Kelly 必为负 → 一律取消
- 赔率 > 10.0 属彩票注 → 减仓
- 每场限 1 笔，单批次 ≤ 10% 银行余额
