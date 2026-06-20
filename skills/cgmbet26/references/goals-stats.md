# Goals Statistics 模块 — 分钟概率网格

## 定位

基于ELO匹配的历史概率网格（分钟 x 市场），赛中核心工具

## 工作方式

1. 输入：联赛 + 主队 + 客队 + ELO容差(默认+-75)
2. 查找ELO相近的历史比赛
3. 输出：每个市场在每个分钟的概率

## 网格结构

- 行 = 市场（1X2 / O-U 0.5-4.5 / GG-NG / DC / 主客领先 / Correct Score / 精确进球数）
- 列 = 分钟 5/10/15/.../90 + Full T + Half T
- 值 = 历史满足条件占比%

## 读取方法

```
比赛30分钟比分0-0
→ 看"30 min"列
→ Full T列 O 2.5 = 41%
→ 赔率 > 2.44(1/0.41) → Value!
```

## 多Tab

最多10个标签页同时监控多场比赛

## 过滤控制

| 控制 | 选项 |
|------|------|
| ELO +/- | 开/关，范围设置 |
| Show | 百分比 / 隐含赔率 |
| Interval | 5/10/15/30/45分钟 |
| Between minutes | 自定义分钟范围 |
| Source | All seasons / Last N seasons |

## 底部控制

- Current minute：设置当前比赛分钟
- Market type：Correct Score / Home Leads / Draw / Away Leads / Handicaps / O-U / GG-NG
- Score spinners：设置当前比分
- Highlight if % between：高亮高概率格子（默认70-100%）
- Save/Load：99个配置槽

## 实用建议

- Games count < 30 → 放宽ELO范围(75→100/150)
- 同时开2个Tab对比：赛前(0分0-0) vs 当前实时
- 限制近期赛季(3-5)可能更准确
