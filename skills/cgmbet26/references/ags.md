# A.G.S. (Advanced Goals Statistics) — 最强研究工具

## 定位

深度历史研究 + 赛中条件分析 + 统计显著性检验

## 三区布局

- 左：配置面板（联赛/赛季/球队/ELO/排名/条件逻辑）
- 中：比赛网格 + 过滤工具栏
- 右：市场统计面板（Won/Won%/Odds/Yield/P-value）

## 左面板配置

### League/Team
选择联赛 + 主/客队

### Range
- 模式1：赛季范围（如 2020-2026）
- 模式2：日期范围（From-To）

### Teams & ELO
- 两种模式：Home and away team / One team
- ELO复选框：设置主/客队ELO范围

### Filters（排名过滤）
- Rank total：按总排名过滤（如 主1-6 vs 客1-6 = 前六对决）
- Rank H/A：按主场/客场排名过滤

### Condition Logic（条件逻辑，核心！）

6个条件(c1-c6)，4种组合模式：

| 模式 | 说明 |
|------|------|
| AND | 所有条件同时满足 |
| OR | 任一条件满足 |
| Custom | 自定义布尔表达式，如 (1 AND 2) OR 3 |
| Manual | 手写分钟+比分演进，如 "30112" = 30分钟比分2-1 |

每个条件的设置：
- Result下拉：比分/领先/净胜/O-U/GG-NG/首球/球队进球数
- Time mode：Between minutes（某分钟时的比分） / Anytime between（某时段内是否出现过）
- 分钟范围：From-To

### 条件示例
```
c1: "Home leads" Between 1-45
c2: "Draw" Between 1-90
逻辑: c1 AND c2 → 找"半场领先但最终平局"的比赛
```

## 右面板 — 市场统计

### 计算模式
- Between min：分析指定时段（默认1-90）
- Next min：从最高条件分钟起，后续N分钟的概率（赛中用）

### 市场分组

1X2 / Double Chance / DNB / Totals(0.5-6.5) / GG-NG / Odd-Even / HT-FT / Scored First / Correct Score / Goals Sequence

### 列定义

| 列 | 含义 |
|----|------|
| Won | 满足条件比赛数 |
| Won% | 胜率 |
| Odds | 平均bookmaker赔率（仅全场） |
| **Yield%** | 理论收益率（正=盈利） |
| **P-value** | 统计显著性（<5%=显著） |

**P-value 解读**：
- < 5% → 策略有效，非运气
- 5-10% → 弱证据
- > 10% → 不显著

### 交互
- 点击市场行 → 网格只显示该市场赢的比赛
- 点击Reset → 恢复全部

## 赛中功能（Live Game）

- 底部Live game下拉 → 选择正在进行的比赛
- 自动配置：联赛+球队+当前比分
- 自动刷新：15/30/60秒可选
- 实时更新所有市场概率

## Save/Load

99个槽，保存完整配置（联赛/赛季/球队/ELO/排名/条件逻辑/工具栏过滤/计算模式）
