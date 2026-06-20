#!/usr/bin/env python3
"""Bet Angel live order and position management engine."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
WORK_ROOT = ROOT / "work"
OUTPUTS_ROOT = ROOT / "outputs"
SYSTEM_ROOT = WORK_ROOT / "football-trading-system"
LOCAL_SCRIPTS = WORK_ROOT / "football-trading-advisor" / "scripts"

if str(LOCAL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(LOCAL_SCRIPTS))

from advisor import ba_balance, post_json  # type: ignore  # noqa: E402

BA_BASE = "http://localhost:9000/api"
TZ = ZoneInfo("Europe/Bucharest")
CONFIG_PATH = SYSTEM_ROOT / "live_trade_manager.json"


def now_local() -> datetime:
    return datetime.now(TZ)


def ensure_dirs() -> None:
    OUTPUTS_ROOT.mkdir(parents=True, exist_ok=True)
    SYSTEM_ROOT.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    for encoding in ("utf-8", "utf-8-sig"):
        try:
            return json.loads(path.read_text(encoding=encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except ValueError:
        return None


def string_id(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def lookup_ci(payload: dict[str, Any] | None, *names: str) -> Any:
    if not isinstance(payload, dict):
        return None
    lowered = {str(key).lower(): value for key, value in payload.items()}
    for name in names:
        if name in payload:
            return payload[name]
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def bool_ci(payload: dict[str, Any] | None, *names: str) -> bool | None:
    value = lookup_ci(payload, *names)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "on"}:
        return True
    if text in {"false", "0", "no", "off"}:
        return False
    return None


def resolve_path(value: str | None, fallback: Path) -> Path:
    if not value:
        return fallback
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def default_config() -> dict[str, Any]:
    return {
        "execute": False,
        "ai_automation_enabled": False,
        "heartbeat_mode": True,
        "heartbeat_file": "outputs/live-order-engine-heartbeat-latest.json",
        "heartbeat_log_file": "outputs/live-order-engine-heartbeat.jsonl",
        "state_file": "work/football-trading-system/live_trade_manager_state.json",
        "poll_seconds": 10,
        "max_cycles": 0,
        "watch_inplay_only": True,
        "always_monitor_exposure": True,
        "cancel_unmatched_before_exit": True,
        "action_cooldown_seconds": 45,
        "single_action_balance_cap_pct": 3.0,
        "absolute_balance_cap_pct": 10.0,
        "default_profit_lock_ron": 1.0,
        "default_stop_loss_ron": -1.0,
        "default_reduce_fraction": 0.5,
        "default_close_price_option": "BEST_PRICE",
        "default_green_price_option": "BEST_MARKET_PRICE",
        "default_max_supplement_price_drift_pct": 8.0,
        "plans": [],
    }


def normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    config["execute"] = bool(config.get("execute"))
    config["ai_automation_enabled"] = bool(config.get("ai_automation_enabled", False))
    config["heartbeat_mode"] = bool(config.get("heartbeat_mode", True))
    config["poll_seconds"] = max(1, int(config.get("poll_seconds") or 10))
    config["max_cycles"] = int(config.get("max_cycles") or 0)
    config["watch_inplay_only"] = bool(config.get("watch_inplay_only", True))
    config["always_monitor_exposure"] = bool(config.get("always_monitor_exposure", True))
    config["cancel_unmatched_before_exit"] = bool(config.get("cancel_unmatched_before_exit", True))
    config["action_cooldown_seconds"] = max(0, int(config.get("action_cooldown_seconds") or 45))
    config["single_action_balance_cap_pct"] = float(config.get("single_action_balance_cap_pct") or 3.0)
    config["absolute_balance_cap_pct"] = float(config.get("absolute_balance_cap_pct") or 10.0)
    config["default_profit_lock_ron"] = float(config.get("default_profit_lock_ron") or 1.0)
    config["default_stop_loss_ron"] = float(config.get("default_stop_loss_ron") or -1.0)
    config["default_reduce_fraction"] = float(config.get("default_reduce_fraction") or 0.5)
    config["default_close_price_option"] = str(config.get("default_close_price_option") or "BEST_PRICE")
    config["default_green_price_option"] = str(config.get("default_green_price_option") or "BEST_MARKET_PRICE")
    config["default_max_supplement_price_drift_pct"] = float(
        config.get("default_max_supplement_price_drift_pct") or 8.0
    )
    if not isinstance(config.get("plans"), list):
        config["plans"] = []
    return config


def load_config(path: Path) -> dict[str, Any]:
    config = default_config()
    data = load_json(path)
    if isinstance(data, dict):
        config.update(data)
    return normalize_config(config)


def ensure_config_file(path: Path) -> dict[str, Any]:
    config = load_config(path)
    if not path.exists():
        write_json(path, config)
    return config


def load_state(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if isinstance(data, dict):
        return data
    return {"labels": {}}


def save_state(path: Path, state: dict[str, Any]) -> None:
    write_json(path, state)


def get_markets() -> list[dict[str, Any]]:
    payload = {
        "dataRequired": [
            "ID",
            "NAME",
            "MARKET_START_TIME",
            "MARKET_TYPE",
            "SELECTION_IDS",
            "SELECTION_NAMES",
        ]
    }
    result = post_json(f"{BA_BASE}/markets/v1.0/getMarkets", payload, timeout=30)
    return result.get("result", {}).get("markets", [])


def get_market_prices() -> list[dict[str, Any]]:
    payload = {
        "dataRequired": [
            "MARKET_STATUS",
            "INPLAY_INFO",
            "BEST_THREE_PRICES",
            "LAST_TRADED_PRICE",
            "MATCHED_BET_SUMMARY",
            "UNMATCHED_BET_SUMMARY",
            "PROFIT",
            "CLOSE_TRADE_PROFIT",
            "GREENING_PROFIT",
        ]
    }
    result = post_json(f"{BA_BASE}/markets/v1.0/getMarketPrices", payload, timeout=30)
    return result.get("result", {}).get("markets", [])


def get_market_bets(market_id: str, filter_option: str = "ALL") -> dict[str, Any]:
    payload = {"marketId": market_id, "filter": {"option": filter_option}}
    return post_json(f"{BA_BASE}/markets/v1.0/getMarketBets", payload, timeout=20)


def place_bet(market_id: str, selection_id: str, side: str, price: float, stake: float) -> dict[str, Any]:
    payload = {
        "marketId": market_id,
        "async": False,
        "globalSettings": {"action": "NONE"},
        "betsToPlace": [
            {
                "selectionId": int(selection_id),
                "type": side,
                "price": float(price),
                "stake": float(stake),
            }
        ],
    }
    response = post_json(f"{BA_BASE}/betting/v1.0/placeBets", payload, timeout=20)
    return {"payload": payload, "response": response}


def cancel_bets(market_id: str, bet_refs: list[str] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "marketId": market_id,
        "type": "ALL",
        "async": False,
    }
    if bet_refs:
        payload["filterOption"] = "SPECIFIED_BET_REFS"
        payload["betRefs"] = bet_refs
    else:
        payload["filterOption"] = "ALL"
    response = post_json(f"{BA_BASE}/betting/v1.0/cancelBets", payload, timeout=20)
    return {"payload": payload, "response": response}


def green_all_selections(market_id: str, price_option: str) -> dict[str, Any]:
    payload = {
        "marketId": market_id,
        "priceOption": price_option,
        "async": False,
    }
    response = post_json(f"{BA_BASE}/betting/v1.0/greenAllSelections", payload, timeout=20)
    return {"payload": payload, "response": response}


def close_trade(
    market_id: str,
    selection_id: str,
    with_greening: bool,
    price_option: str,
    fixed_price: float | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "marketId": market_id,
        "selectionId": int(selection_id),
        "withGreening": bool(with_greening),
        "priceOption": price_option,
        "async": False,
    }
    if price_option == "FIXED_PRICE" and fixed_price is not None:
        payload["fixedPrice"] = float(fixed_price)
    response = post_json(f"{BA_BASE}/betting/v1.0/closeTrade", payload, timeout=20)
    return {"payload": payload, "response": response}


def market_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("id")): row for row in rows if row.get("id") is not None}


def selection_rows(meta: dict[str, Any] | None, prices: dict[str, Any] | None) -> list[dict[str, Any]]:
    if meta and meta.get("selections"):
        return [row for row in meta.get("selections", []) if row.get("id") is not None]
    if prices and prices.get("selections"):
        return [row for row in prices.get("selections", []) if row.get("id") is not None]
    return []


def selection_name(meta: dict[str, Any] | None, prices: dict[str, Any] | None, selection_id: str | None) -> str | None:
    if not selection_id:
        return None
    for row in selection_rows(meta, prices):
        if str(row.get("id")) == str(selection_id):
            return str(row.get("name")) if row.get("name") else None
    return None


def selection_price_row(prices: dict[str, Any] | None, selection_id: str | None) -> dict[str, Any] | None:
    if not prices or not selection_id:
        return None
    for row in prices.get("selections", []) or []:
        if str(row.get("id")) == str(selection_id):
            return row
    return None


def executable_price(side: str, price_row: dict[str, Any] | None) -> float | None:
    if not price_row:
        return None
    if side == "BACK":
        return safe_float(lookup_ci(lookup_ci(price_row, "lay1"), "prc")) or safe_float(lookup_ci(lookup_ci(price_row, "back1"), "prc"))
    if side == "LAY":
        return safe_float(lookup_ci(lookup_ci(price_row, "back1"), "prc")) or safe_float(lookup_ci(lookup_ci(price_row, "lay1"), "prc"))
    return None


def opposite_side(side: str) -> str:
    return "LAY" if side == "BACK" else "BACK"


def market_is_inplay(prices: dict[str, Any] | None, meta: dict[str, Any] | None = None) -> bool:
    if not prices:
        return False
    direct = bool_ci(prices, "inPlay", "isInPlay", "inplay")
    if direct is not None:
        return direct
    nested = lookup_ci(prices, "inPlayInfo", "inplayInfo", "inplay")
    if isinstance(nested, dict):
        nested_flag = bool_ci(nested, "inPlay", "isInPlay", "inplay")
        if nested_flag is not None:
            return nested_flag
    status = str(lookup_ci(prices, "status") or "").upper()
    start_time = str((meta or {}).get("startTime") or "")
    market_type = str((meta or {}).get("marketType") or "").upper()
    market_name = str((meta or {}).get("name") or "")
    if status in {"OPEN", "SUSPENDED"} and (market_type == "MATCH_ODDS" or " - Match Odds" in market_name):
        try:
            parsed = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=TZ)
            return parsed <= now_local()
        except ValueError:
            return False
    return False


def market_has_exposure(prices: dict[str, Any]) -> bool:
    if safe_float(lookup_ci(prices, "profit")) not in {None, 0.0}:
        return True
    matched_summary = lookup_ci(prices, "matchedBetSummary")
    unmatched_summary = lookup_ci(prices, "unmatchedBetSummary")
    if matched_summary or unmatched_summary:
        return True
    for row in prices.get("selections", []) or []:
        if safe_float(lookup_ci(row, "profit", "closeProfGreen", "greenAllProfit")) not in {None, 0.0}:
            return True
    return False


def bet_side(bet: dict[str, Any]) -> str | None:
    raw = lookup_ci(bet, "type", "betType", "side")
    if raw is None:
        return None
    return str(raw).upper()


def bet_stake(bet: dict[str, Any]) -> float:
    for name in ("stakeMatched", "matchedStake", "stake", "sizeMatched", "size"):
        value = safe_float(lookup_ci(bet, name))
        if value is not None:
            return value
    return 0.0


def summarize_market_bets(bets_payload: dict[str, Any]) -> dict[str, Any]:
    result = bets_payload.get("result", {}) if isinstance(bets_payload, dict) else {}
    matched = result.get("matchedBets", []) or []
    unmatched = result.get("unmatchedBets", []) or []
    selection_summary: dict[str, dict[str, Any]] = {}

    def touch(selection_id: str) -> dict[str, Any]:
        return selection_summary.setdefault(
            selection_id,
            {
                "matchedStake": 0.0,
                "unmatchedStake": 0.0,
                "matchedBackStake": 0.0,
                "matchedLayStake": 0.0,
                "unmatchedBackStake": 0.0,
                "unmatchedLayStake": 0.0,
                "betRefs": [],
            },
        )

    for bet in matched:
        selection_id = string_id(lookup_ci(bet, "selectionId"))
        if not selection_id:
            continue
        row = touch(selection_id)
        stake = bet_stake(bet)
        side = bet_side(bet)
        row["matchedStake"] = round(row["matchedStake"] + stake, 2)
        if side == "BACK":
            row["matchedBackStake"] = round(row["matchedBackStake"] + stake, 2)
        elif side == "LAY":
            row["matchedLayStake"] = round(row["matchedLayStake"] + stake, 2)
        bet_ref = string_id(lookup_ci(bet, "betRef"))
        if bet_ref:
            row["betRefs"].append(bet_ref)

    for bet in unmatched:
        selection_id = string_id(lookup_ci(bet, "selectionId"))
        if not selection_id:
            continue
        row = touch(selection_id)
        stake = bet_stake(bet)
        side = bet_side(bet)
        row["unmatchedStake"] = round(row["unmatchedStake"] + stake, 2)
        if side == "BACK":
            row["unmatchedBackStake"] = round(row["unmatchedBackStake"] + stake, 2)
        elif side == "LAY":
            row["unmatchedLayStake"] = round(row["unmatchedLayStake"] + stake, 2)
        bet_ref = string_id(lookup_ci(bet, "betRef"))
        if bet_ref:
            row["betRefs"].append(bet_ref)

    exposed_selection_ids = [sid for sid, row in selection_summary.items() if row["matchedStake"] > 0 or row["unmatchedStake"] > 0]
    return {
        "matchedBets": matched,
        "unmatchedBets": unmatched,
        "selectionSummary": selection_summary,
        "matchedCount": len(matched),
        "unmatchedCount": len(unmatched),
        "matchedStakeTotal": round(sum(bet_stake(bet) for bet in matched), 2),
        "unmatchedStakeTotal": round(sum(bet_stake(bet) for bet in unmatched), 2),
        "exposedSelectionCount": len(exposed_selection_ids),
        "hasExposure": bool(exposed_selection_ids),
    }


def preview_values(market_prices: dict[str, Any] | None, selection_id: str | None) -> dict[str, float | None]:
    selection = selection_price_row(market_prices, selection_id)
    green_all_profit = safe_float(lookup_ci(market_prices, "greenAllProfit", "greeningProfit"))
    if green_all_profit is None and selection is not None:
        green_all_profit = safe_float(lookup_ci(selection, "greenAllProfit", "greeningProfit"))
    close_profit = None
    selection_profit = None
    if selection is not None:
        close_profit = safe_float(lookup_ci(selection, "closeProfGreen", "closeTradeProfit"))
        selection_profit = safe_float(lookup_ci(selection, "profit"))
    if selection_profit is None:
        selection_profit = safe_float(lookup_ci(market_prices, "profit"))
    return {
        "greenAllProfit": green_all_profit,
        "closeProfGreen": close_profit,
        "selectionProfit": selection_profit,
    }


def build_market_snapshot(
    meta: dict[str, Any] | None,
    prices: dict[str, Any] | None,
    bets_payload: dict[str, Any],
) -> dict[str, Any]:
    bet_summary = summarize_market_bets(bets_payload)
    return {
        "marketId": string_id((meta or {}).get("id") or (prices or {}).get("id")),
        "marketName": (meta or {}).get("name"),
        "marketType": (meta or {}).get("marketType"),
        "marketStatus": (prices or {}).get("status"),
        "marketStartTime": (meta or {}).get("startTime"),
        "inPlay": market_is_inplay(prices, meta),
        "betSummary": bet_summary,
    }


def action_signature(action: dict[str, Any]) -> str:
    key_fields = {
        "kind": action.get("kind"),
        "marketId": action.get("marketId"),
        "selectionId": action.get("selectionId"),
        "side": action.get("side"),
        "price": action.get("price"),
        "stake": action.get("stake"),
        "priceOption": action.get("priceOption"),
    }
    return json.dumps(key_fields, sort_keys=True, ensure_ascii=False)


def allowed_place_stake(
    requested_stake: float,
    current_balance: float,
    config: dict[str, Any],
    plan: dict[str, Any],
) -> float:
    absolute_cap = current_balance * (float(config["absolute_balance_cap_pct"]) / 100.0)
    single_cap = current_balance * (float(config["single_action_balance_cap_pct"]) / 100.0)
    plan_cap = safe_float(plan.get("maxActionStakeRon"))
    cap = min(single_cap, absolute_cap, plan_cap if plan_cap is not None else float("inf"))
    return round(min(requested_stake, cap), 2)


def evaluate_plan(
    plan: dict[str, Any],
    config: dict[str, Any],
    market_snapshot: dict[str, Any],
    meta: dict[str, Any] | None,
    prices: dict[str, Any] | None,
    current_balance: float,
) -> dict[str, Any]:
    selection_id = string_id(plan.get("selectionId"))
    side = str(plan.get("side") or "").upper()
    selection_summary = market_snapshot["betSummary"]["selectionSummary"].get(selection_id or "", {})
    price_row = selection_price_row(prices, selection_id)
    entry_price = safe_float(plan.get("entryPrice"))
    current_price = executable_price(side, price_row)
    reduce_side = opposite_side(side) if side in {"BACK", "LAY"} else None
    reduce_price = executable_price(reduce_side or "", price_row)
    max_supplement_price = safe_float(plan.get("maxSupplementPrice"))
    if max_supplement_price is None and entry_price is not None:
        drift_pct = float(plan.get("maxSupplementPriceDriftPct") or config["default_max_supplement_price_drift_pct"])
        max_supplement_price = round(entry_price * (1.0 + drift_pct / 100.0), 3)
    min_supplement_price = safe_float(plan.get("minSupplementPrice"))
    allow_fresh_entry = bool(plan.get("allowFreshEntry", False))
    allow_supplement = bool(plan.get("allowSupplement", False))
    allow_cash_out = bool(plan.get("allowCashOut", True))
    in_play_only = bool(plan.get("inPlayOnly", config["watch_inplay_only"]))
    with_greening = bool(plan.get("withGreening", True))
    green_whole_market = bool(plan.get("greenWholeMarketIfMultipleExposures", True))
    target_stake = safe_float(plan.get("targetStake"))
    profit_lock = safe_float(plan.get("profitLockRon"))
    stop_loss = safe_float(plan.get("stopLossRon"))
    reduce_on_profit = safe_float(plan.get("reduceOnProfitRon"))
    reduce_fraction = safe_float(plan.get("reduceFraction"))
    if profit_lock is None:
        profit_lock = config["default_profit_lock_ron"]
    if stop_loss is None:
        stop_loss = config["default_stop_loss_ron"]
    if reduce_fraction is None:
        reduce_fraction = config["default_reduce_fraction"]

    matched_stake = float(selection_summary.get("matchedBackStake" if side == "BACK" else "matchedLayStake", 0.0))
    opposing_matched_stake = float(selection_summary.get("matchedLayStake" if side == "BACK" else "matchedBackStake", 0.0))
    unmatched_stake = float(selection_summary.get("unmatchedBackStake" if side == "BACK" else "unmatchedLayStake", 0.0))
    opposing_unmatched_stake = float(selection_summary.get("unmatchedLayStake" if side == "BACK" else "unmatchedBackStake", 0.0))
    preview = preview_values(prices, selection_id)
    gate_trace: list[dict[str, Any]] = []

    def gate(name: str, passed: bool, detail: Any) -> None:
        gate_trace.append({"name": name, "passed": passed, "detail": detail})

    gate("market_open", market_snapshot["marketStatus"] == "OPEN", market_snapshot["marketStatus"])
    gate("in_play", (not in_play_only) or market_snapshot["inPlay"], market_snapshot["inPlay"])
    gate("selection_id", bool(selection_id), selection_id)
    gate("side", side in {"BACK", "LAY"}, side)
    gate("price_present", current_price is not None, current_price)
    market_open_ok = market_snapshot["marketStatus"] == "OPEN"
    in_play_ok = (not in_play_only) or market_snapshot["inPlay"]
    side_ok = side in {"BACK", "LAY"}
    selection_ok = bool(selection_id)
    selection_actionable = market_open_ok and in_play_ok and side_ok and selection_ok
    hedge_ratio = (opposing_matched_stake / matched_stake) if matched_stake > 0 else 0.0
    already_hedged = matched_stake > 0 and hedge_ratio >= 0.9 and opposing_unmatched_stake == 0

    actions: list[dict[str, Any]] = []
    reasons: list[str] = []
    suppressed: list[dict[str, Any]] = []

    green_profit = preview["greenAllProfit"]
    close_profit = preview["closeProfGreen"]
    comparison_profit = close_profit if close_profit is not None else green_profit
    gate("cashout_preview_available", comparison_profit is not None, comparison_profit)
    gate("not_already_hedged", not already_hedged, f"opposing={opposing_matched_stake}, matched={matched_stake}")

    exit_triggered = False
    if allow_cash_out and not already_hedged and market_open_ok and in_play_ok and side_ok and comparison_profit is not None:
        if comparison_profit >= float(profit_lock):
            exit_triggered = True
            if market_snapshot["betSummary"]["unmatchedCount"] > 0 and config["cancel_unmatched_before_exit"]:
                actions.append(
                    {
                        "kind": "CANCEL_UNMATCHED",
                        "marketId": market_snapshot["marketId"],
                        "betRefs": [
                            str(lookup_ci(bet, "betRef"))
                            for bet in market_snapshot["betSummary"]["unmatchedBets"]
                            if lookup_ci(bet, "betRef") is not None
                        ],
                    }
                )
            if green_whole_market and market_snapshot["betSummary"]["exposedSelectionCount"] > 1:
                actions.append(
                    {
                        "kind": "GREEN_ALL",
                        "marketId": market_snapshot["marketId"],
                        "priceOption": str(plan.get("greenPriceOption") or config["default_green_price_option"]),
                    }
                )
                reasons.append(f"profit_lock_green_all:{comparison_profit}")
            elif selection_ok:
                actions.append(
                    {
                        "kind": "CLOSE_TRADE",
                        "marketId": market_snapshot["marketId"],
                        "selectionId": selection_id,
                        "withGreening": with_greening,
                        "priceOption": str(plan.get("closePriceOption") or config["default_close_price_option"]),
                    }
                )
                reasons.append(f"profit_lock_close_trade:{comparison_profit}")
        elif comparison_profit <= float(stop_loss):
            exit_triggered = True
            if market_snapshot["betSummary"]["unmatchedCount"] > 0 and config["cancel_unmatched_before_exit"]:
                actions.append(
                    {
                        "kind": "CANCEL_UNMATCHED",
                        "marketId": market_snapshot["marketId"],
                        "betRefs": [
                            str(lookup_ci(bet, "betRef"))
                            for bet in market_snapshot["betSummary"]["unmatchedBets"]
                            if lookup_ci(bet, "betRef") is not None
                        ],
                    }
                )
            if green_whole_market and market_snapshot["betSummary"]["exposedSelectionCount"] > 1:
                actions.append(
                    {
                        "kind": "GREEN_ALL",
                        "marketId": market_snapshot["marketId"],
                        "priceOption": str(plan.get("greenPriceOption") or config["default_green_price_option"]),
                    }
                )
                reasons.append(f"stop_loss_green_all:{comparison_profit}")
            elif selection_ok:
                actions.append(
                    {
                        "kind": "CLOSE_TRADE",
                        "marketId": market_snapshot["marketId"],
                        "selectionId": selection_id,
                        "withGreening": with_greening,
                        "priceOption": str(plan.get("closePriceOption") or config["default_close_price_option"]),
                    }
                )
                reasons.append(f"stop_loss_close_trade:{comparison_profit}")

    if (
        not exit_triggered
        and not already_hedged
        and selection_actionable
        and reduce_on_profit is not None
        and comparison_profit is not None
        and comparison_profit >= reduce_on_profit
    ):
        gate("reduce_price_present", reduce_price is not None, reduce_price)
        gate("matched_position_exists", matched_stake > 0, matched_stake)
        if reduce_price is not None and matched_stake > 0 and reduce_side:
            raw_stake = matched_stake * float(reduce_fraction)
            if entry_price is not None:
                raw_stake = matched_stake * float(entry_price) / float(reduce_price) * float(reduce_fraction)
            capped_stake = allowed_place_stake(raw_stake, current_balance, config, plan)
            gate("reduce_stake_positive", capped_stake > 0, capped_stake)
            if capped_stake > 0:
                actions.append(
                    {
                        "kind": "REDUCE_EXPOSURE",
                        "marketId": market_snapshot["marketId"],
                        "selectionId": selection_id,
                        "side": reduce_side,
                        "price": round(float(reduce_price), 3),
                        "stake": capped_stake,
                    }
                )
                reasons.append(f"reduce_on_profit:{comparison_profit}")

    if not exit_triggered and not actions and not already_hedged and selection_actionable and allow_supplement and target_stake is not None:
        delta_stake = round(target_stake - matched_stake - unmatched_stake, 2)
        gate("supplement_has_existing_position", allow_fresh_entry or matched_stake > 0, f"matched={matched_stake}")
        gate("supplement_delta_positive", delta_stake > 0, delta_stake)
        if side == "BACK":
            supplement_price_ok = current_price is not None and (
                max_supplement_price is None or float(current_price) <= float(max_supplement_price)
            )
            gate("supplement_price_ok", supplement_price_ok, f"{current_price} <= {max_supplement_price}")
        else:
            supplement_price_ok = current_price is not None and (
                min_supplement_price is None or float(current_price) >= float(min_supplement_price)
            )
            gate("supplement_price_ok", supplement_price_ok, f"{current_price} >= {min_supplement_price}")
        if allow_fresh_entry or matched_stake > 0:
            capped_stake = allowed_place_stake(delta_stake, current_balance, config, plan)
            gate("supplement_stake_positive", capped_stake > 0, capped_stake)
            if (
                current_price is not None
                and delta_stake > 0
                and capped_stake > 0
                and supplement_price_ok
            ):
                actions.append(
                    {
                        "kind": "SUPPLEMENT",
                        "marketId": market_snapshot["marketId"],
                        "selectionId": selection_id,
                        "side": side,
                        "price": round(float(current_price), 3),
                        "stake": capped_stake,
                    }
                )
                reasons.append(f"supplement_to_target:{target_stake}")

    if not actions and already_hedged:
        reasons.append("already_hedged")
    elif not actions:
        reasons.append("hold_monitor_only")

    return {
        "label": str(plan.get("label") or f"{market_snapshot['marketId']}:{selection_id or 'market'}"),
        "marketId": market_snapshot["marketId"],
        "marketName": market_snapshot["marketName"],
        "marketStatus": market_snapshot["marketStatus"],
        "inPlay": market_snapshot["inPlay"],
        "selectionId": selection_id,
        "selectionName": selection_name(meta, prices, selection_id),
        "side": side,
        "matchedStake": round(matched_stake, 2),
        "opposingMatchedStake": round(opposing_matched_stake, 2),
        "unmatchedStake": round(unmatched_stake, 2),
        "opposingUnmatchedStake": round(opposing_unmatched_stake, 2),
        "currentPrice": current_price,
        "entryPrice": entry_price,
        "maxSupplementPrice": max_supplement_price,
        "minSupplementPrice": min_supplement_price,
        "preview": preview,
        "gateTrace": gate_trace,
        "actions": actions,
        "suppressedActions": suppressed,
        "reasons": reasons,
    }


def suppress_repeated_execute_actions(
    decision: dict[str, Any],
    state: dict[str, Any],
    cooldown_seconds: int,
) -> dict[str, Any]:
    if not decision["actions"] or cooldown_seconds <= 0:
        return decision
    label_state = ((state.get("labels") or {}).get(decision["label"])) or {}
    kept: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = list(decision.get("suppressedActions") or [])
    now_ts = now_local().timestamp()
    for action in decision["actions"]:
        signature = action_signature(action)
        last_sig = label_state.get("lastActionSignature")
        last_ts = safe_float(label_state.get("lastActionTimestamp"))
        if last_sig == signature and last_ts is not None and now_ts - last_ts < cooldown_seconds:
            suppressed.append(
                {
                    "action": action,
                    "reason": f"cooldown_active:{int(cooldown_seconds - (now_ts - last_ts))}",
                }
            )
        else:
            kept.append(action)
    decision["actions"] = kept
    decision["suppressedActions"] = suppressed
    if not kept and "hold_monitor_only" not in decision["reasons"]:
        decision["reasons"].append("cooldown_suppressed_actions")
    return decision


def update_state_for_action(state: dict[str, Any], label: str, action: dict[str, Any]) -> None:
    labels = state.setdefault("labels", {})
    labels[label] = {
        "lastActionAt": now_local().isoformat(),
        "lastActionTimestamp": now_local().timestamp(),
        "lastActionSignature": action_signature(action),
    }


def execute_action(action: dict[str, Any]) -> dict[str, Any]:
    kind = action["kind"]
    if kind in {"SUPPLEMENT", "REDUCE_EXPOSURE"}:
        return place_bet(action["marketId"], action["selectionId"], action["side"], action["price"], action["stake"])
    if kind == "CANCEL_UNMATCHED":
        bet_refs = [str(ref) for ref in action.get("betRefs", []) if ref]
        return cancel_bets(action["marketId"], bet_refs or None)
    if kind == "GREEN_ALL":
        return green_all_selections(action["marketId"], action["priceOption"])
    if kind == "CLOSE_TRADE":
        return close_trade(
            action["marketId"],
            action["selectionId"],
            bool(action.get("withGreening", True)),
            action["priceOption"],
            safe_float(action.get("fixedPrice")),
        )
    raise ValueError(f"Unsupported action kind: {kind}")


def cycle_output_path(cycle_ts: str) -> Path:
    return OUTPUTS_ROOT / f"live-trade-manager-{cycle_ts}.json"


def heartbeat_summary(cycle_payload: dict[str, Any], cycle_number: int) -> dict[str, Any]:
    decisions = [
        decision
        for market in cycle_payload["markets"]
        for decision in market["decisions"]
    ]
    highlights = [decision_highlight(decision, cycle_payload.get("config") or {}) for decision in decisions]
    highlights = sorted(highlights, key=highlight_priority)
    return {
        "generatedAt": cycle_payload["generatedAt"],
        "cycle": cycle_number,
        "mode": cycle_payload["mode"],
        "balance": cycle_payload["balance"],
        "monitoredMarketCount": cycle_payload["monitoredMarketCount"],
        "inPlayMarketCount": sum(1 for market in cycle_payload["markets"] if market["snapshot"]["inPlay"]),
        "candidateActionCount": sum(len(decision["actions"]) for decision in decisions),
        "suppressedActionCount": sum(len(decision.get("suppressedActions") or []) for decision in decisions),
        "executedActionCount": cycle_payload["executedActionCount"],
        "highlights": highlights[:5],
    }


def compact_market_name(name: str | None) -> str:
    if not name:
        return "unknown"
    text = name.replace(" - Match Odds", "").strip()
    return text if len(text) <= 32 else text[:29].rstrip() + "..."


def decision_blocker(decision: dict[str, Any]) -> str:
    failed = [item["name"] for item in decision.get("gateTrace", []) if not item.get("passed")]
    if "in_play" in failed:
        return "wait:in_play"
    if "market_open" in failed:
        return "wait:market"
    if "price_present" in failed:
        return "wait:price"
    if "supplement_price_ok" in failed:
        return "wait:price"
    if "supplement_delta_positive" in failed:
        return "at_target"
    if "supplement_has_existing_position" in failed:
        return "wait:position"
    reasons = decision.get("reasons") or []
    return str(reasons[0]) if reasons else "hold"


def action_label(action: dict[str, Any]) -> str:
    kind = str(action.get("kind") or "")
    if kind == "SUPPLEMENT":
        return f"ADD {action.get('stake')} @ {action.get('price')}"
    if kind == "REDUCE_EXPOSURE":
        return f"REDUCE {action.get('stake')} @ {action.get('price')}"
    if kind == "CLOSE_TRADE":
        return "CLOSE"
    if kind == "GREEN_ALL":
        return "GREEN_ALL"
    if kind == "CANCEL_UNMATCHED":
        return "CANCEL_UNMATCHED"
    return kind or "ACTION"


def decision_highlight(decision: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    actions = decision.get("actions") or []
    preview = decision.get("preview") or {}
    target = None
    for plan in config.get("plans", []):
        if isinstance(plan, dict) and plan.get("label") == decision.get("label"):
            target = safe_float(plan.get("targetStake"))
            break
    matched = safe_float(decision.get("matchedStake")) or 0.0
    if actions:
        status = "ACTION"
        message = ";".join(action_label(action) for action in actions[:2])
    else:
        status = "WAIT"
        message = decision_blocker(decision)
    return {
        "status": status,
        "market": compact_market_name(decision.get("marketName")),
        "inPlay": bool(decision.get("inPlay")),
        "selection": decision.get("selectionName") or decision.get("selectionId"),
        "side": decision.get("side"),
        "matchedStake": matched,
        "targetStake": target,
        "price": decision.get("currentPrice"),
        "closeProfit": preview.get("closeProfGreen"),
        "greenProfit": preview.get("greenAllProfit"),
        "message": message,
    }


def highlight_priority(item: dict[str, Any]) -> tuple[int, float]:
    if item.get("status") == "ACTION":
        return (0, 0.0)
    close_profit = safe_float(item.get("closeProfit"))
    green_profit = safe_float(item.get("greenProfit"))
    value = close_profit if close_profit is not None else green_profit
    return (1, abs(value or 0.0) * -1)


def format_status_line(summary: dict[str, Any], inplay_only: bool = False, limit: int = 3) -> str:
    timestamp = str(summary.get("generatedAt") or "")
    clock = timestamp[11:19] if len(timestamp) >= 19 else timestamp
    balance = safe_float(summary.get("balance")) or 0.0
    head = (
        f"monitoring | {clock} | mode={summary.get('mode')} | "
        f"balance={balance:.2f} | markets={summary.get('monitoredMarketCount')} | "
        f"inPlay={summary.get('inPlayMarketCount')} | "
        f"actions={summary.get('candidateActionCount')} | "
        f"suppressed={summary.get('suppressedActionCount')} | "
        f"executed={summary.get('executedActionCount')}"
    )
    highlights = summary.get("highlights") or []
    if inplay_only:
        highlights = [item for item in highlights if item.get("inPlay")]
    if not highlights:
        return head
    parts = [head]
    for item in highlights[:limit]:
        profit = item.get("closeProfit")
        if profit is None:
            profit = item.get("greenProfit")
        profit_text = "p/l=n/a" if profit is None else f"p/l={float(profit):.2f}"
        target = item.get("targetStake")
        stake_text = f"{item.get('matchedStake')}/{target}" if target is not None else str(item.get("matchedStake"))
        parts.append(
            f"{item.get('status')} | {item.get('market')} | {item.get('selection')} | "
            f"{item.get('message')} | stake={stake_text} | price={item.get('price')} | {profit_text}"
        )
    return "\n".join(parts)


def run_cycle(
    config: dict[str, Any],
    execute: bool,
    state: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    cycle_started = now_local()
    balance = ba_balance()
    current_balance = safe_float(balance.get("balance")) or safe_float(balance.get("result", {}).get("balance")) or 0.0

    markets = get_markets()
    prices = get_market_prices()
    market_by_id = market_map(markets)
    prices_by_id = market_map(prices)
    plans = [plan for plan in config.get("plans", []) if isinstance(plan, dict)]
    market_id_filter = {str(item) for item in config.get("_market_id_filter", []) if item}
    if market_id_filter:
        plans = [plan for plan in plans if str(plan.get("marketId")) in market_id_filter]

    candidate_market_ids = {str(plan.get("marketId")) for plan in plans if plan.get("marketId")}
    for market_id, price_row in prices_by_id.items():
        has_exposure = market_has_exposure(price_row)
        if market_id_filter and market_id not in market_id_filter and not (
            config["always_monitor_exposure"] and has_exposure
        ):
            continue
        if has_exposure:
            candidate_market_ids.add(market_id)

    monitored_markets: list[dict[str, Any]] = []
    action_log: list[dict[str, Any]] = []

    for market_id in sorted(candidate_market_ids):
        meta = market_by_id.get(market_id)
        price_row = prices_by_id.get(market_id)
        if meta is None and price_row is None:
            continue
        bets_payload = get_market_bets(market_id)
        snapshot = build_market_snapshot(meta, price_row, bets_payload)
        plans_for_market = [plan for plan in plans if str(plan.get("marketId")) == market_id]

        if config["watch_inplay_only"] and not snapshot["inPlay"] and not plans_for_market:
            continue

        decision_rows: list[dict[str, Any]] = []
        if plans_for_market:
            for plan in plans_for_market:
                decision = evaluate_plan(plan, config, snapshot, meta, price_row, current_balance)
                if execute:
                    decision = suppress_repeated_execute_actions(decision, state, int(config["action_cooldown_seconds"]))
                decision_rows.append(decision)
                if execute:
                    for action in decision["actions"]:
                        result = execute_action(action)
                        action_log.append(
                            {
                                "marketId": market_id,
                                "marketName": snapshot["marketName"],
                                "label": decision["label"],
                                "action": action,
                                "result": result,
                            }
                        )
                        update_state_for_action(state, decision["label"], action)
        else:
            decision_rows.append(
                {
                    "label": f"{market_id}:monitor_only",
                    "marketId": market_id,
                    "marketName": snapshot["marketName"],
                    "marketStatus": snapshot["marketStatus"],
                    "inPlay": snapshot["inPlay"],
                    "selectionId": None,
                    "selectionName": None,
                    "side": None,
                    "matchedStake": snapshot["betSummary"]["matchedStakeTotal"],
                    "unmatchedStake": snapshot["betSummary"]["unmatchedStakeTotal"],
                    "currentPrice": None,
                    "entryPrice": None,
                    "maxSupplementPrice": None,
                    "minSupplementPrice": None,
                    "preview": {
                        "greenAllProfit": safe_float(lookup_ci(price_row, "greenAllProfit", "greeningProfit")),
                        "closeProfGreen": None,
                        "selectionProfit": safe_float(lookup_ci(price_row, "profit")),
                    },
                    "gateTrace": [],
                    "actions": [],
                    "suppressedActions": [],
                    "reasons": ["exposure_detected_without_plan"],
                }
            )

        monitored_markets.append(
            {
                "snapshot": snapshot,
                "decisions": decision_rows,
            }
        )

    return {
        "generatedAt": cycle_started.isoformat(),
        "mode": "execute" if execute else "dry-run",
        "balance": current_balance,
        "config": config,
        "monitoredMarketCount": len(monitored_markets),
        "executedActionCount": len(action_log),
        "markets": monitored_markets,
        "actionLog": action_log,
    }, state


def main() -> int:
    parser = argparse.ArgumentParser(description="Bet Angel live order and position management engine.")
    parser.add_argument("--config", default=str(CONFIG_PATH), help="Path to local JSON config.")
    parser.add_argument("--execute", action="store_true", help="Actually submit Bet Angel actions.")
    parser.add_argument("--cycles", type=int, default=None, help="Override max cycles. Use 0 for heartbeat loop.")
    parser.add_argument("--poll", type=int, default=None, help="Override polling interval seconds.")
    parser.add_argument("--status-line", action="store_true", help="Print one compact heartbeat status line per cycle.")
    parser.add_argument("--status-inplay-only", action="store_true", help="Only print in-play market hints in status-line output.")
    parser.add_argument("--status-limit", type=int, default=3, help="Maximum market hint lines to print after the summary line.")
    parser.add_argument("--market-id", action="append", default=[], help="Limit monitoring/execution to one market ID. Repeatable.")
    args = parser.parse_args()

    ensure_dirs()
    config_path = Path(args.config)
    config = ensure_config_file(config_path)
    if args.cycles is not None:
        config["max_cycles"] = args.cycles
    if args.poll is not None:
        config["poll_seconds"] = max(1, args.poll)
    if args.market_id:
        config["_market_id_filter"] = [str(item) for item in args.market_id]

    execute = bool(config.get("execute")) and bool(config.get("ai_automation_enabled")) and args.execute
    heartbeat_file = resolve_path(str(config.get("heartbeat_file") or ""), OUTPUTS_ROOT / "live-order-engine-heartbeat-latest.json")
    heartbeat_log_file = resolve_path(str(config.get("heartbeat_log_file") or ""), OUTPUTS_ROOT / "live-order-engine-heartbeat.jsonl")
    state_file = resolve_path(str(config.get("state_file") or ""), SYSTEM_ROOT / "live_trade_manager_state.json")
    state = load_state(state_file)

    max_cycles = int(config["max_cycles"])
    infinite = max_cycles == 0
    cycle = 0
    runs: list[dict[str, Any]] = []
    last_run: dict[str, Any] | None = None

    try:
        while infinite or cycle < max_cycles:
            cycle += 1
            cycle_payload, state = run_cycle(config, execute, state)
            cycle_payload["cycle"] = cycle
            last_run = cycle_payload
            summary = heartbeat_summary(cycle_payload, cycle)
            if not infinite and max_cycles <= 200:
                runs.append(cycle_payload)
            if config["heartbeat_mode"]:
                write_json(heartbeat_file, summary)
                append_jsonl(heartbeat_log_file, summary)
            if args.status_line:
                print(
                    format_status_line(
                        summary,
                        inplay_only=args.status_inplay_only,
                        limit=max(0, args.status_limit),
                    ),
                    flush=True,
                )
            if config["heartbeat_mode"] or execute:
                save_state(state_file, state)
            if not infinite and cycle >= max_cycles:
                break
            time.sleep(config["poll_seconds"])
    except KeyboardInterrupt:
        pass

    final_payload = {
        "generatedAt": now_local().isoformat(),
        "mode": "execute" if execute else "dry-run",
        "configPath": str(config_path),
        "runCount": cycle,
        "heartbeatMode": config["heartbeat_mode"],
        "storedRunHistory": bool(runs),
    }
    if runs:
        final_payload["runs"] = runs
    if last_run is not None:
        final_payload["lastRun"] = last_run

    ts = now_local().strftime("%Y-%m-%d-%H%M%S")
    out_path = cycle_output_path(ts)
    write_json(out_path, final_payload)
    if not args.status_line:
        print(json.dumps({"output": str(out_path), "mode": final_payload["mode"], "runCount": cycle}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
