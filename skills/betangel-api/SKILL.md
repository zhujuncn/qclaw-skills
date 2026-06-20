---
name: betangel-api
description: Build, debug, and explain Bet Angel Professional API integrations. Use when Codex needs to create JSON requests, scripts, or workflows for Bet Angel API, Guardian, Automation, Stored Values, Markets, Betting, Betfair bet placement/modification/cancellation, trading windows, automation servants, coupons, or the local Bet Angel JavaScript API example.
---

# Bet Angel API

Use this skill to help with Bet Angel Professional API requests and local automations.

## Core Workflow

1. Confirm Bet Angel Professional is running, logged in, and the API is enabled in Settings > Bet Angel API.
2. Use `localhost` and port `9000` by default unless the user gives another host/port.
3. Build URLs as `http://{host}:{port}/api/{component}/v1.0/{operationName}`.
4. Send JSON with HTTP `POST`; expect a JSON response with `status`, optional `errors`, and optional `result`.
5. For betting operations, ask before placing, modifying, cancelling, greening, or closing trades if the user has not explicitly authorized the live action.
6. For live betting calls, prefer `async: true` when the user wants non-blocking behavior, then poll the matching `getPending...Result` operation with `marketId` and `pendingResultId`.
7. If a request returns `PROCESSED_WITH_ERRORS`, preserve successful result data and inspect each item-level `error` or top-level `errors`.

## Global Live Execution Switch

For qclaw football workflows, use the root wrapper as the global daily switch:

```powershell
.\ba.ps1 AI开
.\ba.ps1 AI关
```

`AI开` keeps monitoring on and allows AI automatic Bet Angel execution when all strategy and risk gates pass. `AI关` keeps monitoring on but disables automatic live execution and returns to dry-run monitoring. Treat these as the global controls for automatic Bet Angel betting, reduce, close, and cash-out across all football skills. Use lower-level `ai-on`, `ai-off`, or direct `--execute` only when debugging the wrapper.

## Bet Angel GUI/API Mismatch

When the Bet Angel GUI shows in-play football markets but API monitoring reports `markets=0` or `inPlay=0`, do not assume the GUI and API are synchronized. Refresh `getMarkets`, `getMarketPrices`, and `getMarketBets`. Compare market IDs, market names, `status`, `inPlay`, and `startTime`. Treat API-returned football Match Odds markets with `status=OPEN` or `SUSPENDED` and `startTime <= now` as in-play-equivalent for monitoring, but allow real execution only while `status=OPEN`. If a GUI-visible market is absent from API `getMarkets`, mark it `API_NOT_VISIBLE` and do not auto bet, close, reduce, or green until the API returns explicit market ID, selection ID, status, and prices.
## References

- Read `references/api-reference.md` for endpoint components, operation names, payload fields, and common templates.
- Read `references/workflows.md` for end-to-end Guardian, Stored Values, and Betting sequences from the official guide and local JavaScript example.

## Local Example

The installed Bet Angel JavaScript test page is normally at:

`C:\Program Files (x86)\Bet Angel Limited\Bet Angel - Professional\api\javascript_example`

Use its `index.html` UI to experiment with requests, and inspect `index.js` when exact request builder behavior is needed. It contains the current installed operation mapping and JSON payload construction.

