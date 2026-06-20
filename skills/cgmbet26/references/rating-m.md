# Rating M 模块 — 单场条件分析

## 定位

单场比赛深度分析 + 可手动调整概率 + 赛中条件概率计算

## 与Rating V的区别

- Rating V：批量分析多场比赛
- Rating M：单场深度分析 + 手动调概率 + 条件场景

## Tab管理

最多10个Tab同时监控，每个独立配置
Live比赛自动刷新30秒

## 左面板 — 进球概率分布

### Goal Percentage Spinners
- 10行：各队进0-9球的概率
- 动态排序（概率最高在最上）
- **可手动编辑** → 所有市场实时重算
- Totals行：各列总和应为100%

### Most Probable Correct Scores
Top 10最可能比分 + 概率 + 隐含赔率

## 右面板 — 市场计算

### 市场分组
1X2 / Double Chance / Totals(0.5-4.5) / GG-NG / Correct Score

### 列
| 列 | 含义 |
|----|------|
| % | 计算概率 |
| Calc Odds | 公平赔率 = 100/% |
| Real Odds | 实际bookmaker赔率（绿=Value） |

## 底部 — 条件分析（赛中核心）

| 控制 | 说明 |
|------|------|
| Current minute | 0-90，>0时启用条件过滤 |
| Market type | Correct Score / Home Leads / Draw / Away Leads / Handicaps / O-U / GG-NG |
| Score spinners | 仅Correct Score模式显示 |

### 条件分析示例
```
Minute=60, Market=Draw, Score=1-1
→ 只看"60分钟时1-1"的相似ELO历史比赛
→ 统计剩余30分钟各市场概率
→ 判断下半场是否有Value
```

## 计算方式

1. 查询同联赛+比赛日前历史比赛
2. ELO过滤（若启用）
3. 条件过滤（若minute>0）
4. 统计"Between minutes"范围的进球分布
5. 构建10x10比分矩阵
6. 推导所有市场概率

## 实用建议

- Calc Odds vs Real Odds：绿格=Value
- 手动调概率测试what-if场景
- Between minutes设46-90分析下半场
- Games < 20 → 放宽ELO或增加赛季
