# Bet Angel API 快速参考

Base URL: `http://localhost:9000`

## Guardian 端点

### addMarkets
```
POST /api/guardian/v1.0/addMarkets
Body: {"marketIds": ["1.XXXXXXXXX", ...]}
Response: {"status":"OK"}
```
幂等，可重复调用。

### applyRules（挂载/移除规则）
```
POST /api/guardian/v1.0/applyRules
Body: {
  "rulesFileName": "CODEX_BAF005_1RON",   // 空字符串 = 移除
  "marketsFilter": {
    "filter": "SPECIFIED_IDS",             // 必须用此值，不要用 ALL
    "ids": ["1.XXXXXXXXX", ...]
  },
  "guardianRulesColumn": 1                 // 必填，1-5
}
Response: {"status":"OK"}
常见错误: INVALID_RULE_COLUMN（缺少 guardianRulesColumn）
```

### applyCoupon（加载 Coupon 到 Watch List）
```
POST /api/guardian/v1.0/applyCoupon
Body: {"couponName": "FT", "watchListNumber": 1, "clearOption": "CLEAR_WATCH_LIST_ONLY"}
```

## Automation 端点

### getInstances
```
POST /api/automation/v1.0/getInstances
Body: {}
Response: {
  "status": "OK",
  "result": {
    "instances": [{
      "id": 1,
      "status": "PENDING",
      "rulesFileName": "CODEX_BAF005_1RON",
      "marketId": "1.XXXXXXXXX",
      "marketName": "...",
      "instanceType": "GUARDIAN",
      "guardianRulesColumn": 1,
      "timeCreated": "2026-06-20T03:17:02..."
    }]
  }
}
```

### startAutomationServant（单市场直接启动）
```
POST /api/automation/v1.0/startAutomationServant
Body: {
  "marketId": "1.XXXXXXXXX",
  "rulesFileName": "CODEX_BAF005_1RON",
  "contextSelectionId": "XXXXXXX",  // 可选
  "contextPrice": 1.72               // 可选
}
```

## Markets 端点

### getMarkets
```
POST /api/markets/v1.0/getMarkets
Body: {"dataRequired": ["ID","NAME","MARKET_TYPE","MARKET_INPLAY_STATUS","MARKET_START_TIME"]}
Response: {"status":"OK", "result": {"markets": [...]}}  // 注意：数据在 result.markets
```

### getMarketBets
```
POST /api/markets/v1.0/getMarketBets
Body: {"marketId": "1.XXXXXXXXX"}
Response: {
  "status":"OK",
  "result": {
    "matchedBets": [],
    "unmatchedBets": []
  }
}
```

### getBalance
```
POST /api/markets/v1.0/getBalance
Body: {}
Response: {"status":"OK", "balance": 690.73}
```
