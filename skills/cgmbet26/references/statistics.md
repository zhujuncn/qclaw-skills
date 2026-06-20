# Statistics 模块 — 跨联赛/跨球队统计面板

## 功能

- 全联赛/全球队跨维度统计
- 两个Tab：Leagues（联赛级） / Teams（球队级）
- 共享底部过滤器

## 三种显示模式（核心！）

| 模式 | 含义 | 用途 |
|------|------|------|
| **Percentages** | 标准概率 | 基础分析 |
| **Positive Streaks** | 当前连续X场满足条件 | 找"热点"趋势 |
| **Negative Streaks** | 当前连续X场不满足 | 找"回归"机会 |

### 连续模式示例

- Over 2.5 正向连续=7 → 近7场全Over 2.5 → 热点持续
- Over 2.5 负向连续=5 → 近5场全Under → 回归概率升高 → Value出现

## 可用列

Won / Drawn / Lost / O 0.5-4.5 / U 0.5-4.5 / GG / NG / G Sco / G Con / Sco 1st / Con 1st / No Goals

Teams Tab 额外列：Team / Next Opponent / Sco(进球率) / Con(失球率)

## 过滤器

| 过滤器 | 选项 |
|--------|------|
| 场地 | All / Home / Away |
| 赛季 | 当前 / 近2 / 全部 / 近5场 / 近10场 / 近30天 / 近60天 |
| 分钟 | 1-90（自定义） |
| 联赛 | 下拉选择 / All Leagues |
