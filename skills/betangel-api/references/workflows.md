# Bet Angel API Workflows

## Request Builder Checklist

1. Identify component and operation.
2. Use `POST http://localhost:9000/api/{component}/v1.0/{operation}` unless host/port differ.
3. Build a JSON instruction body. Use `{}` for operations with no instruction fields.
4. Validate ID strings:
   - Market IDs look like `1.214607388`.
   - Selection IDs are strings in the local JavaScript example.
   - Bet refs are strings.
5. Parse response:
   - `status: OK`: inspect `result`.
   - `status: PENDING`: save `pendingResultId`, then call paired pending result operation.
   - `status: PROCESSED_WITH_ERRORS`: inspect successful result data and each `error`.
   - `status: FAILED`: inspect `errors`.

## Load Markets, Set Stored Values, Apply Rules

Use this workflow for "load coupon and apply strategy/rules based on stored values".

1. Apply a Guardian coupon:

```text
POST /api/guardian/v1.0/applyCoupon
```

```json
{
  "couponName": "Ex: HR - UK - Win & Place - 2 column",
  "clearOption": "CLEAR_GUARDIAN_AND_WATCH_LIST",
  "watchListNumber": 1
}
```

2. Wait for Guardian to load market/selection data. This can take seconds or minutes depending on market count and Guardian refresh interval.

3. Get market and selection IDs:

```text
POST /api/markets/v1.0/getMarkets
```

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

4. Set stored values. Numeric values use `v`; text values use `t`.

```text
POST /api/automation/v1.0/setStoredValues
```

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
    },
    {
      "id": "1.206990739",
      "selections": [
        {
          "id": "7450122",
          "sharedValues": [
            {"n":"STAKE","v":5},
            {"n":"MIN_PRICE","v":1.6}
          ]
        }
      ]
    }
  ]
}
```

5. Apply rules to Guardian:

```text
POST /api/guardian/v1.0/applyRules
```

```json
{
  "rulesFileName": "Place Bet Based on Stored Values",
  "marketsFilter": {"filter":"ALL"},
  "guardianRulesColumn": 1
}
```

If a market ID is wrong, expect `PROCESSED_WITH_ERRORS` and an error like `UNKNOWN_MARKET`.

## Place, Modify, Inspect, Cancel

Use this workflow for unmatched bet management.

1. Place one or more bets:

```text
POST /api/betting/v1.0/placeBets
```

```json
{
  "marketId": "1.214607388",
  "globalSettings": {"action":"NONE"},
  "async": false,
  "betsToPlace": [
    {"selectionId":"47999","type":"LAY","price":1.10,"stake":10.0},
    {"selectionId":"1096","type":"LAY","price":1.10,"stake":10.0},
    {"selectionId":"56323","type":"LAY","price":1.10,"stake":10.0}
  ]
}
```

The response returns one item per requested bet. Save `betRef`; `stakeMatched: 0` means the bet is currently unmatched.

2. Modify unmatched bets:

```text
POST /api/betting/v1.0/modifyBets
```

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

Important behavior:

- Increasing stake can create an `additionalBetRef`.
- Changing price can create a `newBetRef`.
- Decreasing stake normally cancels part of the unmatched stake without changing the bet ref.

3. Inspect unmatched bets:

```text
POST /api/markets/v1.0/getMarketBets
```

```json
{"marketId":"1.214607388","filter":{"option":"ALL_UNMATCHED"}}
```

4. Cancel a specific bet:

```text
POST /api/betting/v1.0/cancelBets
```

```json
{
  "marketId": "1.214607388",
  "filterOption": "SPECIFIED_BET_REFS",
  "betRefs": ["313259260007"],
  "type": "ALL",
  "async": false
}
```

5. Cancel all unmatched bets:

```json
{
  "marketId": "1.214607388",
  "filterOption": "ALL",
  "type": "ALL",
  "async": false
}
```

6. Confirm cleanup with `getMarketBets` and `ALL_UNMATCHED`; the `unmatchedBets` list should be empty.

## Automation Servant Workflow

1. Ensure the market is loaded in Guardian.
2. Use `displayMarket` if the servant requires the market on a trading screen.
3. Start the servant with `startAutomationServant`.
4. Track it with `getInstances`.
5. Stop early with `stopAutomationServant` if needed.

Example:

```json
{
  "marketId": "1.23456789",
  "rulesFileName": "My Servant",
  "contextSelectionId": "12345",
  "contextPrice": 2.5,
  "contextBackStake": 10,
  "contextLayStake": 10
}
```

Possible start errors include unknown market/selection, invalid or unknown rules file, market not in a trading screen, invalid stake/liability, and invalid price.

## Troubleshooting

- If API calls fail to connect, check API enabled state, port, local firewall, and whether another Bet Angel instance is using a different port.
- If remote LAN access is needed, use the official guide's "Calling the API from another PC" page and verify host binding/firewall.
- If `applyCoupon` fails, make Guardian visible at least once after starting Bet Angel.
- After `addMarkets` or `applyCoupon`, wait before calling `getMarkets`; Guardian may still be loading selection information.
- For `startAutomationServant`, display the market on a trading screen first if the API returns `MARKET_NOT_IN_A_TRADING_SCREEN`.
- For bet actions, preserve all returned bet refs because modifications may return `newBetRef` or `additionalBetRef`.
