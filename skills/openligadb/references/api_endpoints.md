# OpenLigaDB API 端点完整参考

来源: https://github.com/OpenLigaDB/OpenLigaDB-Samples + Swagger OpenAPI 3.0.4

## API Base URL

```
https://api.openligadb.de/
```

## 所有端点

### 比赛数据

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/getmatchdata/{leagueShortcut}` | 当前轮次比赛 |
| GET | `/getmatchdata/{leagueShortcut}/{leagueSeason}` | 整赛季比赛 |
| GET | `/getmatchdata/{leagueShortcut}/{leagueSeason}/{groupOrderId}` | 指定轮次 |
| GET | `/getmatchdata/{leagueShortcut}/{leagueSeason}/{teamFilterstring}` | 按队名过滤 |
| GET | `/getmatchdata/{matchId}` | 按 ID 获取比赛 |
| GET | `/getmatchdata/{teamId1}/{teamId2}` | 两队历史交锋 |

### 下一场/最后一场

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/getnextmatchbyleagueteam/{leagueId}/{teamId}` | 某队下一场(需leagueId) |
| GET | `/getnextmatchbyleagueshortcut/{leagueShortcut}` | 联赛下一场 |
| GET | `/getlastmatchbyleagueteam/{leagueId}/{teamId}` | 某队最后一场(需leagueId) |
| GET | `/getlastmatchbyleagueshortcut/{leagueShortcut}` | 联赛最后一场 |

### 轮次/分组

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/getcurrentgroup/{leagueShortcut}` | 当前轮次信息 |
| GET | `/getavailablegroups/{leagueShortcut}/{leagueSeason}` | 所有轮次列表 |

### 积分榜/射手榜/球队

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/getbltable/{leagueShortcut}/{leagueSeason}` | 积分榜 |
| GET | `/getgoalgetters/{leagueShortcut}/{leagueSeason}` | 射手榜 |
| GET | `/getavailableteams/{leagueShortcut}/{leagueSeason}` | 球队列表 |

### 元数据

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/getavailableleagues` | 所有可用联赛 |
| GET | `/getavailablesports` | 所有运动类型 |
| GET | `/getlastchangedate/{leagueShortcut}/{leagueSeason}/{groupOrderId}` | 最后变更时间 |
| GET | `/getresultinfos/{leagueId}` | 联赛结果类型配置 |

## 数据模型

### Match (比赛)

```typescript
interface Match {
  matchID: number;
  matchDateTime: string;        // "2024-10-26T15:30:00"
  matchDateTimeUTC: string;     // "2024-10-26T13:30:00Z"
  leagueId: number;
  leagueName: string;
  leagueSeason: number;
  leagueShortcut: string;
  matchIsFinished: boolean;
  group: Group;
  team1: Team;
  team2: Team;
  matchResults: MatchResult[];
  goals: Goal[];
  location: Location;
  numberOfViewers: number;
}
```

### Team (球队)

```typescript
interface Team {
  teamId: number;
  teamName: string;
  teamIconUrl: string;
  shortName?: string;
  teamGroupName?: string;
}
```

### MatchResult (比赛结果)

```typescript
interface MatchResult {
  resultID: number;
  resultName: string;           // "Halbzeitergebnis" | "Endergebnis"
  pointsTeam1: number;
  pointsTeam2: number;
  resultOrderID: number;
  resultTypeID: number;         // 1=半场 2=全场
  resultDescription: string;
}
```

### Group (轮次)

```typescript
interface Group {
  groupName: string;            // "8. Spieltag"
  groupOrderID: number;         // 8
  groupID: number;
}
```

### Goal (进球)

```typescript
interface Goal {
  goalID: number;
  goalScoreTeam1: number;
  goalScoreTeam2: number;
  goalMatchMinute: number;
  goalGetterID: number;
  goalGetterName: string;
  isPenalty: boolean;
  isOwnGoal: boolean;
  isOvertime: boolean;
  comment: string;
}
```

### League (联赛)

```typescript
interface League {
  leagueId: number;
  leagueName: string;
  leagueShortcut: string;
  leagueSeason: number;
}
```

### GoalGetter (射手)

```typescript
interface GoalGetter {
  goalGetterId: number;
  goalGetterName: string;
  goalCount: number;          // 进球数
}
```

### TableEntry (积分榜条目)

```typescript
interface TableEntry {
  teamInfoId: number;
  teamName: string;
  points: number;
  won: number;
  draw: number;
  lost: number;
  goals: number;
  opponentGoals: number;
  matches: number;
  goalDiff: number;
}
```

## 常用联赛 Shortcuts

| Shortcut | 联赛 |
|----------|------|
| `bl1` | 德甲 1. Bundesliga |
| `bl2` | 德乙 2. Bundesliga |
| `bl3` | 德丙 3. Liga |

## 注意事项

1. **赛季年份用赛季开始年**: 2024/25赛季 → `leagueSeason=2024`
2. **德甲 34轮, 德乙 34轮, 德丙 38轮**
3. **当前轮次自动切换**: 在上一轮最后一场和下一轮第一场时间的中点
4. **resultTypeID**: `1`=半场比分, `2`=全场比分 (跨联赛统一)
5. **缓存**: 使用 `getlastchangedate` 避免无意义轮询
6. **无需 API Key**: 所有端点公开可用
7. **teamFilterstring**: 支持部分队名匹配
