# Upcoming 模块 — 比赛中心（核心工作区）

## 概览

- 左侧：比赛网格 | 右侧：系统Tabs面板（27自定义列）
- 顶部：联赛/状态/时段/ELO/Form/赔率/统计过滤器
- 底部：Backtest & P-value / Check My Alerts / Export

## 系统 Tabs（27自定义列）

每个Tab配置：
1. **State**: Enabled/Disabled
2. **Team**: Home/Away
3. **Type**: Select a market / Custom（公式编辑器，VIP Plus）
4. **Market**: Won/Drawn/Lost/O-U/GG-NG/Scored/Conceded/Points/Shots等
5. **Range**: 当前赛季/近X场/近X赛季/全部
6. **Game type**: All/Home/Away
7. **Time period**: Full time/1st Half/2nd Half/Between minutes
8. **Highlight**: >= / <= / between / not between / if true / if false
9. **Highlight only if games >= N**: 最小样本量过滤

### 配置步骤

```
1. 点击Tab编号 → State改为Enabled
2. 输入Header名称
3. 选Market（如 Won）
4. 设Range（如近5场 Home games Between 1-45分钟）
5. 设Highlight（如 >= 60%, games >= 3）
6. 点击 Calculate
```

### 自定义公式语法（VIP Plus）

```
XY(V,M,RRRR)
X = H(主队)/A(客队)/L(联赛)
Y = S(进球)/C(失球)
V = H(主场)/A(客场)/空(所有)
M = S(全赛季)/数字(近N场)
RRRR = 0190(全场)/0145(半场)/...

示例：HS(H,5,0190) = 主队近5主场进球，全场
```

## Save/Load System

99个配置槽，保存所有27 Tab设置。切换策略快速加载。

## 右键菜单快速跳转

H2H / Tables / Goals / Score Evolution / A.G.S. / Rating M / Poisson

## Alerts Manager

99个预警槽，每个含：主队条件 + 客队条件 + 赔率条件
- 全部AND逻辑
- 触发后在Upcoming和Daily Briefing展示
- Combine Settings：合并多个简单Alert为复杂Alert
