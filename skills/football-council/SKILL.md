---
name: football-council
version: 1.9
last_updated: 2026-05-07
status: beta
parent_skills: [cgmbet26, cgmbet26-strategies]
description: |
  Football betting multi-agent roundtable discussion and decision system.
  Multiple specialized agents debate each other, final ruling by main agent + Evolver optimization.
  Triggers: "multi-agent discussion", "football council", "roundtable decision", "analyze live matches".
  Also: "name resolver", "team name match", "BA market lookup", "batch analysis".
tags: [football, betting, multi-agent, discussion, decision-making, evolver, name-resolver]
permissions: [network, shell]
---

# Football Council - Multi-Agent Betting Decision System

> **Version: 1.9** | Date: 2026-05-07 | Status: Beta

## ⭐ 自动下单成功模式 (2026-05-07 验证)

### 完整自动化流程（已验证 4/4 成功）

```
CGMBet26 扫描 → Name Resolver 匹配 → 筛选候选 → BA 下单 → 保存记录
```

### Step 1: CGMBet26 候选生成
```python
# 查询明日比赛 + ELO/Form 筛选
# 输出: _may6_final.json
# 格式: [{home, away, bet_side, bet_type, bet_price, market_id, sel_id}, ...]
```

### Step 2: BA 市场匹配
```python
# 使用 NameResolver v3
# 关键: Selection ID 必须从 getMarketPrices 按位置获取
# 顺序: [0]=Home, [1]=Draw, [2]=Away
```

### Step 3: 下单执行 (place_bets_may6.py)
```python
import requests

BA_BASE = 'http://localhost:9000'

def place_bet(market_id: str, sel_id: str, bet_type: str, price: float, stake: float = 1.0):
    """下单核心函数 - 2026-05-07 验证成功"""
    payload = {
        'marketId': market_id,
        'async': False,
        'globalSettings': {'accountId': 'DEFAULT'},
        'betsToPlace': [{
            'type': bet_type,        # 'BACK' or 'LAY'
            'price': price,           # float
            'stake': stake,           # float
            'selectionId': int(sel_id)  # 必须转 int
        }]
    }
    
    r = requests.post(f'{BA_BASE}/api/betting/v1.0/placeBets', json=payload, timeout=10)
    resp = r.json()
    
    # 关键：响应在 result.bets[0]
    bets = resp.get('result', {}).get('bets', [])
    if bets and bets[0].get('status') == 'OK':
        return {
            'success': True,
            'betRef': bets[0].get('betRef'),
            'priceMatched': bets[0].get('priceMatched'),
            'stakeMatched': bets[0].get('stakeMatched', 0.0)
        }
    return {'success': False, 'error': resp}
```

### Step 4: 响应解析
```json
{
  "status": "OK",
  "result": {
    "bets": [{
      "betToPlace": {"selectionId": "58805", "type": "BACK", "price": 3.55, "stake": 1.0},
      "status": "OK",
      "betRef": "428222990021",
      "priceMatched": 3.6,
      "stakeMatched": 1.0
    }]
  }
}
```

### 成功检查清单
- ✅ `bets[0].status == 'OK'` （不是外层 status）
- ✅ `betRef` 存在 = 下单成功
- ✅ `stakeMatched > 0` = 已成交
- ✅ `stakeMatched == 0` = PENDING（排队中）

### 关键经验（2026-05-07）

| # | 经验 | 说明 |
|---|------|------|
| 1 | **selectionId 必须转 int** | API 返回字符串，下注需 `int(sel_id)` |
| 2 | **Sel ID 非固定** | 58805 在某些市场是 AWAY，不是固定 Draw |
| 3 | **按位置取 Sel ID** | `[0]=Home, [1]=Draw, [2]=Away` |
| 4 | **响应路径** | `result.bets[0]` 不是 `result.results` |
| 5 | **Market ID** | 用 Betfair Market ID（1.xxxxx），不是 Guardian ID |

### 下注记录格式 (_may6_bets.json)
```json
[
  {
    "home": "Ostrava B",
    "away": "Brno",
    "bet_type": "BACK",
    "bet_side": "AWAY",
    "bet_price": 3.55,
    "sel_id": "58805",
    "betRef": "428222990021",
    "priceMatched": 3.6,
    "stakeMatched": 1.0,
    "placed": true
  }
]
```

---

## ⚠️ 概率基准修正 v1.8（2026-05-02）

### 循环论证问题（已解决）

所有研究脚本必须使用 **外部概率**（CGMBet26 独立数据），而非从市场赔率反推：

```
❌ 错误: draw_prob = 1 / market_back_odds  # 循环论证
✅ 正确: draw_prob = get_league_draw_rate(league_name)  # 来自 CGMBet26 历史
```

### 校准数据接口

```python
import json, os
CAL = r'C:\Users\zhuju\.self-improving\calibration\league_calibration.json'

def get_draw_rate(league: str = None) -> float:
    """返回 Draw 概率（0-1）。league=None 时返回全局 26.2%"""
    with open(CAL) as f:
        cal = json.load(f)
    if league and league in cal.get('leagues', {}):
        return cal['leagues'][league]['draw_rate']
    return cal['overall']['draw_rate']  # 0.262

# 使用示例
draw_prob = get_draw_rate('Norwegian Eliteserien')  # → 0.256
draw_prob = get_draw_rate()                         # → 0.262 (全局)
```

**全局 Draw 率 = 26.2%**（基于 217,585 场比赛），不再是旧值 31.85%。

---


## Concept

Football Council is a **multi-agent collaborative decision framework** that upgrades
traditional single-agent analysis into **multi-role roundtable discussion**:

```
[BetAngel Markets] → [Name Resolver] → [Council Convenes] → [Multi-Agent Debate]
    → [Main Agent Ruling] → [Execute Bet]

Modules:
  Name Resolver  (match BA ↔ Sofascore/CGM team names)
  CGMBet26       (statistical model / value detection)
  Poisson xG     (true odds from goals data)
  Kelly Criterion (stake sizing)
  Football Council (multi-agent decision)
```

---

## DJYY ExchangeBets 数据提取

DJYY (djyydata.com) 提供 7 个策略的每日 picks，是重要的数据来源。

### 关键技术突破 (2026-04-25)

DJYY 使用 **Radix UI Popover**，所有程序化点击方法均失败：
- ❌ CDP mouse click
- ❌ JavaScript `.click()` / `dispatchEvent`
- ❌ xbrowser `find role button click --name "N picks"` (无法区分重复名称)

**唯一成功方法**: `eval focus()` + `press Enter`
```javascript
document.querySelectorAll('button')[N].focus();  // 聚焦特定按钮
// 然后发送 Enter 键
```

### 策略按钮索引
| 策略 | Index | Picks |
|------|--------|-------|
| Home Win A | 3 | N |
| Home Win B | 5 | N |
| Balance Draw | 7 | N |
| Away Win | 9 | N |
| DC X2 | 11 | N |
| Over 2.5 | 13 | N |
| Corners U9.5 | 15 | N |

### 提取脚本模板
```powershell
$NODE = "C:\Program Files\QClaw\resources\node\node.exe"

# 初始化
& $NODE "...xb.cjs" init
& $NODE "...xb.cjs" run --browser cft open 'https://djyydata.com/en/strategies'
& $NODE "...xb.cjs" run --browser cft wait --load networkidle

# 获取按钮索引
& $NODE "...xb.cjs" run --browser cft eval "JSON.stringify(Array.from(document.querySelectorAll('button')).map(function(b,i){return i+':'+b.textContent.trim().slice(0,10)}).filter(function(s){return s.indexOf('picks')>0}))"

# 提取每个策略
foreach ($idx in 3,5,7,9,11,13,15) {
  & $NODE "...xb.cjs" run --browser cft eval "(function(){document.querySelectorAll('button')[$idx].focus();return 'ok'})()"
  & $NODE "...xb.cjs" run --browser cft press Enter
  Start-Sleep -Seconds 2
  & $NODE "...xb.cjs" run --browser cft snapshot -i
  # 解析 menuitem 提取比赛
  & $NODE "...xb.cjs" run --browser cft press Escape
}
```

### DJYY → BA 名称匹配结果 (2026-04-25)

| 指标 | 数值 |
|------|------|
| 匹配率 | 93.8% (30/32) |
| 核心映射 | Paris→PSG, Koln→FC Koln, Bayern Munchen→Bayern Munich, Hearts→Heart of Midlothian |
| 未匹配 | A-League (无 BA 市场), League One (无 BA 市场) |

```python
from name_resolver import NameResolver
nr = NameResolver()
nr.register_ba_markets(ba_markets_dict)
r.find_match("Paris", "Lille")  # → {'ba_name': 'Paris Saint-Germain v LOSC Lille', 'score': 1.0}
```

---

## Quick Reference

### fast_analysis.py — Single-Match Analysis (~1s)

```powershell
# Full analysis: CGMBet26 + Poisson xG → outputs TRUE ODDS
# (Kelly requires actual market odds — see value_scan_and_bet.py for full pipeline)
python .../fast_analysis.py analyze <Team1> <Team2>

# With actual market odds: --market-odds home=X,draw=Y,away=Z
python .../fast_analysis.py analyze Chelsea Leeds --market-odds home=2.06,draw=3.5,away=3.6

# Quick Bet Angel status (balance + market count)
python .../fast_analysis.py quick

# Monitor market until appears (polls every 30s, up to 30min)
python .../fast_analysis.py monitor <TeamKW1> <TeamKW2>

# Get prices for specific market IDs
python .../fast_analysis.py prices 1.234,1.235
```

### name_resolver.py — Team Name Matching

```powershell
# Test resolver on tomorrow's matches
python C:\Users\zhuju\.qclaw\workspace\_test_resolver_v2.py

# Use in script:
python -c "
import sys; sys.path.insert(0, '.../scripts')
from name_resolver import NameResolver
nr = NameResolver()
nr.register_ba_markets({market_name: market_id})
r = nr.find_match('Sheffield United', 'Blackburn Rovers')
print(r)
"
```

### Batch Betting Pipeline (CORRECT — fixed 2026-04-27)

```powershell
# Step 1: Get all BA Match Odds markets with selection IDs and prices
python C:\Users\zhuju\.qclaw\workspace\scan_and_bet.py
# Output: current_live_markets.json (139 Match Odds with prices)

# Step 2: Batch analysis — CGMBet26 Poisson xG + REAL value calculation
python C:\Users\zhuju\.qclaw\workspace\value_scan_and_bet.py
# Output: top_value_bets.json (ranked value opportunities)
# Key fix: Value% = (1/true_odds - 1/market_back) / (1/market_back) * 100
# (NOT the old hardcoded 1/true_odds * 1.07 formula)

# Step 3: Place value bets
python C:\Users\zhuju\.qclaw\workspace\place_bets.py
# Input: top_value_bets.json → BACK @ 1.5 RON each
# Output: bet_results.json with bet_ids
```

**IMPORTANT**: Use `x2_framework` (in `betangel/` directory) for all BA API calls:
- Market data: `xf.get_guardian_markets()` + `xf.scan_prices_bulk()`
- Prices: `xf.get_market_prices(market_id)` → returns `selections[].back1.prc`
- Endpoints: `http://localhost:9000/api/markets/v1.0/` (NOT `/api/betting/v1.0/`)

### ⭐ CGMBet26 Value Scan + Betting (2026-04-27 验证: 10/10成功)

```powershell
# 批量 LAY Draw 下注 (基于 EV 筛选)
python C:\Users\zhuju\.qclaw\workspace\_batch_place_draw_lay.py
```
- 执行结果: 13/13 下注成功
- 总注额: 15.6 RON
- 总责任: 47.3 RON
- 10 场立即成交, 3 场排队

**关键实现细节**:
- 使用 `requests.post(url, json=payload)` 直接调用 BA API
- `selectionId` 必须在 **每个 betsToPlace 条目内部**
- Draw selection ID = `'58805'` (字符串)
- 速率限制: 0.5s 延迟避免 API 过载
- 成功检查: `status == 'OK'`

---

## Critical Findings (Must Know)

### Bet Angel API — Correct Patterns

| What | Correct | WRONG |
|------|---------|-------|
| Endpoint | `/api/betting/v1.0/placeBets` | `/api/bets/v1.0/placeBets` ❌ |
| Display market | `POST /api/markets/v1.0/displayMarket` | (must call before prices) |
| Get prices | `POST /api/markets/v1.0/getMarketPrices` | |
| Header | `"Accept": "application/json"` | |
| Payload | `{"marketId":"xxx","dataRequired":["BEST_PRICE_ONLY"]}` | |
| Price fields | `back1.prc` / `lay1.prc` | `back.price` ❌ |
| Size field | `back1.sz` | |
| Stake type | `type: "BACK"` or `"LAY"` (not `betType`) | |
| Stake value | float, NOT string | `"stake": "5.0"` → fails ❌ |
| placeBets status | `"OK"` = success | `"SUCCESS"` ❌ (wrong!) |
| Market ID for placeBets | **Guardian ID** from getMarkets | Betfair Market ID ❌ |
| Selection ID source | `getMarkets` → `selections[].id` | `getMarketPrices` ❌ |

**placeBets full payload structure**:
```json
{
  "marketId": "1.257177154",
  "async": false,
  "globalSettings": {"accountId": "DEFAULT"},
  "betsToPlace": [
    {"type": "BACK", "price": 4.40, "stake": 1.3, "selectionId": "48461"}
  ]
}
```

**placeBets success response**:
```json
{
  "status": "OK",
  "result": {
    "bets": [
      {
        "betToPlace": {"selectionId": "48461", "type": "BACK", "price": 4.4, "stake": 1.3},
        "status": "OK",
        "betRef": "426555002473",
        "priceMatched": 4.4,
        "stakeMatched": 1.3
      }
    ]
  }
}
```

### 🚨 Critical Fix (2026-04-28)

**BUG**: 之前用 `resp.get('result', {}).get('results', [])` ❌

**FIX**: 用 `resp.get('result', {}).get('bets', [])` ✅

**原因**: API 返回 `result.bets` 不是 `result.results`！

```python
# 错误 (之前):
bets = resp.get('result', {}).get('results', [])

# 正确 (现在):
bets = resp.get('result', {}).get('bets', [])
br = bets[0]
if br.get('status') == 'OK':  # inner status, not outer
    betRef = br.get('betReference', '')
```

**Draw selection**: global ID = `'58805'` (可用在任意市场)

---

## Football Council v2 执行 (2026-04-28)


运行 Football Council 多 Agent 分析后批量下单流程：

```powershell
# Step 1: 运行分析 (5 场比赛)
python C:\Users\zhuju\.qclaw\skills\football-council\scripts\fast_analysis.py analyze <Team1> <Team2>

# Step 2: 生成 council 结果JSON → `_council_results.json`

# Step 3: 批量下单 (v3修复版)
python C:\Users\zhuju\.qclaw\workspace\_place_council_v3.py
```

**v3 下单脚本关键逻辑**:
```python
# 1. getMarkets 获取Guardian selection IDs
r = sess.post(f'{BA_BASE}/markets/v1.0/getMarkets', json={...})
# → selections[].id = Guardian sel_id

# 2. getMarketPrices 获取实时价格
# → selections[].back1.prc = BACK 价格

# 3. placeBets 用 Guardian ID + sel_id
payload = {
    'marketId': gid,  # Guardian ID
    'betsToPlace': [{
        'selectionId': sel_id,  # Guardian sel_id
        'type': 'BACK',
        'price': price,
        'stake': 1.12
    }]
}

# 4. 解析响应 (关键！)
bets = resp.get('result', {}).get('bets', [])  # 不是 results!
br = bets[0]
if br.get('status') == 'OK':
    betRef = br.get('betReference', '')
```

**v2 结果 (2026-04-28)**:
- 17/21 bets 成功下单
- 14.56 RON staked
- 4 failed: PROCESSED_WITH_ERRORS (市场关闭/流动性不足)
- betRefs 记录在 `_council_bet_log.json`

### Kelly Calculation Bug (FIXED 2026-04-27)

**Problem**: `fast_analysis.py` used hardcoded `true_odds * 1.07` as market estimate →
ALL selections showed ~6.5-7% edge → Kelly analysis completely meaningless.

**Correct formula**:
```
Value% = (1/true_odds - 1/market_back) / (1/market_back) * 100
```
- Positive = model beats market (BACK有价值)
- Negative = market overpricing (BACK无价值)

**Fixed scripts**:
- `value_scan_and_bet.py` — compares CGMBet26 true odds vs actual BA prices
- `fast_analysis.py` — now outputs true odds clearly, with `--market-odds` flag support

### getMarketPrices — Two Approaches

**Approach A (Recommended)**: `xf.scan_prices_bulk()` — one API call for ALL markets
```python
prices = xf.scan_prices_bulk()  # returns dict: {market_id: {selections: {sel_id: {back1: {prc, sz}, lay1: {prc, sz}}}}}}
# Use this for batch operations — most efficient
```

**Approach B**: `displayMarket` + `getMarketPrices` — single market (slower)
1. `POST /api/markets/v1.0/displayMarket` → `{"marketId": "xxx"}`
2. Wait ~0.5s
3. `POST /api/markets/v1.0/getMarketPrices` → `{"marketId": "xxx", "dataRequired": ["BEST_PRICE_ONLY"]}`
4. Response: `result.markets[].selections[].back1.prc / back1.sz / lay1.prc`

### applyCoupon Only Supports "FT"

```python
# WORKS:
xf.apply_coupon('FT')

# ALL FAIL:
xf.apply_coupon('Tomorrow')
xf.apply_coupon('FT Tomorrow')
xf.apply_coupon('Soccer - Tomorrow')
xf.apply_coupon('Soccer - All')
```

`getMarkets` does NOT return `marketStartTime` — cannot filter by date from API.

### CGMBet26 Database — Critical Schema Facts

| Fact | Value |
|------|-------|
| StatusCode = 0 | COMPLETED match (not 1!) |
| StatusCode = 'S' | Scheduled/pending |
| Teams.Id | TEXT (e.g. '33001'), not integer |
| Tomorrow schedule | Only ~33 matches in CGM DB for next day |
| Cyprus | ZERO data |
| Finland | League 3301 (Veikkausliiga) |
| Slovakia | League 23 (2. Liga) |
| Database path | `C:\Users\zhuju\AppData\Roaming\CGMBetSystem\CGMBetStats_v3.db` |

### Name Resolver — Key Thresholds

| Score | Interpretation | Action |
|-------|---------------|--------|
| ≥ 0.75 | High confidence | Auto-learn alias |
| 0.50–0.74 | Medium | Review manually |
| 0.35–0.49 | Low | Check if wrong match |
| < 0.35 | None | Skip / manual |

---

## Module 1: Name Resolver (`scripts/name_resolver.py`)

**Purpose**: Match team names across data sources → BA market names (for Bet Angel execution)

### Architecture

```
外部名称 → [1.精确匹配] → [2.别名库(持久化)] → [3.缩写展开] → [4.模糊匹配] → BA队名
                 ↓                                        ↓
            完全一致命中                            性别过滤 ✅
                                                       双边约束 ✅
                                                       联赛上下文 ✅
```

### Core Class: `NameResolver`

**Init**:
```python
from name_resolver import NameResolver
nr = NameResolver()  # loads team_aliases.json automatically
```

**Methods**:

`register_ba_markets(ba_markets: dict)`
- ba_markets = `{market_name: market_id}`, e.g. `{"Sheff Utd v Blackburn - Match Odds": "1.234"}`
- Automatically filters out women's/reserve teams

`find_match(home: str, away: str, league: str = '') -> dict | None`
```python
r = nr.find_match("Sheffield United", "Blackburn Rovers")
# Returns:
# {
#   'ba_name': 'Sheff Utd v Blackburn - Match Odds',
#   'ba_id': '123',
#   'ba_home': 'Sheff Utd',
#   'ba_away': 'Blackburn',
#   'score': 1.0,
#   'home_score': 1.0,
#   'away_score': 1.0,
#   'method': 'high',
#   'is_women': False
# }
```

`resolve_batch(ba_markets: dict, external_events: list, source: str = 'unknown') -> list`
- external_events = `[{'home': 'Team', 'away': 'Team', 'league': 'League', ...}, ...]`
- Auto-learns aliases for matches with score ≥ 0.75
- Returns list of result dicts (same structure as find_match)

`learn_from_results(results: list, min_score: float = 0.75)`
- Explicitly learn from a batch of results

`save_aliases()`
- Persist aliases to `data/team_aliases.json`

`get_stats(results: list) -> dict`
- Returns: `{total, high, medium, low, none, ba_total, ba_covered, ba_coverage}`

`get_unmatched_ba(results: list) -> list`
- Returns list of BA markets not matched by any external event

### Matching Strategy Detail

1. **Alias mapping** (score 1.0): `team_aliases.json` lookup
2. **Exact match** (score 1.0): lowercase string equality (after strip/diacritics)
3. **Abbreviation expansion** (score ~0.8-1.0):
   - `sheffield united` → known abbr → `Sheff Utd`
   - `fc barcelona` → strip `FC ` → `Barcelona`
4. **Fuzzy match** (0-1):
   - Token Jaccard (word-level overlap)
   - SequenceMatcher (character-level similarity)
   - Takes MAX(forward_score, reverse_score) for bilateral robustness
5. **Gender filter**: if external event has no `(W)`/`Women` flag, skip BA women's markets
6. **Bilateral constraint**: home+away must match the SAME market (prevents Spartak Moscow → Spartak Subotica cross-pollution)

### Alias Database

Stored at `data/team_aliases.json`:
```json
{
  "sheffield united": "Sheff Utd",
  "sporting cp": "Sporting Lisbon",
  "bodo glimt": "Bodo Glimt",
  ...
}
```
Auto-populated via learning. ~151 aliases learned by 2026-04-22.

### Test Results (Tomorrow 2026-04-23)

| Metric | Value |
|--------|-------|
| BA markets | 86 (1 women's filtered) |
| Sofascore events | 251 |
| High confidence | 64 (74.4%) |
| BA coverage | 75.6% (65/86) |
| Unmatched | 21 (mostly small leagues Sofascore doesn't cover) |

---

## Module 2: CGMBet26 Statistical Engine

**Purpose**: Historical data + value detection + probability modeling

### Database Schema

```
CGMBetStats_v3.db
├── Matches (MatchId TEXT, Date TEXT, Time TEXT, Season TEXT, Round TEXT,
│           HomeTeamId TEXT, AwayTeamId TEXT, HomeGoals TEXT, AwayGoals TEXT,
│           Status TEXT, StatusCode TEXT)
├── Teams (Id TEXT, Name TEXT, Seasons TEXT, Verified TEXT)
├── Leagues (Id TEXT, Name TEXT, Country TEXT)
├── Odds (MatchId TEXT, Type TEXT, Line TEXT, HomeOdds TEXT, DrawOdds TEXT,
│        AwayOdds TEXT, OverOdds TEXT, UnderOdds TEXT, ...)
└── Ratings, MatchPlaces, MatchStats
```

**Key Query Patterns**:
```python
# Find team by name (Id is TEXT)
cur.execute("SELECT Id, Name FROM Teams WHERE Name LIKE ?", (f"%{name}%",))

# Team's recent form (last N matches, status=0 completed)
cur.execute("""
    SELECT * FROM Matches
    WHERE (HomeTeamId=? OR AwayTeamId=?) AND StatusCode='0'
    ORDER BY Date DESC LIMIT ?
""", (team_id, team_id, n))

# H2H between two teams
cur.execute("""
    SELECT * FROM Matches
    WHERE HomeTeamId IN (?,?) AND AwayTeamId IN (?,?) AND StatusCode='0'
    ORDER BY Date DESC LIMIT 20
""", (id1, id2, id1, id2))
```

---

## Module 3: Poisson True Odds Model

**Purpose**: Estimate fair odds from xG data (CGMBet26 ratings)

### Lambda Calculation

```python
lambda_home = 0.6 * t1_home_xG_scored + 0.4 * t2_away_xG_conceded
lambda_away = 0.6 * t2_away_xG_scored + 0.4 * t1_home_xG_conceded
```

### 1X2 True Odds

6×6 Poisson goal probability grid, then:
```
home_win_prob = sum(p_lambda_home[i] * p_lambda_away[j]) for i>j
draw_prob     = sum(p_lambda_home[i] * p_lambda_away[i])
away_win_prob = sum(p_lambda_home[i] * p_lambda_away[j]) for i<j
true_odds = 1/probs (no bookmaker margin)
```

### Over 2.5 Goals

```
O2.5_prob = 65% * historical_over25_rate + 35% * poisson_over25
```

### Both Teams To Score

```
BTTS_prob = weighted historical BTTS rate + away_scoring_rate_adjustment
```

---

## Module 4: Kelly Criterion

**Purpose**: Optimal stake sizing

### Formula

```
Kelly% = (b × p - q) / b × 0.5  (Half Kelly cap)

where:
  b = market_odds - 1   (decimal odds - 1, e.g. 3.0 → b=2.0)
  p = true_probability  (from Poisson model)
  q = 1 - p

edge = (market_odds - true_odds) / true_odds
```

### Decision Matrix

| Signal  | Kelly%  | Action          |
|---------|---------|-----------------|
| STRONG  | >8%     | Immediate bet   |
| VALUE   | 3–8%    | Standard bet    |
| LOW     | 1–3%    | Small test      |
| SKIP    | <1%     | No bet          |

### Market Odds vs True Odds

If Bet Angel market not loaded: estimate market opening odds ≈ true_odds × 1.07 (7% margin).
**WARNING**: Do NOT set market odds as true_odds × 0.95 (this makes everything SKIP — learned the hard way 2026-04-22).

---

## Module 5: Football Council Multi-Agent

**Purpose**: Complex matches requiring multi-agent debate

### Council Members

| Agent | Weight | Role |
|-------|--------|------|
| Sofascore Analyst | 25% | Real-time data, live form |
| CGMBet26 Strategist | 30% | Statistical model, value |
| Match Analyzer | 25% | Comprehensive judge |
| Evolver | 20% | Self-optimization |

### Voting Rules

```
3/4 approve → STRONG (bet immediately)
2/4 approve → VALUE (standard position)
1/4 approve → CAUTION (quarter Kelly)
0/4 approve → NO BET
```

### Execution: `fast_analysis.py`

```
Input: team names → Output: Kelly recommendations

PHASE 1 (parallel, ~0.5s):
  ├─ worker_cgmbet_teams()      → team IDs from CGMBet26
  ├─ worker_betangel_markets()  → all live/pre-match markets
  ├─ worker_betangel_balance() → account balance
  └─ worker_sofascore_events()  → today's + tomorrow's events

PHASE 2 (parallel, ~0.3s):
  ├─ worker_cgmbet_stats(id1)   → team1 form + goals stats
  ├─ worker_cgmbet_stats(id2)   → team2 form + goals stats
  └─ worker_cgmbet_h2h(id1,id2) → head-to-head matches

PHASE 3: Poisson xG true odds
PHASE 4: Kelly recommendations
```

---

## Integration Pipeline (Full Workflow)

```
1. Name Resolver
   BA markets → register → Sofascore events → resolve_batch
   → matched events with BA market IDs

2. Stats Filter
   matched events → Sofascore API statistics check
   → events WITH statistics data

3. CGMBet26 Lookup
   → historical stats, ratings, H2H

4. Poisson True Odds
   → true_odds for 1X2 / O2.5 / BTTS

5. Kelly Criterion
   → stake recommendations per market

6. Bet Placement
   → Bet Angel /api/betting/v1.0/placeBets
```

---

## File Structure

```
football-council/
├── SKILL.md                           # This file
├── README.md                          # (unused)
├── data/
│   ├── team_aliases.json              # Team-level alias DB (auto-learned)
│   ├── aliases.json                   # (legacy, unused)
│   └── decisions/                     # Evolver decision records
├── scripts/
│   ├── fast_analysis.py               # Single-match analysis (~1s)
│   ├── batch_analyze_and_bet.py      # ⭐ NEW: Full pipeline (analyze + auto-bet)
│   ├── name_resolver.py              # Team name matching engine
│   ├── read_betangel_live.py         # Legacy: read BA markets
│   ├── run_council.py                 # Legacy: full multi-agent council
│   ├── spawn_council.py              # Legacy: spawn sub-agents
│   ├── vote_aggregator.py             # Legacy: vote aggregation
│   └── record_decision.py             # Legacy: Evolver recording
└── references/
    ├── agent_prompts.md               # Agent system prompts
    └── decision_rules.md              # Decision rules config
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.4 | 2026-04-24 | Evolver: Added Value 筛选阈值 (73场实测), Poisson混合模型, 风控规则强化, Draw信号特征. |
| 1.3 | 2026-04-23 | Added batch auto-betting pipeline. 83 bets placed. |
| 1.2 | 2026-04-22 | Added Name Resolver v2 (team-level aliases, gender filter, bilateral constraint, 75.6% BA coverage). Added Bet Angel API critical fixes. Added batch pipeline patterns. |
| 1.1 | 2026-04-22 | Added `fast_analysis.py`: parallel CGMBet26 + Poisson + Kelly, ~1s per match. |
| 1.0 | 2026-04-22 | Initial version: 3-Agent discussion + Evolver integration |

---

## Trigger Keywords

- "analyze live matches" / "analyze match"
- "football council" / "roundtable"
- "multi-agent discussion"
- "value bet" / "find value"
- "name resolver" / "team name match" / "match team names"
- "batch analysis" / "scan all matches" / "analyze all matches"
- "auto bet" / "place all bets" / "batch betting"
- "poisson" / "kelly"
- "分析" / "投注" / "足球" (Chinese triggers)

---

## Evolver 学习记录 (2026-04-24)

### 73 场实单分析 → Value 筛选验证

| 指标 | 结果 |
|------|------|
| 样本 | 220 笔 BACK, 73 场比赛, 273.40 RON |
| KEEP (≥10%) | 36 场 (49.3%), 139.30 RON |
| MARGINAL (5-10%) | 12 场 (16.3%), 44.70 RON |
| CANCEL (<5%) | 25 场 (34.3%), 89.40 RON |

### Poisson xG 混合模型 (推荐使用)
```
est = Poisson(65%) + Form(35%)
lambda_home = 0.6 * h_xg_scored + 0.4 * a_xg_conceded
lambda_away = 0.6 * a_xg_scored + 0.4 * h_xg_conceded
```

### Value 阈值表 (实测)

| Value | 信号 | 动作 |
|-------|------|------|
| ≥20% | BLUE++ | KEEP, 标准 Kelly |
| 15-20% | BLUE+ | KEEP |
| 10-15% | BLUE | KEEP |
| 5-10% | BLUE- | MARGINAL |
| -5%~5% | GRAY | CANCEL |
| <-15% | PINK++ | 立即取消 |

### 风控规则 (强化)
- 赔率 < 2.0: 一律取消 (Kelly 必为负)
- 赔率 > 10.0: 减仓或取消 (彩票注)
- 每场限 1 笔: 禁止同方向叠加
- 单批次暴露 ≤ 10% 银行余额

### Draw 信号 (高价值)
- 双方平局率均 > 60% → Draw Value 40-70%
- 适用: 挪威/瑞典/爱尔兰/苏格兰低级别联赛
- 对手样本 < 10 场不可靠

### fast_analysis.py 优化建议
- 采纳 Poisson 混合模型替代纯形态估算
- 添加 Value 阈值筛选
- 添加赔率范围过滤 (2.0-8.0)
- 添加 Kelly < 0 自动取消逻辑