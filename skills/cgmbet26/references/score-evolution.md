# Score Evolution 模块 — 比分演进可视化

## 定位

比分树的图形化展示，分析比分最可能的走向（与Goals Statistics的静态概率表互补）

## 4个可视化Tab

### Tab 1: Graphical Tree
- 彩色分支树状图
- 节点：比分 + 概率 + 累计概率
- 颜色：绿=主队进球，蓝=客队进球，橙=平局
- 顶部摘要栏：1X2 / O-U / GG-NG 概率
- 底部：比分概率排名条

### Tab 2: Tree View
- 文字版可折叠树
- 每行：比分徽章 + 转移概率(隐含赔率) + 累计概率
- 底部：最可能的3条路径（如 (0-0)->(0-1)->(0-1) NG 14.99%）

### Tab 3: Diagram - Main Path
- 钻石/格子布局
- 只显示最可能路径（粗绿线连接）
- NG终端 = 比分不再变化

### Tab 4: Diagram - Full
- 完整分支树（可很大）
- 缩放控制：-/+/Reset/Ctrl+Scroll

## 右侧结果面板

- 计算模式：Between min / Next min
- 市场分组：1X2 / DC / DNB / Totals / GG-NG / Odd-Even / HT-FT / Scored First / Correct Score
- 列：Market / Won / Won% / Odds / Yield / P-value

## 过滤控制

- 左侧独立过滤面板：ELO / ELO diff / Form / Form diff / Last N seasons / Same league only / Between minutes / Initial score
- 右侧：ELO / Form / Odds 弹出过滤

## 底部控制

- Current minute spinner
- Market type + Score spinners
- Auto refresh（默认开启，15秒）

## 实用建议

- 从Graphical Tree开始获取全局概览
- Tree View查看精确数字
- 比赛中最可能3条路径快速判断
- ELO+Form+Odds组合过滤使预测更相关
