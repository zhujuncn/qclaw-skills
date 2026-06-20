---
name: openligadb
description: OpenLigaDB 足球数据 API 集成。获取德国足球联赛（德甲、德乙、德丙）、欧洲联赛比赛数据、积分榜、射手榜、球队信息。当用户提到 OpenLigaDB、德甲数据、德乙数据、德国足球联赛、bl1、bl2、bl3、Spieltag、Bundesliga、足球比分、比赛结果、积分榜、射手榜时触发。
license: MIT
---
depends_on:
  - football-council  # NameResolver v3 shared infra


# OpenLigaDB API Skill

德国足球数据开放平台 API 封装。提供实时比赛数据、积分榜、射手榜等查询能力。

## API Base

```
https://api.openligadb.de/
```

## 核心参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `leagueShortcut` | 联赛短代码 | `bl1`(德甲), `bl2`(德乙), `bl3`(德丙) |
| `leagueSeason` | 赛季年份（赛季开始年） | `2024` = 2024/25赛季 |
| `groupOrderId` | 比赛轮次（Spieltag） | `1`-`34` |

## 常用 API 端点

### 1. 获取当前轮次比赛
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

## 常用联赛短代码

| 代码 | 联赛 |
|------|------|
| `bl1` | 德甲（1. Bundesliga） |
| `bl2` | 德乙（2. Bundesliga） |
| `bl3` | 德丙（3. Liga） |

## 使用脚本

```bash
# 获取当前德甲轮次
python scripts/openligadb_client.py current bl1

# 获取指定轮次
python scripts/openligadb_client.py matchday bl1 2024 11

# 获取积分榜
python scripts/openligadb_client.py table bl1 2024

# 获取射手榜
python scripts/openligadb_client.py scorers bl1 2024

# 获取球队列表
python scripts/openligadb_client.py teams bl1 2024
```

## 缓存策略

使用 `getlastchangedate` 检查数据是否更新，避免不必要的轮询：

```python
last_change = api.get_last_change_date("bl1", 2024, 11)
if last_change != cached_change:
    matches = api.get_matchday("bl1", 2024, 11)
    cached_change = last_change
```

## 来源

- GitHub: https://github.com/OpenLigaDB/OpenLigaDB-Samples
- API 文档: https://api.openligadb.de/
