# 挂载后验证与监控

## 即时验证（挂载后立即执行）

```powershell
$marketId = "1.XXXXXXXXX"
$ruleName = "CODEX_BAF005_1RON"

# 1. 检查 automation instances
$inst = Invoke-RestMethod -Uri "http://localhost:9000/api/automation/v1.0/getInstances" `
  -Method POST -Body '{}' -ContentType "application/json"
$ruleInst = $inst.result.instances | Where-Object { $_.rulesFileName -eq $ruleName }
Write-Host "Instances: $($ruleInst.Count)"
$ruleInst | ForEach-Object { Write-Host "  [$($_.status)] $($_.marketId) $($_.marketName)" }

# 2. 检查 bets
$bets = Invoke-RestMethod -Uri "http://localhost:9000/api/markets/v1.0/getMarketBets" `
  -Method POST -Body "{`"marketId`":`"$marketId`"}" -ContentType "application/json"
Write-Host "Matched: $($bets.result.matchedBets.Count) | Unmatched: $($bets.result.unmatchedBets.Count)"
```

## 持续监控循环（可选，120秒窗口）

```powershell
$marketId    = "1.XXXXXXXXX"
$expectedRule = "CODEX_BAF005_1RON"
$sw = [System.Diagnostics.Stopwatch]::StartNew()

while ($sw.Elapsed.TotalSeconds -lt 120) {
    $ts   = Get-Date -Format "HH:mm:ss"
    $inst = Invoke-RestMethod -Uri "http://localhost:9000/api/automation/v1.0/getInstances" `
              -Method POST -Body '{}' -ContentType "application/json"
    $bets = Invoke-RestMethod -Uri "http://localhost:9000/api/markets/v1.0/getMarketBets" `
              -Method POST -Body "{`"marketId`":`"$marketId`"}" -ContentType "application/json"

    $iCount  = $inst.result.instances.Count
    $matched = $bets.result.matchedBets.Count
    $unmatched = $bets.result.unmatchedBets.Count

    Write-Host "[$ts] Instances=$iCount | Matched=$matched | Unmatched=$unmatched"

    if ($matched -gt 0 -or $unmatched -gt 0) {
        Write-Host "⚠️ 检测到下注！立即停止并人工检查。"
        break
    }
    if ($iCount -eq 0) { Write-Host "ℹ️ 所有实例已消失（比赛结束或规则完成）"; break }

    Start-Sleep -Seconds 5
}
```

## Instance 状态说明

| 状态 | 含义 |
|------|------|
| `PENDING` | 规则已挂载，等待触发条件满足 |
| `RUNNING` | 规则正在执行 |
| `COMPLETED` | 规则已完成（可能已下注） |
| `FAILED` | 规则执行失败 |

## getMarkets 快速查询

```powershell
$body = '{"dataRequired":["ID","NAME","MARKET_TYPE","MARKET_INPLAY_STATUS"]}'
$r = Invoke-RestMethod -Uri "http://localhost:9000/api/markets/v1.0/getMarkets" `
  -Method POST -Body $body -ContentType "application/json"
# 注意：数据在 $r.result.markets，不是 $r.markets
$r.result.markets | Where-Object { $_.id -eq "1.XXXXXXXXX" }
```
