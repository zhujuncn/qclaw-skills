# AI Export 模块 — 数据导出给外部AI

## 定位

把CGMBet数据导出为结构化文本 → 粘贴到ChatGPT/Gemini等做综合分析

## 分析类型

| 类型 | 说明 | 限制 |
|------|------|------|
| Single Match Analysis | 单场详细统计 | 最全面 |
| Multiple Matches | 日/周预览 | 最多25场 |
| League Overview | 联赛总览 | 全联赛统计 |

## 可导出数据

| 选项 | 内容 |
|------|------|
| Home/Away Specific Form | 主客场分别表现 |
| Head-to-Head History | 交锋记录 |
| League Standings | 排名+积分 |
| Goals Scored/Conceded Averages | 进球/失球场均 |
| Over/Under Rates | O 1.5/2.5/3.5 率 |
| BTTS | 双方进球率 |
| Clean Sheet Percentages | 零封率 |
| Betting Odds | 1X2/O2.5/BTTS赔率 |
| Poisson Projections | xG + 比分概率 |
| Goal Timing Patterns | 15分钟间隔进球时段 |
| Corner Statistics | 角球统计 |

## 分析深度

- Recent Form Matches: Last 3/5/10/All Season
- H2H History: Last 3/5/10/All Time

## 输出格式

- Structured Text（推荐，AI最易解析）
- CSV
- Markdown

## AI Prompt Template

默认prompt要求AI提供：
1. 比赛结果预测 + 置信度
2. O/U 2.5预测 + 理由
3. BTTS预测
4. 关键影响因素
5. 基于赔率的价值投注

## 工作流

```
1. 选分析类型 + 比赛
2. 调数据选项
3. Copy to Clipboard
4. 粘贴到AI助手
5. 保存AI回答到Save/Load的AI Answer区
```

## 实用建议

- 多场比赛模式建议<10场（避免超出AI上下文）
- 包含Poisson Projections给AI更多量化参考
- Save/Load 99个配置槽，Slot 1自动加载
