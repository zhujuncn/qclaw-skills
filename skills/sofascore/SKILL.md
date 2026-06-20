---
name: sofascore
description: |
  Sofascore 足球数据 API 集成。获取实时比赛数据、统计数据、事件时间线、赛程等。
  当用户提到 Sofascore、比赛数据、实时比分、足球统计、赛程查询等时触发。
---
depends_on:
  - football-council  # NameResolver v3 shared infra


# Sofascore API 技能

基于 Public-Sofascore-API 项目，提供 Sofascore 数据访问能力。

## 前置条件

- Python 3.8+ 已安装
- curl_cffi 库：`pip install curl_cffi`
- 仓库位置：`C:\Users\zhuju\.qclaw\workspace\Public-Sofascore-API`

## 核心端点

### 1. 比赛详情
```
GET https://api.sofascore.com/api/v1/event/{eventId}
```
返回：比赛基本信息、球队、比分、状态

### 2. 比赛统计
```
GET https://api.sofascore.com/api/v1/event/{eventId}/statistics
```
返回：控球率、射门、传球、犯规等统计数据

### 3. 事件时间线 (关键！)
```
GET https://api.sofascore.com/api/v1/event/{eventId}/incidents
```
返回：进球、红黄牌、换人、VAR 等事件数组

### 4. 动量图数据
```
GET https://api.sofascore.com/api/v1/event/{eventId}/graph
```
返回：比赛动量/压力图数据点

### 5. 每日赛程
```
GET https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date}
```
日期格式：`YYYY-MM-DD` (如 `2026-04-20`)

---

## DJYY ExchangeBets 集成

DJYY picks 可与 Sofascore 比赛数据交叉验证：
1. 从 DJYY 提取策略 picks (xbrowser `focus + Enter`)
2. 在 Sofascore 搜索比赛获取 eventId
3. 获取实时统计验证 DJYY 信号

**DJYY 按钮 DOM 索引**: HW-A=3, HW-B=5, BD=7, AW=9, X2=11, O2.5=13, CU9.5=15

### DJYY → BA 名称匹配
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

---

## 使用示例

### Python 客户端
```python
from curl_cffi import requests

# 必须模拟浏览器 TLS 指纹，否则 403
session = requests.Session(impersonate="chrome")

# 获取比赛事件
resp = session.get("https://api.sofascore.com/api/v1/event/12551555/incidents")
data = resp.json()

# incidents 数组包含所有事件
for incident in data.get('incidents', []):
    minute = incident.get('time')
    type_ = incident.get('type')  # goal, card, substitution
    print(f"{minute}': {type_}")
```

### 关键字段

**incident 对象：**
- `time`: 分钟数
- `type`: goal | card | substitution | period
- `player.name`: 球员名
- `homeScore` / `awayScore`: 当时比分
- `incidentClass`: 对于卡片 - yellow | red | yellowRed
- `isHome`: True/False

## 与 Bet Angel / Superbet 协同

1. **赛前研究**: 用 Sofascore 获取球队近期状态、历史交锋
2. **赛中监控**: incidents 端点实时推送进球/红黄牌事件
3. **赔率验证**: 对比 Sofascore 统计与博彩公司赔率

## 注意事项

- **TLS 指纹**: 必须用 curl_cffi 或类似库模拟浏览器
- **Rate Limit**: 限制较严，避免高频请求
- **Event ID**: 需通过 scheduled-events 或搜索获取

## 参考

- 完整文档: `C:\Users\zhuju\.qclaw\workspace\Public-Sofascore-API\README.md`
- Django 服务: `C:\Users\zhuju\.qclaw\workspace\Public-Sofascore-API\sofascore_service\`
