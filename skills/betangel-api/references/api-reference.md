# Bet Angel API Reference

Sources used to build this reference:

- Official guide: `https://www.betangel.com/api-guide/`
- Local example: `C:\Program Files (x86)\Bet Angel Limited\Bet Angel - Professional\api\javascript_example\index.html`
- Local request builders: `C:\Program Files (x86)\Bet Angel Limited\Bet Angel - Professional\api\javascript_example\index.js`

## Connection Model

Enable the API in Bet Angel Settings > Bet Angel API. Default address: `http://localhost:9000`.

Every call is a `POST` to:

```text
http://{host}:{port}/api/{component}/v1.0/{operationName}
```

Components:

- `markets`: markets loaded into Bet Angel, prices, bet info, balance.
- `guardian`: Guardian market management, coupons, rules, nominated selections, trading windows.
- `automation`: automation instances, rules file names, stored values, servants.
- `betting`: place, modify, cancel, green, and close trades.

Common response shape:

```json
{"status":"OK","result":{}}
```

Other statuses include `FAILED`, `PENDING`, and `PROCESSED_WITH_ERRORS`. Errors normally contain `code` and `msg`.

## Filters

ID filter:

```json
{"filter":"ALL"}
```

```json
{"filter":"SPECIFIED_IDS","ids":["1.23456789"]}
```

Market bet filter:

```json
{"option":"ALL"}
```

```json
{"option":"ALL_MATCHED"}
```

```json
{"option":"ALL_UNMATCHED"}
```

```json
{"option":"SPECIFIED_BET_REFS","betRefs":["123456789"]}
```

Stored value filter:

```json
{"storedValueFilter":"ALL"}
```

```json
{"storedValueFilter":"SPECIFIED_NAMES","names":["STAKE","MIN_PRICE"]}
```

Add `excludeSharedValues: true` for instance-only search, or `excludeInstanceValues: true` for shared-only search.

## Markets

Base URL: `/api/markets/v1.0/{operationName}`

Operations:

- `getBalance`: body `{}`. Returns Betfair account balance as last updated by Bet Angel.
- `getMarkets`: returns market metadata and optional selections.
- `getMarketPrices`: returns price/profit/bet-summary data for loaded markets.
- `getMarketBets`: returns matched/unmatched bets for one market.

Common `getMarkets` body:

```json
{
  "dataRequired": [
    "ID",
    "NAME",
    "MARKET_START_TIME",
    "EVENT_ID",
    "EVENT_TYPE_ID",
    "MARKET_TYPE",
    "SELECTION_IDS",
    "SELECTION_NAMES"
  ]
}
```

Common `getMarketPrices` data items:

- `BEST_PRICE_ONLY`
- `BEST_THREE_PRICES`
- `BEST_SIX_PRICES`
- `BEST_TEN_PRICES`
- `INPLAY_INFO`
- `LAST_TRADED_PRICE`
- `SP`
- `VOLUME`
- `PROFIT`
- `CLOSE_TRADE_PROFIT`
- `GREENING_PROFIT`
- `UNMATCHED_BET_SUMMARY`
- `MATCHED_BET_SUMMARY`

Example:

```json
{"dataRequired":["BEST_THREE_PRICES","LAST_TRADED_PRICE","VOLUME","PROFIT"]}
```

`getMarketBets` example:

```json
{"marketId":"1.214607388","filter":{"option":"ALL_UNMATCHED"}}
```

## Guardian

Base URL: `/api/guardian/v1.0/{operationName}`

Operations:

- `addMarkets`: add Betfair market IDs to Guardian.
- `removeMarkets`: remove all or specified markets, optionally by status.
- `getCoupons`: list available Guardian coupons.
- `applyCoupon`: apply a coupon to Guardian/watch list.
- `applyRules`: apply a Guardian automation rules file.
- `removeRules`: remove rules from a Guardian automation column.
- `getNominatedSelections`: read Guardian nominated selections.
- `setNominatedSelections`: set or clear nominated selections.
- `displayMarket`: show a loaded market on a trading screen/window.
- `getTradingWindows`: list active trading windows.
- `closeTradingWindow`: close a one-click or ladder window.

Examples:

```json
{"marketIds":["1.23456789","1.23456790"]}
```

```json
{
  "couponName": "Ex: HR - UK - Win & Place - 2 column",
  "clearOption": "CLEAR_GUARDIAN_AND_WATCH_LIST",
  "watchListNumber": 1
}
```

```json
{
  "rulesFileName": "Place Bet Based on Stored Values",
  "marketsFilter": {"filter":"ALL"},
  "guardianRulesColumn": 1
}
```

```json
{
  "marketId": "1.23456789",
  "displayChoice": "NEW_LADDER_WINDOW",
  "activateWindow": true
}
```

Display choices include `MAIN_ONE_CLICK`, `MAIN_LADDER`, `NEW_ONE_CLICK_WINDOW`, `NEW_LADDER_WINDOW`, `SPECIFIC_ONE_CLICK_WINDOW`, and `SPECIFIC_LADDER_WINDOW`.

## Automation

Base URL: `/api/automation/v1.0/{operationName}`

Operations:

- `getRulesFileNames`: list automation rules files.
- `getInstances`: list Guardian/Servant automation instances.
- `getStoredValues`: retrieve stored values.
- `setStoredValues`: set stored values at Bet Angel, event, market, or selection level.
- `clearStoredValues`: clear stored values using the same search fields as `getStoredValues`.
- `startAutomationServant`: start a servant on a market shown on a trading screen.
- `stopAutomationServant`: stop a servant by instance ID.

`getInstances` examples:

```json
{"includeStoppedInstances":true}
```

```json
{
  "includeStoppedInstances": true,
  "restrictToTypes": ["SERVANT","SAFETY_SERVANT"]
}
```

```json
{
  "includeStoppedInstances": true,
  "fromId": 1,
  "toId": 1000,
  "marketsFilter": {"filter":"SPECIFIED_IDS","ids":["1.23456789"]}
}
```

Stored values use `{ "n": "NAME", "v": 12.34 }` for numeric values and `{ "n": "NAME", "t": "text" }` for text values.

Set shared selection-level stored values:

```json
{
  "writeToMarketLog": true,
  "markets": [
    {
      "id": "1.206990738",
      "selections": [
        {
          "id": "7450122",
          "sharedValues": [
            {"n":"STAKE","v":10},
            {"n":"MIN_PRICE","v":4}
          ]
        }
      ]
    }
  ]
}
```

Get all stored values:

```json
{
  "marketsFilter": {"filter":"ALL"},
  "selectionsFilter": {"filter":"ALL"},
  "storedValueFilterBetAngelLevel": {"storedValueFilter":"ALL"},
  "storedValueFilterEventLevel": {"storedValueFilter":"ALL"},
  "storedValueFilterMarketLevel": {"storedValueFilter":"ALL"},
  "storedValueFilterSelectionLevel": {"storedValueFilter":"ALL"}
}
```

Start servant:

```json
{
  "marketId": "1.23456789",
  "rulesFileName": "My Servant",
  "contextSelectionId": "12345",
  "contextPrice": 2.0,
  "contextBackStake": 10,
  "contextLayStake": 10
}
```

Stop servant:

```json
{"id":1}
```

## Betting

Base URL: `/api/betting/v1.0/{operationName}`

Operations:

- `placeBets` and `getPendingPlaceBetsResult`
- `modifyBets` and `getPendingModifyBetsResult`
- `cancelBets` and `getPendingCancelBetsResult`
- `greenAllSelections` and `getPendingGreenAllSelectionsResult`
- `closeTrade` and `getPendingCloseTradeResult`

Live-safety rule: do not execute these calls without explicit user approval for the market, selection, side, stake/liability, price, and whether the call should be async.

Place bets:

```json
{
  "marketId": "1.214607388",
  "globalSettings": {"action":"NONE"},
  "async": false,
  "betsToPlace": [
    {"selectionId":"47999","type":"LAY","bspBetType":"NOT_BSP","price":1.10,"stake":10.0}
  ]
}
```

Global settings actions include `NONE`, `OFFSET`, `OFFSET_AND_STOP`, `OFFSET_AND_TRAILING_STOP`, `OFFSET_WITH_GREENING`, `OFFSET_WITH_GREENING_AND_STOP`, `OFFSET_WITH_GREENING_AND_TRAILING_STOP`, and `STOP_ON_OPENING_BET`.

Offset/stop/fill-or-kill fields:

```json
{
  "action": "OFFSET_WITH_GREENING_AND_STOP",
  "offsetTicks": 3,
  "offsetBatches": 1,
  "stopTriggerTicks": 4,
  "stopPlacementTicks": 7,
  "useFillOrKill": true,
  "killDelay": 2
}
```

Modify bets:

```json
{
  "marketId": "1.214607388",
  "async": false,
  "betsToModify": [
    {"betRef":"313259260005","newStake":12.67},
    {"betRef":"313259260006","newPrice":1.15}
  ]
}
```

Cancel bets:

```json
{
  "marketId": "1.214607388",
  "filterOption": "SPECIFIED_BET_REFS",
  "betRefs": ["313259260007"],
  "type": "ALL",
  "async": false
}
```

`filterOption`: `ALL`, `SPECIFIED_BET_REFS`, `SPECIFIED_SELECTION_IDS`.
`type`: `ALL`, `BACK_ONLY`, `LAY_ONLY`.

Green all selections:

```json
{
  "marketId": "1.214607388",
  "priceOption": "BEST_MARKET_PRICE",
  "async": false
}
```

Close trade:

```json
{
  "marketId": "1.214607388",
  "selectionId": "47999",
  "withGreening": true,
  "priceOption": "FIXED_PRICE",
  "fixedPrice": 2.0,
  "async": false
}
```

Other close-trade price options include `BEST_PRICE`, `SECOND_BEST_PRICE`, `THIRD_BEST_PRICE`, `REVERSE_PRICE`, `SECOND_REVERSE_PRICE`, `THIRD_REVERSE_PRICE`, `TICKS_ABOVE_BEST_PRICE`, `TICKS_BELOW_BEST_PRICE`, `TICKS_ABOVE_REVERSE_PRICE`, `TICKS_BELOW_REVERSE_PRICE`, `PERC_ABOVE_BEST_PRICE`, `PERC_BELOW_BEST_PRICE`, `PERC_ABOVE_REVERSE_PRICE`, and `PERC_BELOW_REVERSE_PRICE`.

Pending result:

```json
{"marketId":"1.214607388","pendingResultId":"1"}
```
