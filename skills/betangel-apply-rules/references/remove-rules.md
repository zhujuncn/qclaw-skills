# 移除规则

## 从单个市场移除（清空某列）

```powershell
# 传空字符串 rulesFileName 来清空指定列
$body = '{
  "rulesFileName": "",
  "marketsFilter": {"filter": "SPECIFIED_IDS", "ids": ["1.XXXXXXXXX"]},
  "guardianRulesColumn": 1
}'
Invoke-RestMethod -Uri "http://localhost:9000/api/guardian/v1.0/applyRules" `
  -Method POST -Body $body -ContentType "application/json"
```

## 从所有当前 Guardian 市场移除某规则

```powershell
$ruleName = "CODEX_BAF005_1RON"

# 先获取所有挂了该规则的市场 ID
$inst = Invoke-RestMethod -Uri "http://localhost:9000/api/automation/v1.0/getInstances" `
  -Method POST -Body '{}' -ContentType "application/json"
$targets = $inst.result.instances | Where-Object { $_.rulesFileName -eq $ruleName } `
           | Select-Object -ExpandProperty marketId

if ($targets.Count -eq 0) { Write-Host "没有找到 $ruleName 的实例"; return }

Write-Host "将从 $($targets.Count) 个市场移除 $ruleName"

$body = @{
    rulesFileName = ""
    marketsFilter = @{ filter = "SPECIFIED_IDS"; ids = $targets }
    guardianRulesColumn = 1
} | ConvertTo-Json -Depth 5 -Compress

$r = Invoke-RestMethod -Uri "http://localhost:9000/api/guardian/v1.0/applyRules" `
  -Method POST -Body $body -ContentType "application/json"
Write-Host "Remove result: $($r.status)"

# 验证
Start-Sleep -Seconds 1
$inst2 = Invoke-RestMethod -Uri "http://localhost:9000/api/automation/v1.0/getInstances" `
  -Method POST -Body '{}' -ContentType "application/json"
$remaining = $inst2.result.instances | Where-Object { $_.rulesFileName -eq $ruleName }
Write-Host "剩余 $ruleName 实例: $($remaining.Count)"
```

## 注意

- 移除操作前先确认 bets 状态（matched/unmatched），有未结算下注时谨慎操作
- column 必须与挂载时一致（默认 column=1）
