# 批量挂载规则（从 candidates JSON）

## 输入格式

candidates JSON 文件结构（由 daily-news-briefing 或扫描器生成）：

```json
{
  "rule": "CODEX_BAF005_1RON",
  "rows": [
    {"marketId": "1.259259287", "marketName": "...", "marketType": "OVER_UNDER_25", ...},
    ...
  ]
}
```

## 批量挂载脚本

```powershell
# 参数
$jsonPath  = "<path>/BAF005_today_candidates.json"
$ruleName  = "CODEX_BAF005_1RON"
$column    = 1

# 读取候选市场
$json      = Get-Content $jsonPath | ConvertFrom-Json
$marketIds = $json.rows | Select-Object -ExpandProperty marketId
Write-Host "候选市场总数: $($marketIds.Count)"

# Step 1: 批量加入 Guardian
$addBody = @{ marketIds = $marketIds } | ConvertTo-Json -Compress
$r1 = Invoke-RestMethod -Uri "http://localhost:9000/api/guardian/v1.0/addMarkets" `
  -Method POST -Body $addBody -ContentType "application/json"
Write-Host "AddMarkets: $($r1.status)"

# Step 2: 批量应用规则
$applyBody = @{
    rulesFileName = $ruleName
    marketsFilter = @{ filter = "SPECIFIED_IDS"; ids = $marketIds }
    guardianRulesColumn = $column
} | ConvertTo-Json -Depth 5 -Compress

$r2 = Invoke-RestMethod -Uri "http://localhost:9000/api/guardian/v1.0/applyRules" `
  -Method POST -Body $applyBody -ContentType "application/json"
Write-Host "ApplyRules: $($r2.status)"

# Step 3: 验证
Start-Sleep -Seconds 2
$inst = Invoke-RestMethod -Uri "http://localhost:9000/api/automation/v1.0/getInstances" `
  -Method POST -Body '{}' -ContentType "application/json"
$ruleInst = $inst.result.instances | Where-Object { $_.rulesFileName -eq $ruleName }
Write-Host "Instances for ${ruleName}: $($ruleInst.Count)"
$ruleInst | Group-Object status | ForEach-Object { Write-Host "  $($_.Name): $($_.Count)" }
```

## 注意事项

- `addMarkets` 幂等，重复调用安全
- `applyRules` 会覆盖该列已有规则，请确认 column 使用正确
- 如 candidates 中含已过期市场（startTime < now），Guardian 可能忽略，不影响其他市场
- 建议挂载前先运行 `getInstances` 确认无重复
