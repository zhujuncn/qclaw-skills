# Advanced Poisson 模块 — 批量泊松回测引擎

## 定位

全联赛批量Poisson计算 + xG公式自定义 + Yield回测 = CGMBet最强分析引擎

## xG 公式构建器（核心创新）

### 公式语法

```
XY(V,M,RRRR)

X: H=主队, A=客队, L=联赛平均
Y: S=进球, C=失球
V: H=主场, A=客场, 空=所有
M: S=全赛季, 数字=近N场
RRRR: 4位分钟码, 0190=全场, 0145=半场
```

### 默认公式

```
Home: HS(H,S,0190) = 主队主场进球，全赛季，全场
Away: AS(A,S,0190) = 客队客场进球，全赛季，全场
```

### 自定义公式示例

```
HS(H,5,0190)               → 主队近5主场进球
(HS(H,5,0190)+LC(,S,0190))/2 → 主队近5主场进球 与 联赛场均失球 的均值
```

公式文本框可直接编辑

## 计算流程

1. 解析Home/Away公式
2. 对每场比赛，查询该比赛日期之前的历史数据
3. 计算各组件的场均进球 → 得到xG
4. 若公式有多个组件用+连接 → 取均值
5. 用xG作为Poisson分布lambda参数
6. 计算所有市场概率

## 调整模式

| 模式 | 说明 |
|------|------|
| No adjustments | 纯Poisson |
| Dixon-Coles | 修正低分平局(0-0,1-0,0-1,1-1)低估 |
| Zero-Inflation | 增加0-0概率 |

可选：排除异常值（>2标准差）

## 数据网格

### 固定列
Flag / League / Date/KO / Rd / Home Team / T(h) / Away Team / T(a) / Result / ExpG H / ExpG A

### 市场列（每组4列）

| 子列 | 含义 |
|------|------|
| % | Poisson概率 |
| O(C) | 理论公平赔率 = 1/概率 |
| O(R) | 实际bookmaker赔率 |
| **Value%** | **(O(R)/O(C)-1)x100**，正=Value |

可用市场组：1X2 / O-U(0.5-4.5) / GG-NG / Correct Scores

## 右侧面板

### Highlight
- Value 范围高亮（默认15-70%）
- Only if won：只在预测正确时高亮
- % 范围高亮（默认70-100%）

### Filters
- Results：All/Home Win/Draw/Away Win/特定O-U/GG-NG/CS
- %：All / Highlighted only
- Value：All / Value on any / Value on specific market

### Market Statistics
- 计算模式切换：All games / Value odds（只统计有Value的比赛）
- 每个市场显示：S(样本量) / HR(命中率%) / Y(Yield%)
- **关键：Value odds模式下Yield为正 → 历史上模型Value信号盈利**

## Backtest P-Value

底部按钮 → 统计显著性检验 → 验证预测是否有效

## Save/Load

99个槽，保存完整配置（联赛/公式/过滤/调整）
