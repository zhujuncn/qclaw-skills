---
name: cgmbet26-strategies
version: 1.5.2
last_updated: 2026-05-07
status: active
parent_skills: [cgmbet26]
depends_on:
  - football-council  # NameResolver v3 shared infra
description: |
  CGMBet26 直接下单策略库。当用户提到策略、建议下单、买入/卖出信号、入场条件、资金管理、凯利公式、置信度、星级推荐、价值检测、P-value验证时使用此技能。
  本技能基于 CGMBet26 System v2.16 的14个分析模块，将“研究工具”转化为“可直接执行的交易信号”。
  适用场景：赛前快速决策、赛中实时下单、策略回测验证、资金配置。
---

# CGMBet26 直接下单策略库 v1.5.2

## 概率基准修正(2026-05-02)

**全局 Draw 率 = 26.2%**(基于 CGMBet26 数据库 217,585 场),不再是 31.85%。

所有 Kelly / EV 计算中的 baseline draw rate 必须更新:
- 旧值:`HR=0.3185` -> 错误高估 21%
- 新值:`HR=0.262`(全局)或从 `league_calibration.json` 读取

## 系统定位

**本技能 = CGMBet26 研究层 -> Bet Angel 执行层** 的桥梁:
```
CGMBet26 研究/概率计算 -> 策略信号 -> 决策 -> Bet Angel 下单
```

## 策略分级速查

| 等级 | 置信度 | 适用场景 | 建议仓位 |
|------|--------|---------|---------|
| Tier 1 | >85% | 保守型/大资金 | 标准 Kelly |
| Tier 2 | 70-85% | 标准型 | Half Kelly |
| Tier 3 | 55-70% | 激进型/小资金 | Quarter Kelly |
| Tier 4 | <55% | 测试/观摩 | 极小额或不参与 |

## Value 筛选阈值(实测验证 73 场)

| Value 范围 | 信号等级 | 动作 |
|-----------|---------|------|
| >= 20% | BLUE++ | 强信号,Tier 1,标准仓位 |
| 15-20% | BLUE+ | 强信号,KEEP |
| 10-15% | BLUE | 标准信号,KEEP |
| 5-10% | BLUE- | 弱信号,MARGINAL |
| -5%~5% | GRAY | 无价值,CANCEL |
| -15%~-5% | PINK | 负价值,CANCEL |
| < -15% | PINK++ | 强负价值,立即取消 |

### 低赔率陷阱(< 2.0)
Barcelona @1.65 -> Kelly=-1.2% -> **必须取消**

### 极端冷门(> 10.0)
即使 Value 为正,仍属彩票注,建议减仓至极小比例或直接取消。

### Draw 信号特征
双方平局率均 > 60% 时,Draw 价值极高(实测 Value 40-70%)

## DJYY ExchangeBets 策略信号源

| DJYY 策略 | Yield | WR | 适用 |
|-----------|-------|-----|------|
| Balance Draw | 13.58% | 31.85% | Draw 高价值 |
| Home Win B | 6.16% | 73.65% | Home Win |
| Away Win | 6.20% | 45.85% | Away Win |
| Home Win A | 5.93% | 46.75% | Home Win |
| Corners U9.5 | 5.89% | 53.65% | 角球 |

## DJYY → BA 名称匹配

**Name Resolver v3** 是所有足球技能的统一底层组件,位于:
```
C:/Users/zhuju/.qclaw/skills/football-council/scripts/name_resolver.py
别名库: C:/Users/zhuju/.qclaw/skills/football-council/data/team_aliases.json (578条)
```

所有技能统一使用以下导入方式:
```python
import sys
sys.path.insert(0, 'C:/Users/zhuju/.qclaw/skills/football-council/scripts')
from name_resolver import NameResolver

nr = NameResolver()
nr.register_ba_markets(ba_markets_dict)  # {market_name: market_id}

result = nr.find_match('Bayern Munchen', 'Mainz 05')
# -> {'ba_name': 'Bayern Munich v Mainz 05', 'score': 0.75, 'method': 'fuzzy'}

# v3 新增:一句话下单
result = nr.find_and_bet(home='Bodo Glimt', away='Molde',
                         side='BACK', max_price=1.5, stake=1.0)
```

#### Name Resolver v3 关键改进
- **匹配策略 5 层**: CGM_SHORTEN -> DJYY_ALIASES (300+) -> team_aliases.json (578条) -> EXPANSIONS -> fuzzy
- **CGM 缩写硬编码**: az->Az Alkmaar, fh->Hafnarfjordur, ibv->IBV, shamrock->Shamrock
- **去变音**: Genclerbirligi, Brondby, Malmo
- **性别过滤**: 男足!=女足,二队默认过滤
- **BA API 端点**: /api/betting/v1.0/placeBets | Price: back1.prc / lay1.prc
- **selectionId**: 必须是 INT,不是字符串

#### 关键别名映射(2026-05-03 验证)
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

## Tier 1: Suggestions (AI) - 最强自动信号

入口:Suggestions 界面 -> 选取以下过滤器
```
 Strong predictions only (>=70%)  <- 只看高置信
 Highlight only if there is a value <- 只看有价值
 Hide matches with insufficient data <- 隐藏低样本
 Min. games for prediction: 5(默认)
```

### 入场条件
```
 赛制: 杯赛/联赛均可
 信号强度: >= 70%(Suggestions AI)
 Value: 开启(有Value)
 样本量: >= 5 场
 联赛: 优先主流联赛(英超/西甲/意甲/德甲/法甲)
```

## Tier 2: Rating V - 经验频率概率

Rating V 策略基于 ELO 频率概率计算 Value。
入口:Rating V 界面

### 入场条件
```
 Rating V 信号 >= 70%(蓝色格)
 Value% >= 10%(Rating V)
 联赛: 优先高样本联赛
 赔率范围: 1.5-8.0
```

## Tier 3: Advanced Poisson - 批量泊松分析

入口:Advanced Poisson 界面 -> 设置 xG 公式
批量计算大批比赛的 Over/Under 概率。

### 入场条件
```
 Over 2.5 概率 >= 60%
 Value% >= 15%(Advanced Poisson)
 样本量 >= 10 场
```

## Tier 4: A.G.S. - 深度回测验证

入口:A.G.S. 界面 -> 选择策略类型 -> 回测
Yield% + P-value < 5% 验证显著性。

### 入场条件
```
 Yield% >= 5%(年化)
 P-value < 5%(统计显著)
 样本量 >= 50 场
```

## Goals Statistics - 赛中分钟概率

入口:Goals Statistics 界面
基于 ELO 匹配历史分钟进球概率。

### 入场条件
```
 当前比分: 0-0 或 1-0 / 0-1
 比赛时间: < 75 分钟
 剩余分钟 >= 15 分钟
 主队/客队分钟进球率 > 0.03/分钟
```

## Kelly Calculator - 资金管理

所有 Tier 策略统一使用 **Half Kelly**(避免波动):
```
 Kelly% = (BP - Q) / B
 Kelly% *= 0.5  # Half Kelly
 实际投注额 = Kelly% * 账户余额
```

## 策略回测验证(2026-04-24)

| 策略 | Yield | P-value | 样本 | 结论 |
|------|-------|---------|------|------|
| Suggestions | 8.3% | 2.1% | 217 | 显著有效 |
| Rating V | 6.7% | 4.3% | 152 | 显著有效 |
| Advanced Poisson | 12.1% | 0.8% | 89 | 显著有效 |
| A.G.S. | 15.4% | 0.2% | 312 | 显著有效 |

## 与 Bet Angel X2 集成

### 市场加载
```python
# 通过 Guardian 加载 FT Coupon
# 批量加载约 400-500 市场
```

### 下注端点(已验证)
```
POST http://localhost:9000/api/betting/v1.0/placeBets
Content-Type: application/json
```

### BACK 正确格式
```python
{
    "marketId": market_id,
    "async": False,
    "globalSettings": {"persist": True},
    "betsToPlace": [{
        "type": "BACK",       # <- 必须是 type 字段
        "price": float,        # 赔率
        "stake": float,        # 本金
        "selectionId": int,    # <- 必须是 INT,不是字符串
    }]
}
```

### LAY 正确格式
```python
{
    "betsToPlace": [{
        "type": "LAY",        # <- 必须是 type 字段
        "price": float,        # LAY 赔率 = BACK + 1
        "stake": float,
        "selectionId": int,    # <- 必须是 INT
    }]
}
```

### 关键陷阱(已验证不可用)
- ❌ `betType: "L"` -> 被解释为 BACK!
- ❌ `"side": "BACK"` -> 无效字段
- ❌ `"size": "5.0"` (字符串) -> stake 解析为 0

## 执行前检查清单

1. Guardian 是否已加载目标市场(必须!)
2. 市场是否为 In Play 或 Preplay(不接受 Closed)
3. getMarketPrices 是否返回 selections(价格必须 > 0)
4. selectionId 是否为整数(不是字符串)
5. 每场限 1 笔注(禁止叠加)
6. 赔率范围 2.0-8.0(< 2.0 一律取消,> 10.0 减仓)
7. 单批次总暴露 <= 账户余额 10%
8. Kelly < 0 -> 立即取消

## 下注成功记录

### 2026-05-07 批量下单（4/4 成功）
| 比赛 | 类型 | 赔率 | 状态 | betRef |
|------|------|------|------|--------|
| Kromeriz vs Slavia Prague B | BACK HOME | 2.28 | PENDING | 428222972009 |
| Ostrava B vs Brno | BACK AWAY | 3.55 | MATCHED @3.6 | 428222990021 |
| Vlasim vs Zizkov | BACK HOME | 2.24 | MATCHED @2.24 | 428223004496 |
| Egersund vs Raufoss | BACK HOME | 1.48 | PENDING | 428223007847 |

**流程**: CGM扫描 → Name Resolver匹配 → BA下单 → 4/4成功

### 2026-05-03 初次验证
- Bodo Glimt vs Molde - O0.5 BACK @1.02 x1 RON ✅
- AZ Alkmaar vs FC Twente - O0.5 BACK @1.03 x1 RON ✅
- Duisburg vs Cottbus - O0.5 BACK @1.04 x1 RON ✅
