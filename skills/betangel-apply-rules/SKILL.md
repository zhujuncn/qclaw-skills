---
name: betangel-apply-rules
description: Bet Angel Guardian 自动化规则挂载技能。当用户需要将 Bet Angel automation 规则（.baf 文件）挂到一个或多个 Betfair 市场时使用。支持：单市场挂载、批量挂载（从 JSON candidates 文件）、验证执行结果（automation instances + bets 监控）、移除规则。触发词：挂规则、挂 BAF、apply rules、挂载自动化、Guardian 挂规则、把规则挂到市场、BAF 全部挂入。不适用于：创建/修改 .baf 规则文件本身、Betfair API 直接下注。
---

# Bet Angel Guardian — 自动化规则挂载

## API 基础

- **Host**: `http://localhost:9000`
- **Protocol**: POST, Content-Type: `application/json`
- **前提**: Bet Angel Professional 进程必须运行（`Get-Process BetAngel`）

## 核心流程（4 步）

### Step 1：确认前提条件

```powershell
# 检查 BetAngel 进程
Get-Process BetAngel | Select-Object Name, Id

# 检查现有 automation 实例（避免重复挂载）
Invoke-RestMethod -Uri "http://localhost:9000/api/automation/v1.0/getInstances" `
  -Method POST -Body '{}' -ContentType "application/json"
```

### Step 2：将市场加入 Guardian

```powershell
$body = '{"marketIds": ["1.XXXXXXXXX", ...]}'
Invoke-RestMethod -Uri "http://localhost:9000/api/guardian/v1.0/addMarkets" `
  -Method POST -Body $body -ContentType "application/json"
# 预期: {"status":"OK"}
```

### Step 3：挂载规则

```powershell
$body = '{
  "rulesFileName": "CODEX_BAF005_1RON",
  "marketsFilter": {"filter": "SPECIFIED_IDS", "ids": ["1.XXXXXXXXX"]},
  "guardianRulesColumn": 1
}'
Invoke-RestMethod -Uri "http://localhost:9000/api/guardian/v1.0/applyRules" `
  -Method POST -Body $body -ContentType "application/json"
# 预期: {"status":"OK"}
# 注意: guardianRulesColumn 必须为 1-5，缺失会报 INVALID_RULE_COLUMN
```

### Step 4：验证 + 监控

挂载后立即验证，见 `references/monitor.md`。如果 API 显示已挂载但 Bet Angel GUI 找不到规则，按 `references/gui-view.md` 检查 Guardian 列显示、Automation 实例窗口和列表刷新状态。

---

## 场景 A：单市场挂载

```
用户：把 CODEX_BAF005_1RON 挂到市场 1.259280819
```

1. 检查市场类型是否符合规则预期
2. 确认当前无重复实例
3. addMarkets → applyRules（column=1）
4. 验证 instances=1, status=PENDING

## 场景 B：批量挂载（从 candidates JSON）

```
用户：BAF005 全部挂入 <path>/BAF005_today_candidates.json
```

见 `references/batch-apply.md` 完整脚本。

## 场景 C：移除规则

见 `references/remove-rules.md`。

---

## 硬停止条件（必须遵守）

- ⛔ 如果 automation instances > 预期数量，立即停止并报警
- ⛔ 如果出现 matched 或 unmatched bets，立即停止并报告
- ⛔ 如果市场类型与规则不匹配，停止挂载
- ⛔ 挂到多个市场时，始终使用 `SPECIFIED_IDS` filter，绝不使用 `ALL`

## 规则文件路径

```
C:\Users\zhuju\AppData\Roaming\Bet Angel\Bet Angel Professional\Automation\
```

可用规则列表见 `references/rules-catalog.md`。
