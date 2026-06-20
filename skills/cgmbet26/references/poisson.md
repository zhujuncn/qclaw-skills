# Poisson 模块 — 单场泊松计算器

## 定位

快速手动 what-if 分析：输入xG → 输出所有市场概率

## 输入

| 控件 | 范围 | 默认 |
|------|------|------|
| Expected goals (Home) | 0.00-9.99, 精度0.01 | 1.70 |
| Expected goals (Away) | 0.00-9.99, 精度0.01 | 1.70 |
| Correction (Home) | -50% ~ +50% | 0% |
| Correction (Away) | -50% ~ +50% | 0% |

校正公式：Adjusted lambda = Expected Goals x (1 + Correction/100)

## 输出

### Table 1: Number of Goals
各队进0-9球的概率 + 隐含赔率

P(X=k) = (lambda^k x e^(-lambda)) / k!

### Table 2: Line and Totals
三组市场：

| 组 | 市场 | 计算方式 |
|----|------|---------|
| 1X2 | Home/Draw/Away | 联合概率P(h>a), P(h=a), P(h<a) |
| O-U | 0.5-4.5 | h+a超过/低于阈值 |
| GG-NG | GG/NG | GG = 1-P(h=0)-P(a=0)+P(0,0) |

每组显示 % + 公平赔率

### Table 3: Correct Score
0-0到4-4+所有比分，按概率从高到低排列
显示：比分 / % / 赔率

## 导航

从Upcoming右键 → "Open in Poisson" → 自动填入xG + 队名

## 校正用法

```
主队关键球员受伤 → xG 1.70, 校正 -20% → 1.36
客队客场虫 → xG 1.20, 校正 -10% → 1.08
→ 新概率分布反映真实战力
```

## 注意

赔率为零边际公平赔率，实际bookmaker赔率更低。
Value判断：bookmaker赔率 > Poisson公平赔率 → 可能有价值
