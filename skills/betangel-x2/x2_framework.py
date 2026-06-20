"""
Bet Angel X2 Strategy Framework v3.0
=====================================
Strategy: LAY Home Team in Match Odds (Red price)
  Condition: Under 5.5 Goals market must exist for same match

Colour reference:
  Blue = BACK  (支持主队)
  Red  = LAY   (反对主队)  <- 我们用的是红色

Pipeline:
  Layer 1: Monitor   - scan Guardian markets every 15s
  Layer 2: Filter    - Match Odds + Under 5.5 present?
  Layer 3: Price     - HOME LAY price (RED)
  Layer 4: Bet       - LAY Home via Betting API
  Layer 5: Green     - auto-green at 45 min / profit >= 0.15
  Layer 6: Logger    - all decisions to x2_bets.csv

API data formats (discovered empirically):
  getMarkets(dataRequired=[...,"SELECTION_IDS","SELECTION_NAMES"])
    -> selections: [{"id":"44526","name":"St Pauli"}, ...]

  getMarketPrices(marketId, dataRequired=["BEST_PRICE_ONLY"])
    -> selections: [{"id":"44526","back1":{"prc":44.0,"sz":33.9},"lay1":{"prc":46.0,"sz":10.76}}, ...]

Usage:
  python x2_framework.py [--test] [--stake 5.0]
"""

import requests
import time
import csv
import logging
import argparse
import os
from datetime import datetime
from typing import Optional, Dict, List

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("x2_framework.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("X2")


# ─── API Endpoints ─────────────────────────────────────────────────────────────
BA_BASE    = "http://localhost:9000"
MARKETS    = f"{BA_BASE}/api/markets/v1.0"
GUARDIAN   = f"{BA_BASE}/api/guardian/v1.0"
BETTING    = f"{BA_BASE}/api/betting/v1.0"

SESSION = requests.Session()
SESSION.headers.update({"Content-Type": "application/json"})


# ─── Strategy Config ─────────────────────────────────────────────────────────
CONFIG = {
    "default_stake":   5.0,
    "min_stake":       2.0,
    "max_stake":       50.0,
    "min_lay_odds":    1.01,
    "max_lay_odds":    1.55,
    "green_threshold": 0.15,   # profit in GBP
    "green_time_mins": 45,
    "poll_interval":   15,
}


# ─── API Helpers ──────────────────────────────────────────────────────────────
def api_post(url: str, payload: dict = None) -> dict:
    try:
        r = SESSION.post(url, json=payload or {}, timeout=30)
        if r.status_code == 404:
            return {"status": "NOT_FOUND"}
        return r.json()
    except Exception as e:
        logger.error(f"API error {url}: {e}")
        return {"status": "ERROR", "error": str(e)}


def api_get_balance() -> float:
    """Get account balance. Returns float in account currency (RON)."""
    r = api_post(f"{MARKETS}/getBalance", {})
    result = r.get("result", {})
    bal = result.get("balance") or r.get("balance", 0)
    return float(bal)


def scan_markets_by_name(name_filter: str, markets: List[dict] = None) -> List[dict]:
    """Scan all Guardian markets and return those matching name_filter (case-insensitive substring).

    Args:
        name_filter: Substring to match against market name (e.g. "over/under 0.5")
        markets: Optional pre-fetched market list (avoids re-fetching)

    Returns:
        List of market dicts with enriched selection names from getMarkets.
    """
    if markets is None:
        markets = get_guardian_markets()
    filt_lower = name_filter.lower()
    return [m for m in markets if filt_lower in m.get("name", "").lower()]


def scan_prices_bulk(market_ids: List[str] = None) -> Dict[str, dict]:
    """Get prices for all Guardian markets in one API call.

    CRITICAL: getMarketPrices returns ALL Guardian markets regardless of marketId param.
    The marketId is still required but any valid ID works.
    Response: {"result":{"markets":[{"id":"...","status":"OPEN","selections":[...]}]}}

    Returns:
        Dict mapping market_id -> {"status":"OPEN","selections":{sel_id: {"back1":...,"lay1":...}}}
    """
    # We need at least one market ID to make the call
    markets = get_guardian_markets()
    if not markets:
        return {}

    if not market_ids:
        market_ids = [m.get("id", "") for m in markets]

    sample_mid = market_ids[0] or markets[0].get("id", "")

    r = api_post(f"{MARKETS}/getMarketPrices", {
        "marketId": sample_mid,
        "dataRequired": ["BEST_PRICE_ONLY"]
    })

    if r.get("status") != "OK":
        return {}

    price_map = {}
    for pm in r.get("result", {}).get("markets", []):
        pmid = pm.get("id", "")
        selections = {}
        for s in pm.get("selections", []):
            sid = s.get("id", "")
            if sid:
                selections[sid] = {
                    "back1": s.get("back1", {}),
                    "lay1": s.get("lay1", {}),
                }
        price_map[pmid] = {
            "status": pm.get("status", ""),
            "selections": selections
        }
    return price_map


# ─── Market Data ─────────────────────────────────────────────────────────────
def get_guardian_markets() -> List[dict]:
    """
    Get all markets loaded in Guardian, with selection names.
    API returns: {"result":{"markets":[...]}}
    Each market has selections: [{"id":"...","name":"Team A"}, ...]
    """
    r = api_post(f"{MARKETS}/getMarkets", {
        "dataRequired": [
            "ID", "NAME", "MARKET_START_TIME", "MARKET_TYPE",
            "SELECTION_IDS", "SELECTION_NAMES"
        ]
    })
    if r.get("status") != "OK":
        return []
    result = r.get("result", {})
    return result.get("markets", [])


def get_market_prices(market_id: str) -> Optional[dict]:
    """
    Get best back/lay price for each selection in a market.

    Returns the market dict with selections enriched:
      [{"id":"44526","name":"St Pauli","back1":{"prc":44.0,"sz":33.9},"lay1":{"prc":46.0,"sz":10.76}}, ...]

    Key fields:
      back1.prc = BEST BACK price (蓝色/BLUE)
      lay1.prc  = BEST LAY  price (红色/RED)  <- 我们用这个
    """
    r = api_post(f"{MARKETS}/getMarketPrices", {
        "marketId": market_id,
        "dataRequired": ["BEST_PRICE_ONLY"]
    })
    if r.get("status") != "OK":
        return None
    result = r.get("result", {})
    markets = result.get("markets", [])
    for m in markets:
        if m.get("id") == market_id:
            return m
    return None


def get_pending_bets(market_id: str, pending_id: int) -> dict:
    return api_post(f"{BETTING}/getPendingPlaceBetsResult", {
        "marketId": market_id, "pendingId": pending_id
    })


# ─── Betting ─────────────────────────────────────────────────────────────────
def place_lay_bet(market_id: str, selection_id: str, price: float, stake: float) -> dict:
    """Place a LAY bet. Uses Bet Angel's flat betsToPlace format (type + price + stake).

    CRITICAL: Use "type" field, NOT "betType"! "betType": "L" is interpreted as BACK!
    """
    logger.info(f"  >> Placing LAY {stake} @ {price} | sel={selection_id}")
    return api_post(f"{BETTING}/placeBets", {
        "marketId":      market_id,
        "globalSettings": {"action": "NONE"},
        "async":          False,
        "betsToPlace":   [{
            "selectionId": str(selection_id),
            "type":        "LAY",  # <-- CORRECT: use "type", not "betType"!
            "price":       float(price),
            "stake":       float(stake)
        }]
    })


def place_back_bet(market_id: str, selection_id: str, price: float, stake: float) -> dict:
    """Place a BACK bet. Bet Angel format: type='BACK' + price + stake (flat fields, NOT priceSize).

    Discovered 2026-04-17: Use "type" field, NOT "betType"!
    "betType": "B" or "L" are both interpreted as BACK - this is a trap!

    Response: {"status":"OK","result":{"bets":[{"status":"OK","betToPlace":{"type":"BACK","stake":5.0,"price":1.03}}]}}
    """
    logger.info(f"  >> Placing BACK {stake} @ {price} | sel={selection_id}")
    return api_post(f"{BETTING}/placeBets", {
        "marketId":      market_id,
        "globalSettings": {"action": "NONE"},
        "async":          False,
        "betsToPlace":   [{
            "selectionId": str(selection_id),
            "type":        "BACK",  # <-- CORRECT: use "type", not "betType"!
            "price":       float(price),
            "stake":       float(stake)
        }]
    })


def parse_bet_result(result: dict) -> dict:
    """Parse placeBets API response into a standard dict.

    Returns:
        {
            "success": True/False,
            "status": "OK"/"FAILED"/...,
            "bet_id": "...",
            "stake": 5.0,
            "price": 1.03,
            "error_code": "...",
            "error_msg": "...",
        }
    """
    out = {"success": False, "status": "", "error_code": "", "error_msg": ""}
    if result.get("status") != "OK" and result.get("status") != "PROCESSED_WITH_ERRORS":
        out["status"] = result.get("status", "UNKNOWN")
        return out

    bets = result.get("result", {}).get("bets", [])
    if not bets:
        out["status"] = "NO_BETS_RETURNED"
        return out

    b = bets[0]
    bstatus = b.get("status", "")
    btp = b.get("betToPlace", {})
    err = b.get("error", {})

    out["status"] = bstatus
    out["stake"] = btp.get("stake", 0)
    out["price"] = btp.get("price", 0)

    if bstatus == "OK":
        out["success"] = True
        # Some responses include betRef/betId
        out["bet_id"] = b.get("betRef", btp.get("betId", ""))
    else:
        out["error_code"] = err.get("code", "")
        out["error_msg"] = err.get("msg", "")

    return out


def cancel_all_bets(market_id: str) -> dict:
    return api_post(f"{BETTING}/cancelBets", {
        "marketId":     market_id,
        "filterOption": "ALL",
        "type":         "ALL"
    })


def lay_home_team(market_id: str, stake: float = 5.0, max_odds: float = 1.55) -> dict:
    """Simplified LAY Home Team execution.

    Automatically finds home team selection and current LAY price, then places bet.

    Args:
        market_id: Guardian Market ID (e.g., "1.256453772")
        stake: Bet stake in RON (default 5.0)
        max_odds: Maximum LAY odds to accept (default 1.55 for X2 strategy)

    Returns:
        {"success": True/False, "bet_id": "...", "price": 1.45, "message": "..."}

    Example:
        >>> lay_home_team("1.256453772", stake=1.0)
        {'success': True, 'bet_id': '425867...', 'price': 8.0, 'message': 'LAY SSD Bari @ 8.0'}
    """
    # Get market info to find home team
    markets = get_guardian_markets()
    target_market = None
    for m in markets:
        if m.get('id') == market_id:
            target_market = m
            break

    if not target_market:
        return {"success": False, "message": f"Market {market_id} not found in Guardian"}

    # Extract home team from market name (e.g., "Team A v Team B - Match Odds")
    market_name = target_market.get('name', '')
    home_team = ""
    if " v " in market_name:
        match_part = market_name.split(" - ")[0] if " - " in market_name else market_name
        home_team = match_part.split(" v ")[0].strip()

    if not home_team:
        return {"success": False, "message": f"Cannot extract home team from: {market_name}"}

    # Find home team selection ID
    selections = target_market.get('selections', [])
    home_sel_id = None
    for sel in selections:
        if home_team.lower() in sel.get('name', '').lower():
            home_sel_id = sel.get('id')
            break

    if not home_sel_id:
        return {"success": False, "message": f"Home team '{home_team}' selection not found"}

    # Get current LAY price
    prices = scan_prices_bulk()
    mdata = prices.get(market_id, {})

    if mdata.get('status') != 'OPEN':
        return {"success": False, "message": f"Market status: {mdata.get('status')}"}

    sel_data = mdata.get('selections', {}).get(home_sel_id, {})
    lay_price = sel_data.get('lay1', {}).get('prc', 0)

    if not lay_price:
        return {"success": False, "message": "No LAY price available"}

    if lay_price > max_odds:
        return {"success": False, "message": f"LAY price {lay_price} > max {max_odds}"}

    # Place LAY bet
    logger.info(f"LAY {home_team}: {stake} RON @ {lay_price}")
    resp = place_lay_bet(market_id, home_sel_id, lay_price, stake)
    parsed = parse_bet_result(resp)

    if parsed.get('success'):
        return {
            "success": True,
            "bet_id": parsed.get('bet_id'),
            "price": lay_price,
            "stake": stake,
            "home_team": home_team,
            "message": f"LAY {home_team} @ {lay_price} ({stake} RON)"
        }
    else:
        return {
            "success": False,
            "message": f"Bet failed: {parsed.get('error_msg', parsed.get('status'))}"
        }


def display_market(market_id: str, screen: str = "MAIN_LADDER", activate: bool = True) -> dict:
    """Display a market on a Bet Angel trading screen.
    screen options: MAIN_LADDER, MAIN_ONE_CLICK, NEW_ONE_CLICK_WINDOW, NEW_LADDER_WINDOW"""
    return api_post(f"{GUARDIAN}/displayMarket", {
        "marketId":       market_id,
        "displayChoice":   screen,
        "activateWindow":  activate
    })


# ─── Greening ─────────────────────────────────────────────────────────────────
def green_all(market_id: str) -> dict:
    return api_post(f"{BETTING}/greenAllSelections", {
        "marketId":    market_id,
        "priceOption": "BEST_MARKET_PRICE"
    })


def green_selection(market_id: str, selection_id: str) -> dict:
    return api_post(f"{BETTING}/closeTrade", {
        "marketId":     market_id,
        "selectionId": selection_id,
        "withGreening": True,
        "priceOption":  "BEST_PRICE"
    })


# ─── Guardian ─────────────────────────────────────────────────────────────────
def get_guardian_coupons() -> List[str]:
    r = api_post(f"{GUARDIAN}/getCoupons", {})
    return r.get("couponNames", [])


def apply_coupon(coupon_name: str, watch_list: int = 1) -> dict:
    return api_post(f"{GUARDIAN}/applyCoupon", {
        "couponName":   coupon_name,
        "clearOption":  "CLEAR_WATCH_LIST_ONLY",
        "watchListNumber": watch_list
    })


# ─── Strategy Logic ────────────────────────────────────────────────────────────
def extract_teams(name: str) -> tuple:
    """Extract home/away from 'Team A v Team B - Match Odds'."""
    if " - " in name:
        match_part = name.split(" - ")[0]
    else:
        match_part = name
    if " v " in match_part:
        parts = match_part.split(" v ", 1)
        return parts[0].strip(), parts[1].strip()
    return "", ""


def has_under_market(markets: List[dict], home: str, away: str) -> bool:
    """True if Under 5.5 Goals exists for this specific match (BOTH teams must match)."""
    home_lc = home.lower()
    away_lc = away.lower()
    for m in markets:
        n = m.get("name", "").lower()
        if "under 5.5" not in n:
            continue
        # Both teams must appear in the market name (case-insensitive substring match)
        # e.g. "St Pauli v Bayern Munich - Under 5.5 Goals" matches both teams
        if home_lc in n and away_lc in n:
            return True
    return False


def evaluate_match(market: dict, all_markets: List[dict]) -> Optional[dict]:
    """
    X2 Strategy: LAY Home in Match Odds (when Under 5.5 present).

    Pipeline:
      1. Verify it's a Match Odds market
      2. Extract home/away team names
      3. Confirm Under 5.5 exists for this match
      4. Fetch prices; merge names by ID
      5. Find HOME selection (skip Draw, skip Away)
      6. Get HOME's LAY price (RED column)
      7. Apply odds filter
    """
    name = market.get("name", "")

    # Only Match Odds
    if "match odds" not in name.lower():
        return None

    home_raw, away_raw = extract_teams(name)
    if not home_raw or not away_raw:
        return None

    # Must have Under 5.5
    if not has_under_market(all_markets, home_raw, away_raw):
        return None

    mid = market.get("id") or market.get("marketId", "")
    logger.info(f"\n  [MATCH] {home_raw} vs {away_raw} | Under 5.5: YES")

    # Build ID -> name map from market data
    name_map: Dict[str, str] = {
        str(sel["id"]): sel["name"]
        for sel in market.get("selections", [])
    }

    # Fetch prices
    price_data = get_market_prices(mid)
    if not price_data:
        logger.warning(f"  [ERROR] No price data for {mid}")
        return None

    # Merge names into price selections
    price_sels = price_data.get("selections", [])
    for psel in price_sels:
        psel["name"] = name_map.get(str(psel.get("id", "")), "")

    # ── HOME DETECTION: match by team name, NOT by order ──────────────────────
    # Bet Angel API selection order is NOT guaranteed.
    # Home = first team in "TeamA v TeamB", Away = second team.
    # Use explicit name matching (exact + partial/substring) to avoid wrong picks.
    def name_matches(sel_name: str, team_name: str) -> bool:
        """True if selection name matches team name (exact or substring/parent)."""
        sn = sel_name.lower().strip()
        tn = team_name.lower().strip()
        if not sn or not tn:
            return False
        return sn == tn or tn in sn or sn in tn

    home_sel = None
    away_sel = None
    draw_sel = None

    for psel in price_sels:
        nl = psel.get("name", "").strip()
        if not nl:
            continue
        nl_lower = nl.lower()
        if nl_lower in ("draw", "the draw", "x"):
            draw_sel = psel
        elif name_matches(nl, home_raw):
            home_sel = psel
        elif name_matches(nl, away_raw):
            away_sel = psel

    # Always LAY Home — no DRAW fallback
    if not home_sel:
        logger.warning(f"  [SKIP] Cannot find HOME selection for '{home_raw}'")
        return None

    lay1 = home_sel.get("lay1", {})
    lay_price = float(lay1.get("prc", 0))
    lay_size  = float(lay1.get("sz",  0))

    # Show all three legs for reference
    draw_lay = draw_sel.get("lay1", {}).get("prc") if draw_sel else None
    away_lay = away_sel.get("lay1", {}).get("prc") if away_sel else None
    logger.info(f"  HOME LAY={lay_price} [RED] | DRAW LAY={draw_lay} | AWAY LAY={away_lay}")

    # Odds filter
    if not (CONFIG["min_lay_odds"] <= lay_price <= CONFIG["max_lay_odds"]):
        logger.info(f"  [SKIP] LAY {lay_price} outside range [{CONFIG['min_lay_odds']}-{CONFIG['max_lay_odds']}]")
        return None

    logger.info(f"  [QUALIFIES] -> LAY Home @{lay_price} | stake GBP{CONFIG['default_stake']}")

    return {
        "market_id":      mid,
        "market_name":    name,
        "home":          home_raw,
        "away":          away_raw,
        "selection_id":  str(home_sel.get("id", "")),
        "selection_name": home_raw,
        "lay_price":     lay_price,
        "lay_size":      lay_size,
    }


# ─── Data Logger ──────────────────────────────────────────────────────────────
DATA_FILE  = "x2_bets.csv"
DATA_FIELDS = [
    "timestamp", "market_id", "market_name",
    "home", "away", "selection_id", "selection_name",
    "bet_type", "lay_price", "stake",
    "pending_id", "matched", "green_status", "profit", "notes"
]


def log_bet(row: dict):
    file_exists = os.path.exists(DATA_FILE)
    with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=DATA_FIELDS)
        if not file_exists:
            w.writeheader()
        w.writerow(row)


# ─── Main Loop ────────────────────────────────────────────────────────────────
def run_framework(test_mode: bool = False, stake: float = None):
    stake = stake or CONFIG["default_stake"]

    logger.info("=" * 60)
    logger.info(f"X2 Strategy Framework v3 | test={test_mode} | stake=GBP{stake}")
    logger.info(f"Balance: GBP{api_get_balance():.2f}")
    logger.info("=" * 60)

    # Show available coupons
    coupons = get_guardian_coupons()
    soccer_coupons = [c for c in coupons if "soccer" in c.lower()]
    if soccer_coupons:
        logger.info(f"Soccer coupons: {soccer_coupons}")
    else:
        logger.warning("No soccer coupons found")

    loop_count   = 0
    active_markets: set = set()   # markets we've already traded

    while True:
        loop_count += 1
        ts = datetime.now().strftime("%H:%M:%S")

        markets = get_guardian_markets()
        match_odds = [m for m in markets if "match odds" in m.get("name", "").lower()]
        logger.info(f"[{ts}] Loop #{loop_count} | {len(markets)} markets, {len(match_odds)} Match Odds")

        if not markets:
            logger.warning("  No markets loaded in Guardian!")
            logger.warning("  Load via: Guardian menu -> Add Market")
            time.sleep(CONFIG["poll_interval"])
            continue

        for market in markets:
            mid = market.get("id") or market.get("marketId", "")
            if mid in active_markets:
                continue

            decision = evaluate_match(market, markets)
            if not decision:
                continue

            logger.info(f"\n  === QUALIFIES ===")
            logger.info(f"    {decision['home']} vs {decision['away']}")
            logger.info(f"    LAY Home @{decision['lay_price']} | Under 5.5: YES | Stake GBP{stake}")

            if test_mode:
                logger.info("  [TEST MODE] Would place LAY bet now")
                log_bet({
                    "timestamp":    datetime.now().isoformat(),
                    **decision,
                    "bet_type":    "LAY_HOME",
                    "stake":        stake,
                    "pending_id":   "TEST",
                    "matched":      False,
                    "green_status": "TEST",
                    "profit":       0,
                    "notes":        "test_mode"
                })
                active_markets.add(mid)
                continue

            # Place the bet
            result = place_lay_bet(
                decision["market_id"],
                decision["selection_id"],
                decision["lay_price"],
                stake
            )

            if result.get("status") == "OK":
                pending_id = result.get("pendingId", 0)
                logger.info(f"  Bet placed, pendingId={pending_id}")
                time.sleep(2)

                settled = get_pending_bets(decision["market_id"], pending_id)
                matched      = settled.get("matched", False)
                matched_stake = settled.get("matchedStake", 0)

                log_bet({
                    "timestamp":    datetime.now().isoformat(),
                    **decision,
                    "bet_type":    "LAY_HOME",
                    "stake":       matched_stake if matched else stake,
                    "pending_id":   pending_id,
                    "matched":      matched,
                    "green_status": "PENDING",
                    "profit":       0,
                    "notes":        "matched" if matched else "unmatched"
                })

                if matched:
                    active_markets.add(mid)
                    logger.info(f"  [OK] BET MATCHED: GBP{matched_stake} @ {decision['lay_price']}")
                else:
                    logger.warning("  [WARN] Bet not yet matched")

            elif result.get("status") == "NOT_FOUND":
                logger.warning("  Betting API not available (need Bet Angel Professional)")
            else:
                logger.error(f"  Bet failed: {result}")

        time.sleep(CONFIG["poll_interval"])


# ─── CLI Entry Point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="X2 Strategy Framework")
    parser.add_argument("--test", action="store_true", help="Test mode (no real bets)")
    parser.add_argument("--stake", type=float, default=5.0, help="Stake in GBP")
    args = parser.parse_args()

    try:
        run_framework(test_mode=args.test, stake=args.stake)
    except KeyboardInterrupt:
        logger.info("Framework stopped by user")
