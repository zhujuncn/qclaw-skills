# Rating V 模块 — 经验频率概率 + 价值信号

## 定位

基于经验频率（非Poisson模型）的概率计算，查找历史相似比赛直接统计胜率

## 与Poisson的区别

| | Rating V | Poisson |
|--|---------|---------|
| 方法 | 查历史相似比赛→统计实际胜率 | 假设泊松分布→计算理论概率 |
| 优势 | 无模型假设 | 可外推 |
| 劣势 | 样本少时不稳定 | 低分平局低估 |

## 计算流程

1. 查找同联赛+比赛日期之前的历史比赛
2. 应用过滤（ELO范围/Form范围/Odds范围）
3. 统计主队主场进球分布 + 客队客场进球分布
4. 构建比分概率矩阵
5. 推导所有市场概率

## ELO过滤

- 相对过滤：主队ELO=1500, 范围=+-75 → 只看1425-1575的历史比赛
- 确保比较的是相似实力的队伍

## 数据网格

### 固定列
Flag / League / Date/KO / Rd / Home / T(h) / Away / T(a) / Result / Sample / ELO H-A / Form H-A

### 市场列（每组2列）

| 子列 | 含义 |
|------|------|
| % | 计算概率 |
| O | 实际bookmaker赔率 |

可用市场：1X2 / O-U(0.5-4.5) / GG-NG

## 右侧 — Highlight & Show

### Sample Size Filter
Highlight only if sample >= 100（默认）

### Percentage Highlighting
% between 70-100% → 黄格

### Back Value Highlighting（蓝格）
```
Value% = 100 x (O(R) - O(C)) / O(R)
O(R) > O(C) → 正Value → 蓝格 → 支持 BACK
默认范围：15-70%
```

### Lay Value Highlighting（粉格）
```
O(R) < O(C) → 负Value → 粉格 → 支持 LAY
默认范围：-70% ~ -15%
```

### Legend
- 黄 = %在范围内
- 蓝 = Back value（赔率高于公平赔率）
- 粉 = Lay value（赔率低于公平赔率）

## 实用建议

- 大样本(100+)优先，低样本(<30)不可靠
- ELO范围越窄越精确但样本越小
- 同时看%高 + Value大 = 高概率+好赔率
- Backtest & P-value 验证策略显著性
