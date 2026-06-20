---
name: match-fetch
version: 1.0.0
last_updated: 2026-05-03
status: beta
depends_on:
  - football-council  # NameResolver v3 shared infra
description: |
  足球比赛数据获取技能。根据队名或联赛获取比赛信息，支持 Sofascore API、OpenLigaDB 等多个数据源。
  当用户提到"查比赛"、"获取比赛"、"查赛程"、"查赛果"、"搜比赛"、"find match"、"get fixtures"时触发。
---

# Match Fetch v1.0.0 - 比赛数据获取

## 功能

- 按队名搜索比赛
- 按联赛/日期获取赛程
- 获取比赛结果
- 多数据源整合（Sofascore / OpenLigaDB / CGMBet26）

## 数据源

### Sofascore API

```python
from curl_cffi import requests
session = requests.Session(impersonate='chrome')
base = 'https://api.sofascore.com/api/v1'

# 每日赛程
resp = session.get(
    f'{base}/sport/football/scheduled-events/{date}',
    timeout=15
)  # date: YYYY-MM-DD

# 比赛详情
event = session.get(f'{base}/event/{event_id}', timeout=15).json()['event']

# 比赛统计
stats = session.get(f'{base}/event/{event_id}/statistics', timeout=15).json()

# 事件时间线
incidents = session.get(f'{base}/event/{event_id}/incidents', timeout=15).json()
```

### OpenLigaDB（德国足球）

```python
from scripts.openligadb_client import OpenLigaDB

oldb = OpenLigaDB()
# 获取当前德甲比赛
matches = oldb.get_current_matches('bl1')

# 获取积分榜
table = oldb.get_table('bl1', 2025)

# 获取射手榜
scorers = oldb.get_scorers('bl1', 2025)
```

### CGMBet26（统计分析）

```python
import sqlite3
conn = sqlite3.connect(r'C:\Users\zhuju\AppData\Roaming\CGMBetSystem\CGMBetStats_v3.db')
# 查询球队历史战绩
```

## Name Resolver v3 统一队名匹配

**所有足球技能统一使用 NameResolver v3**：
```
C:/Users/zhuju/.qclaw/skills/football-council/scripts/name_resolver.py
别名库: C:/Users/zhuju/.qclaw/skills/football-council/data/team_aliases.json (578条)
```

```python
import sys
sys.path.insert(0, 'C:/Users/zhuju/.qclaw/skills/football-council/scripts')
from name_resolver import NameResolver

nr = NameResolver()
# 注册 BA 市场
nr.register_ba_markets(ba_markets_dict)

# 查找比赛
result = nr.find_match('Paris', 'Lille')
# -> {'ba_name': 'Paris St-G v Lille', 'score': 1.0}

# 多数据源名称统一转换
nr.find_team('Bayern Munchen')  # -> 'Bayern Munich'
nr.find_team('PSG')  # -> 'Paris St-G'
```

#### Name Resolver v3 关键改进
- **匹配策略 5 层**: CGM_SHORTEN -> DJYY_ALIASES (300+) -> team_aliases.json (578条) -> EXPANSIONS -> fuzzy
- **CGM 缩写硬编码**: az->Az Alkmaar, fh->Hafnarfjordur, ibv->IBV, shamrock->Shamrock
- **去变音**: Genclerbirligi, Brondby, Malmo
- **性别过滤**: 男足!=女足，二队默认过滤
- **BA API 端点**: /api/betting/v1.0/placeBets | Price: back1.prc / lay1.prc
- **selectionId**: 必须是 INT

## 使用示例

### 按队名搜索
```python
# 输入: "Bayern Munich vs Mainz"
# 输出: {home: 'Bayern Munich', away: 'Mainz', league: 'Bundesliga', time: '...'}
```

### 按日期获取赛程
```python
# 2026-05-04 所有比赛
matches = get_scheduled_events('2026-05-04')
for m in matches:
    print(f"{m['time']} {m['home']} v {m['away']} ({m['league']})")
```

### 整合多数据源
```python
# Sofascore 获取实时数据
ss = get_sofascore(event_id)

# CGMBet26 获取历史统计
cgm = query_cgmbet(home='Bayern Munich', away='Mainz')

# OpenLigaDB 获取德甲积分
bl_table = get_openligadb_table('bl1', year=2025)
```

## 输出格式

```markdown
## [Home] vs [Away]

- **联赛**: [联赛名]
- **时间**: [日期 时间] (Bucharest UTC+3)
- **状态**: [Scheduled / Live / Finished]
- **比分**: [主队得分 - 客队得分] (如已完成)

### Sofascore 实时数据
| xG | 射门 | 控球率 |
|----|------|--------|
| X.XX | XX | XX% |

### CGMBet26 历史（[联赛]）
| 指标 | 主队 | 客队 |
|------|------|------|
| 近15场胜率 | XX% | XX% |
| xG 场均 | X.XX | X.XX |
| Draw 率 | XX% | XX% |
```
