# Calculators 模块 — 投注计算器套件

## 9个计算器

### 1. P-value Calculator（策略验证核心）

4个子Tab：

| 子Tab | 用途 |
|-------|------|
| Load & Analyse | 导入CSV历史 → 自动计算各市场P-value |
| P-value Test | 输入Sample/Won/Avg Odds → P-value + ELS |
| Manual Input | 快速P-value计算（直接输入或从赔率计算） |
| Educational | P-value概念教学 |

P-value解读：

| P-value | 含义 | 标记 |
|---------|------|------|
| > 10% | 不显著（运气） | - |
| 5-10% | 弱证据 | * |
| 1-5% | 显著 | ** |
| 0.1-1% | 非常显著 | *** |
| < 0.1% | 高度显著 | **** |

ELS（Expected Losing Sequence）：平均最长连败 → 建议3xELS做资金储备

CSV必需列：HomeGoals, AwayGoals + 各市场赔率列

### 2. Hedged Dutch Betting
- 最多10个选择
- 主选=盈利 / 次选=保本
- 两种分配：标准Dutch / 对冲Dutch

### 3. Back / Lay Arbitrage
- 比较Back vs Lay策略
- 输入：Back Odds / Lay Odds / 选择 / 金额
- 输出：最优策略 + 利润

### 4. DNB & Double Chance
- 从1X2赔率推导DNB和双机会赔率
- DNB：赢则盈利，平则退本
- Double Chance：1X / X2 / 12

### 5. Asian Handicap
- 整数/半球/半球盘计算
- 四分之一盘：注金分拆两线
- 输入最终比分看盈亏

### 6. Arbitrage
- 最多10个选择
- 三种策略：Single Bet / Equal Profit / Free Bet
- 条件：sum(1/Odds) < 1.0

### 7. Kelly Criterion（资金管理核心）

| 输入 | 说明 |
|------|------|
| Bankroll | 总资金 |
| Decimal Odds | 赔率 |
| Win Probability | 真实概率估计 |
| Fractional Kelly | 1.0=全/0.5=半/0.25=四分 |

输出：Kelly% / 推荐注额 / 期望值 / Edge

**始终用Half(0.5)或Quarter(0.25) Kelly！Full Kelly波动太大**

### 8. Odds Converter
6种格式互转：Decimal / Fractional / American / Hong Kong / Indonesian / Malay
+ 隐含概率显示

### 9. Parlay Calculator
- 最多20腿
- 输入：Stake + 各腿赔率
- 输出：Combined Odds / Total Return / Profit / 隐含胜率
