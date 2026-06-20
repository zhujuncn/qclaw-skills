# Guardian GUI 查看步骤

当 `applyRules` 返回 `OK` 且 `getInstances` 能看到规则实例，但 Bet Angel GUI 里找不到规则时，按这个顺序检查。Bet Angel 的 GUI 状态和 localhost API 状态可能不同步；以 API 的 `getInstances` 作为挂载事实，以 GUI 作为人工确认界面。

## 1. 先确认 API 事实

```powershell
$ruleName = "CODEX_BAF006_1RON"
$inst = Invoke-RestMethod -Uri "http://localhost:9000/api/automation/v1.0/getInstances" `
  -Method POST -Body '{}' -ContentType "application/json"
$inst.result.instances |
  Where-Object { $_.rulesFileName -eq $ruleName } |
  Select-Object status, marketId, marketName, guardianRulesColumn, rulesFileName |
  Format-Table -AutoSize
```

确认重点：

- `rulesFileName` 是目标规则，例如 `CODEX_BAF006_1RON`
- `guardianRulesColumn` 是实际列号，例如 `2`
- `status` 通常应为 `PENDING`
- 实例数量应等于本次候选市场数量，除非部分市场已过期或被 Bet Angel 忽略

## 2. Guardian 主表查看

1. 打开 Bet Angel Professional。
2. 切到 `Guardian` 页面。
3. 确认当前 Guardian 列表不是空的；如果列表为空，先点击刷新或重新加载 Watch List/Coupon。
4. 在 Guardian 表格里找到任一候选市场，例如通过市场名称或 marketId 对应的比赛名查找。
5. 查看 automation 规则列：
   - `Rules 1` / `Automation Rules 1` 对应 `guardianRulesColumn = 1`
   - `Rules 2` / `Automation Rules 2` 对应 `guardianRulesColumn = 2`
   - 如果表格只显示第一列规则，右键表头或打开列设置，把第 2 规则列显示出来
6. 如果同一市场已经在 `column 1` 挂了 `CODEX_BAF005_1RON`，而本次把 `CODEX_BAF006_1RON` 挂到 `column 2`，GUI 中应在两个不同规则列分别看到它们。

## 3. Automation 实例窗口查看

如果 Guardian 主表没有显示 column 2：

1. 在 Bet Angel 中打开 Automation/Servants/Rules 实例相关窗口。
2. 查找规则名 `CODEX_BAF006_1RON`。
3. 对照 API 输出的 `marketName` 和 `status`。
4. 如果实例窗口有过滤器，清除规则名、状态、市场、仅显示运行中等过滤条件。

## 4. 刷新和视图问题

如果 API 显示实例存在但 GUI 看不到：

- 点击 Guardian 列表刷新。
- 切换到其他页面再回到 Guardian。
- 检查 Guardian 当前 Watch List/Coupon 是否包含这些市场。
- 检查表格列设置是否隐藏了 Rules 2/Automation Rules 2。
- 检查是否按状态、开始时间、市场名或仅显示活动市场做了过滤。
- 不要用 `ALL` 重新挂载；仍然使用 `SPECIFIED_IDS`。

## 5. 辅助定位某个市场

可让 Bet Angel 直接显示一个市场，帮助在 GUI 里定位：

```powershell
$marketId = "1.259177749"
$body = @{
  marketId = $marketId
  displayChoice = "MAIN_LADDER"
  activateWindow = $false
} | ConvertTo-Json -Compress

Invoke-RestMethod -Uri "http://localhost:9000/api/guardian/v1.0/displayMarket" `
  -Method POST -Body $body -ContentType "application/json"
```

然后回到 Guardian，用该市场名称检查 `Rules 2` 是否显示目标规则。

## 6. 何时重新执行 applyRules

只有在以下情况才重新执行：

- API 中目标规则实例数量为 0 或小于候选市场数量
- `guardianRulesColumn` 与预期列不同
- `rulesFileName` 与预期规则不同

如果 API 中数量、规则名、列号都正确，优先排查 GUI 列显示、列表刷新和过滤器，而不是重复挂载。
