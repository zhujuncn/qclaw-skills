# Bet Angel API Reference

## Base URL
```
http://localhost:9000
```

## Key Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/markets/v1.0/getMarkets` | POST | Get markets loaded in Guardian |
| `/api/markets/v1.0/getMarketPrices` | POST | Get best back/lay prices |
| `/api/markets/v1.0/getBalance` | POST | Get account balance |
| `/api/markets/v1.0/getMarketBets` | POST | Get matched/unmatched bets |
| `/api/betting/v1.0/placeBets` | POST | Place a bet |
| `/api/betting/v1.0/cancelBets` | POST | Cancel bets in a market |
| `/api/betting/v1.0/greenAllSelections` | POST | Green all selections |
| `/api/betting/v1.0/closeTrade` | POST | Close trade on one selection |
| `/api/guardian/v1.0/applyCoupon` | POST | Load markets via coupon |
| `/api/guardian/v1.0/addMarkets` | POST | Add specific market IDs |
| `/api/guardian/v1.0/displayMarket` | POST | Show market in trading screen |

All POST requests require a JSON body (empty `{}` if no params).

---

## Market IDs: Two Formats

Bet Angel uses **two different ID formats** that are easily confused:

| Format | Example | Source |
|---|---|---|
| **Guardian ID** | `1.255680596` | From `getMarkets` (Guardian-loaded markets) |
| **Market ID** | `1.255697096` | From Bet Angel internal / other sources |

**Use Guardian IDs** for all API calls when working with Guardian-loaded markets.

---

## getMarkets

Get all markets loaded in Guardian with selection names.

**Request:**
```json
{
  "dataRequired": [
    "ID", "NAME", "MARKET_START_TIME", "MARKET_TYPE",
    "SELECTION_IDS", "SELECTION_NAMES"
  ]
}
```

**Response:** Markets are returned under `result.markets[]`. Each market has:
- `id`: Guardian market ID (use this for all API calls)
- `name`: Market name, e.g. `"Stuttgart v Hamburger SV - Match Odds"`
- `selections[]`: `[{id, name}, ...]` — selection names for ID mapping

---

## getMarketPrices

Get best back/lay prices. Returns ALL loaded markets in one response.

**Request:**
```json
{
  "marketId": "1.255680596",
  "dataRequired": ["BEST_PRICE_ONLY"]
}
```

**Response:**
```json
{
  "status": "OK",
  "result": {
    "markets": [{
      "id": "1.255680596",
      "status": "OPEN",
      "selections": [{
        "id": "44519",
        "back1": {"prc": 1.42, "sz": 100.0},
        "lay1": {"prc": 1.44, "sz": 50.0}
      }]
    }]
  }
}
```

Key fields per selection:
- `back1.prc` = BEST BACK price (Blue column)
- `lay1.prc` = BEST LAY price (Red column)
- `lay1.prc = 1000` = no lay price available (placeholder)
- `lay1 = null` = no lay side at all

⚠️ **Selection names are NOT in price data.** Always merge by ID with `getMarkets` selection data.

⚠️ **getMarketPrices returns ALL markets**, not just the requested one. Filter by `market.id == marketId`.

---

## placeBets — CRITICAL FORMAT

**This endpoint has a specific nested format that must be exact.**

✅ **CORRECT format:**
```json
{
  "marketId": "1.255680596",
  "globalSettings": {"action": "NONE"},
  "async": false,
  "betsToPlace": [{
    "selectionId": "44519",
    "type": "LAY",
    "bspBetType": "NOT_BSP",
    "price": 1.40,
    "stake": 5.0
  }]
}
```

❌ **WRONG (common mistake):**
```json
{
  "marketId": "1.255680596",
  "selectionId": "44519",     ← flat field, WRONG
  "betType": "LAY",           ← should be "type"
  "price": 1.40,
  "stake": 5.0,
  "globalSettingsAction": "NONE"
}
```

**Response:**
```json
{
  "status": "OK",
  "result": {
    "bets": [{
      "betToPlace": {...},
      "status": "OK",
      "betRef": "425187666743",
      "stakeMatched": 0.0
    }]
  }
}
```

`stakeMatched: 0.0` = bet is UNMATCHED (pending). Wait for match or cancel.

---

## cancelBets

Cancel unmatched bets in a market.

**Request:**
```json
{
  "marketId": "1.255680596",
  "filterOption": "ALL",
  "type": "ALL"
}
```

**Response:**
```json
{
  "status": "OK",
  "result": {
    "bets": [{
      "status": "OK",
      "betRef": "...",
      "stakeCancelled": 5.0
    }]
  }
}
```

---

## displayMarket

Display a market on a Bet Angel trading screen.

**URL:** `POST /api/guardian/v1.0/displayMarket`  
**NOT:** `/api/markets/v1.0/displayMarket` (wrong module, returns 404)

**Request:**
```json
{
  "marketId": "1.255680596",
  "displayChoice": "MAIN_LADDER",
  "activateWindow": true
}
```

`displayChoice` options:
- `MAIN_LADDER` — main ladder screen
- `MAIN_ONE_CLICK` — main one-click screen
- `NEW_ONE_CLICK_WINDOW` — new window
- `NEW_LADDER_WINDOW` — new ladder window

**Response:**
```json
{
  "status": "OK",
  "result": {
    "screenShowingMarket": {
      "marketId": "1.255680596",
      "screen": "MAIN_LADDER"
    }
  }
}
```

⚠️ Market must be added to Guardian first via `addMarkets` or `applyCoupon`.

---

## applyCoupon

Load markets into Guardian via a coupon.

**Request:**
```json
{
  "couponName": "Ex: Soccer - >50k vol - multi-column",
  "clearOption": "CLEAR_WATCH_LIST_ONLY",
  "watchListNumber": 1
}
```

⚠️ **Coupon name MUST include the `"Ex: "` prefix.**

Find available coupons with `getGuardianCoupons()`.

---

## greenAllSelections

Lock in equal profit across all outcomes.

**Request:**
```json
{
  "marketId": "1.255680596",
  "priceOption": "BEST_MARKET_PRICE"
}
```

---

## closeTrade

Greening / close a single selection.

**Request:**
```json
{
  "marketId": "1.255680596",
  "selectionId": "44519",
  "withGreening": true,
  "priceOption": "BEST_PRICE"
}
```

---

## Common Issues

### bet placed but not in Bet Angel UI
- Bet Angel requires the market to be in the trading view.
- Call `displayMarket()` BEFORE placing bets.

### cancelBets returns UNKNOWN_MARKET
- Wrong market ID format. Use Guardian ID from `getMarkets`.

### placeBets returns OK but betRef empty
- Market not displayed in trading view. Call `displayMarket()` first.

### getMarketPrices returns empty
- `getMarkets` must be called first to load market data.
- Markets must be loaded via `applyCoupon` or `addMarkets`.

### Selection names all 'N/A'
- Selection names come from `getMarkets` selections array, not price data.
- Merge by ID: `name_map[selection_id]`.

### LAY price = 1000.0
- "No lay price" placeholder value. Market has no sellers at this price level.

### LAY price = null / missing
- No lay side exists for this selection. Cannot LAY this team.

### Balance unchanged after bet
- For LAY bets, Bet Angel freezes the liability amount (stake × (price - 1)), not the full stake.
- Liability = £5 × (1.40 - 1) = £2.00 frozen.
- Balance shown may be available balance, not including frozen liability.
