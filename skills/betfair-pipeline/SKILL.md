---
name: djyy-betfair-pipeline
version: 1.1.1
last_updated: 2026-05-03
status: active
depends_on:
  - football-council  # NameResolver v3 shared infra
description: |
  DJYY ExchangeBets 每日 05:00 (Bucharest) 自动执行流水线。
  从 DJYY 提取 7 个策略 picks → CGMBet26 统计验证 → Bet Angel Guardian 市场扫描 → 赔率过滤 → 自动 LAY 下注 → 进球监控与 Cash Out。
  当用户提到 DJYY、自动下单、每日博彩流水线、Betfair Exchange 自动交易时触发。
---

# DJYY Betfair Pipeline v1.1.1

## 系统架构

```
DJYY ExchangeBets (xbrowser)
    ↓ xbrowser eval(focus)+Enter 提取
每日 Picks（7 策略）
    ↓
CGMBet26 统计分析（CGMBetStats_v3.db）
    ↓ 赔率过滤 + Value 验证
Bet Angel Guardian 市场扫描（/api/markets/v1.0/getMarkets）
    ↓
Name Resolver v3 队名匹配（足球统一底层组件）
    ↓
自动 LAY/BACK 下注（/api/betting/v1.0/placeBets）
    ↓
进球监控 + Cash Out 决策
```

## 定时执行

**每日 05:00 Bucharest (UTC+3) 自动执行：**
- DJYY 每日 04:00 前更新当天 picks
- pipeline 在 DJYY 更新后 1 小时执行
- 使用 `modelroute` 模型（Cron task 执行）

## DJYY 数据提取

### 唯一有效方法（2026-04-25 验证）

DJYY 使用 Radix UI Popover，CDP mouse click 和 JS `.click()` 均无法触发。

```powershell
# 关键：focus + Enter
"$NODE" ...xb.cjs run --browser cft eval "(function(){document.querySelectorAll('button')[N].focus();return 'ok'})()"
"$NODE" ...xb.cjs run --browser cft press Enter
```

### 按钮 DOM 索引
| 策略 | DOM 索引 | Yield | WR |
|------|---------|-------|-----|
| Home Win A | 3 | 5.93% | 46.75% |
| Home Win B | 5 | 6.16% | 73.65% |
| Balance Draw | 7 | 13.58% | 31.85% |
| Away Win | 9 | 6.20% | 45.85% |
| DC X2 | 11 | 2.86% | 82.14% |
| Over 2.5 | 13 | 2.17% | 55.26% |
| Corners U9.5 | 15 | 5.89% | 53.65% |

## CGMBet26 统计分析

```python
import sqlite3
conn = sqlite3.connect(r'C:\Users\zhuju\AppData\Roaming\CGMBetSystem\CGMBetStats_v3.db')

# 查询明日比赛
cur.execute("""
    SELECT MatchId, HomeTeamId, AwayTeamId, Date, Time
    FROM Matches
    WHERE Date = ?
    ORDER BY Time
""", (tomorrow_str,))
```

### Value 计算（CGMBet26 → Betfair Exchange）
```python
true_odds = cgmbet_prob_to_odds(home_pct, draw_pct, away_pct)
exchange_odds = get_exchange_back_price(home_name)

# Value% = (1/true_odds - 1/market_back) / (1/market_back) * 100
value_pct = (1/true_odds - 1/exchange_odds) / (1/exchange_odds) * 100

if value_pct >= 10:  # KEEP
    place_bet()
elif value_pct >= 5:  # MARGINAL
    half_kelly()
else:  # CANCEL
    skip()
```

### 关键陷阱：低赔率 Kelly 必为负
赔率 < 2.0 的 BACK 注，Kelly 计算几乎必然为负：
- Barcelona @1.65 -> Kelly=-1.2% -> **必须取消**

## DJYY → BA 名称匹配

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

## Bet Angel API 集成

### 已验证端点（2026-05-03）
```
GET BALANCE:   POST http://localhost:9000/api/markets/v1.0/getBalance
GET MARKETS:   POST http://localhost:9000/api/markets/v1.0/getMarkets
GET PRICES:    POST http://localhost:9000/api/markets/v1.0/getMarketPrices
PLACE BETS:   POST http://localhost:9000/api/betting/v1.0/placeBets   <- 注意是 betting 不是 markets！
```

### 价格结构（已验证）
```python
# selections 数组：
sel['back1']['prc']   # BACK 赔率
sel['back1']['sz']    # BACK 可交易量
sel['lay1']['prc']    # LAY 赔率
sel['lay1']['sz']     # LAY 可交易量
```

### 下注 payload 格式（已验证可用）
```python
{
    "marketId": market_id,     # 必须，字符串
    "async": False,
    "globalSettings": {"persist": True},
    "betsToPlace": [{
        "type": "BACK",         # <- 必须是 type 字段，不是 betType！
        "selectionId": int(sel_id),  # <- 必须是 INT，不是字符串！
        "price": float,
        "stake": float,         # <- float，不是字符串
    }]
}
```

### 已知陷阱
- ❌ `betType: "L"` -> 被 BA 解释为 BACK！
- ❌ `selectionId: "58805"` (字符串) -> API 返回 success=False
- ❌ market not monitored by Guardian -> UNKNOWN_MARKET 错误
- ⚠️ 只有 Guardian 监控的市场才能获取价格

## 执行清单

### Step 1: 提取 DJYY
- [ ] xbrowser focus+Enter 提取 7 策略 picks
- [ ] 解析 DOM 获取队名、赔率

### Step 2: CGMBet26 验证
- [ ] 连接 CGMBetStats_v3.db
- [ ] 查询相关球队历史数据
- [ ] 计算 Value%

### Step 3: Bet Angel 市场扫描
- [ ] getMarkets 获取活跃市场列表
- [ ] Guardian 加载 FT Coupon（约 400-500 市场）
- [ ] getMarketPrices 获取实时价格

### Step 4: Name Resolver 匹配
- [ ] register_ba_markets 加载 BA 市场
- [ ] find_match 对每场 DJYY pick 进行匹配
- [ ] 置信度 >= 0.5 才执行

### Step 5: 下注
- [ ] 每场 1 RON（用户确认）
- [ ] BACK 用 back1.prc，LAY 用 lay1.prc
- [ ] selectionId 转为 int

### Step 6: 监控
- [ ] 每 60 秒轮询 getMarketPrices
- [ ] 进球 → Cash Out 判断
- [ ] Cash Out endpoint: `/api/betting/v1.0/placeBets` + `{"type": "CASH_OUT"...}`

## 风控规则

1. 每场限 1 笔注（禁止同方向叠加）
2. 赔率范围：2.0-8.0（< 2.0 一律取消，> 10.0 减仓）
3. 单批次总暴露 <= 账户余额 10%
4. Kelly < 0 立即取消
5. Value < 5% 取消（MARGINAL 可以 5-10% 半仓）
