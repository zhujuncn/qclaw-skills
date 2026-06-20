---
name: match-analyzer
version: 1.4.2
last_updated: 2026-05-07
status: beta
depends_on:
  - football-council  # NameResolver v3 shared infra
description: |
  Football match analysis and betting recommendation workflow. Integrates Sofascore live data with CGMBet26 statistical analysis to provide actionable betting recommendations.
  Use when user wants to analyze a football match, get betting suggestions, or combine live match data with statistical models for trading decisions.
---

# Match Analyzer v1.4.2 - Football Trading Workflow

## Overview

整合三大数据源进行足球分析：
1. **Sofascore API** - 实时比赛数据（比分、xG、射门、动量、事件）
2. **CGMBet26** - 统计分析数据库（历史模式、价值检测）
3. **Recommendation Engine** - 结构化投注建议与置信度评级

## 触发条件

- "分析这场比赛" / "analyze this match"
- "获取比赛信息" / "get match info"
- "给出下单建议" / "betting recommendations"
- "Sofascore + CGMBet26" 组合
- 任意有投注背景的足球分析

## 工作流

### Step 1: 识别比赛

从用户输入中提取：
- 队名（主队 vs 客队）
- 联赛/赛事
- 比赛时间/状态

若未提供 match ID，在 Sofascore 按队名搜索。

### Step 2: 获取 Sofascore 数据

```python
from curl_cffi import requests
session = requests.Session(impersonate='chrome')
base = 'https://api.sofascore.com/api/v1'

event = session.get(f'{base}/event/{match_id}', timeout=15).json()['event']
stats = session.get(f'{base}/event/{match_id}/statistics', timeout=15).json()
graph = session.get(f'{base}/event/{match_id}/graph', timeout=15).json()
incidents = session.get(f'{base}/event/{match_id}/incidents', timeout=15).json()
```

**关键数据点**：
- 当前比分、比赛时间
- xG（预期进球）
- 射门数（总/射正）
- 大机会创造/错失
- 动量图（最近 10-15 分钟）
- 最近事件（换人、红黄牌）
- 角球、控球率、危险进攻

### Step 3: 查询 CGMBet26 数据库

```python
import sqlite3
conn = sqlite3.connect(r'C:\Users\zhuju\AppData\Roaming\CGMBetSystem\CGMBetStats_v3.db')
# 查询相关历史模式
```

### Step 4: 分析与推荐

| 因素 | 权重 | 数据源 |
|------|------|--------|
| xG 趋势 | 高 | Sofascore |
| 动量 | 高 | Sofascore graph |
| 时间衰减 | 中 | 统计 |
| 换人 | 中 | Sofascore incidents |
| 历史模式 | 中 | CGMBet26 |

**推荐等级**：
- **STRONG** (5星) - 高置信、信号清晰
- **VALUE** (4星) - 风险/收益比好
- **CAUTION** (3星) - 条件性，关注触发器
- **AVOID** - 无明显优势

### Step 5: 输出格式

```markdown
## [Home] vs [Away] ([比分], [时间])

### 实时数据
| 指标 | 主队 | 客队 |
|------|------|------|
| xG | X.XX | X.XX |
| 射门 | X | X |
| 大机会 | X | X |
| 动量(10min) | +X | -X |

### 关键信号
1. [信号1及解释]
2. [信号2及解释]

### 推荐
| 优先级 | 市场 | 选项 | 置信度 | 理由 |
|--------|------|------|--------|------|
| 1 | [市场] | [选项] | 4星 | [原因] |
```

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

result = nr.find_match('Paris', 'Lille')
# -> {'ba_name': 'Paris St-G v Lille', 'score': 1.0}

# v3 新增：一句话下单
result = nr.find_and_bet(home='Bodo Glimt', away='Molde',
                         side='BACK', max_price=1.5, stake=1.0)
```

## ⭐ 自动下单模式 (2026-05-07 验证)

### 完整流程
```
1. CGMBet26 扫描候选 → _candidates.json
2. Name Resolver 匹配 BA 市场
3. getMarketPrices 获取 selection IDs（按位置：[0]=Home, [1]=Draw, [2]=Away）
4. placeBets 下单
5. 解析 result.bets[0].status == 'OK'
```

### 下单核心代码
```python
def place_bet(market_id: str, sel_id: str, bet_type: str, price: float, stake: float = 1.0):
    payload = {
        'marketId': market_id,
        'async': False,
        'globalSettings': {'accountId': 'DEFAULT'},
        'betsToPlace': [{
            'type': bet_type,        # 'BACK' or 'LAY'
            'price': price,
            'stake': stake,
            'selectionId': int(sel_id)  # 必须 int
        }]
    }
    r = requests.post('http://localhost:9000/api/betting/v1.0/placeBets', json=payload)
    bets = r.json().get('result', {}).get('bets', [])
    return bets[0].get('status') == 'OK' if bets else False
```

### 关键经验
- **Sel ID 非固定**：58805 不总是 Draw，必须按位置获取
- **响应路径**：`result.bets[0]` 不是 `result.results`
- **成功标志**：`bets[0].status == 'OK'` + `betRef` 存在

#### Name Resolver v3 关键改进
- **匹配策略 5 层**: CGM_SHORTEN -> DJYY_ALIASES (300+) -> team_aliases.json (578条) -> EXPANSIONS -> fuzzy
- **CGM 缩写硬编码**: az->Az Alkmaar, fh->Hafnarfjordur, ibv->IBV, shamrock->Shamrock
- **去变音**: Genclerbirligi, Brondby, Malmo
- **性别过滤**: 男足!=女足，二队默认过滤
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
| Flamengo | Flamengo | DJYY |
| Vasco da Gama | Vasco | DJYY |
| Duisburg | Duisburg | CGM |
| Cottbus | Cottbus | CGM |
| Rio Ave | Rio Ave | DJYY |
| Gil Vicente | Gil Vicente | DJYY |

## 策略性能统计（DJYY 762-3051 场验证）

| 策略 | Yield | Win Rate | Avg Odds |
|------|-------|----------|----------|
| Home Win A | 5.93% | 46.75% | 2.54 |
| Home Win B | 6.16% | 73.65% | 1.49 |
| Balance Draw | 13.58% | 31.85% | 3.57 |
| Away Win | 6.20% | 45.85% | 2.47 |
| DC X2 | 2.86% | 82.14% | 1.28 |
| Over 2.5 | 2.17% | 55.26% | 1.90 |
| Corners U9.5 | 5.89% | 53.65% | 2.01 |

## Scripts

- `scripts/fetch_sofascore.py` - 获取并解析 Sofascore 数据
- `scripts/query_cgmbet.py` - 查询 CGMBet26 数据库
- `scripts/generate_recommendation.py` - 生成格式化的推荐

## References

- `references/cgmbet_queries.md` - CGMBet26 查询模式
- `references/betting_markets.md` - 市场特定分析指南

## Evolver 学习记录（2026-04-24）

### Poisson xG 混合模型

```python
# Step 1: xG 估算
lambda_home = 0.6 * h_xg_scored + 0.4 * a_xg_conceded
lambda_away = 0.6 * a_xg_scored + 0.4 * h_xg_conceded

# Step 2: Poisson 概率网格 (6x6)
p_hw = sum(poisson_prob(lh, la, i, j) ... if i > j)
p_draw = sum(poisson_prob(lh, la, i, i) ...)
p_aw = sum(poisson_prob(lh, la, i, j) ... if i < j)

# Step 3: 混合模型 (65% Poisson + 35% 形态)
est_hw = p_hw * 0.65 + h_win_pct/100 * 0.35
# Normalize
```

### Value 筛选标准（实测验证）
| Value | 等级 | 动作 |
|-------|------|------|
| >= 20% | BLUE++ | KEEP，标准仓位 |
| 15-20% | BLUE+ | KEEP |
| 10-15% | BLUE | KEEP |
| 5-10% | BLUE- | MARGINAL |
| < 5% | GRAY/PINK | CANCEL |
| Kelly < 0 | - | 立即取消 |
