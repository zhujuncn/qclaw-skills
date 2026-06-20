# Football Match Monitor Skill

监控足球比赛比分和 Betfair 交易所 Cash Out 变化，用于交易决策。

## 使用场景

- 监控比赛进球并及时 Cash Out
- 追踪比赛状态变化
- 爆仓预警

## 参数

用户需提供：
- `matchUrl`: Betfair 比赛页面 URL
- `layOdds`: 持仓的 Lay 赔率
- `stake`: 投资金额 (liability)
- `side`: 投注方向 (home/away)

## 执行步骤

1. **browser navigate** 到比赛页面
2. **等待 5 秒** 加载
3. **browser snapshot** 提取:
   - 比赛时间(分钟)
   - 比分
   - 比赛状态
4. **browser evaluate** 提取 Cash Out 面板文字
5. **判断输出**:
   - 有比分变化 → 输出 ⚽ GOAL! + Cash Out 建议
   - 比赛结束 → 输出最终结果
   - 无变化 → 输出简短状态

## Cash Out 逻辑

- **客队进球** → Cash Out 暴涨 → 立即建议 Cash Out
- **主队进球** → Cash Out=0 → 爆仓警告
- **0-0 保持** → 继续等待

## 输出格式

直接输出文本，不要调用 message 工具。包含：
- 当前比赛时间
- 实时比分
- Cash Out 金额
- 建议操作
