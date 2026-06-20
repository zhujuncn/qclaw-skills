#!/usr/bin/env python3
"""Unified CGMBet26 + Bet Angel football betting advisor.

Advice-only by default. This script does not place bets.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import math
import sqlite3
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

try:
    from name_matcher import canonical_pair
except Exception:  # noqa: BLE001 - optional helper for older installs
    canonical_pair = None


DEFAULT_DB = r"C:\Users\zhuju\AppData\Roaming\CGMBetSystem\CGMBetStats_v3.db"
BA_BASE = "http://localhost:9000/api"
GLOBAL_DRAW_PROB = 0.262


@dataclass
class Recommendation:
    match_id: str
    date: str
    time: int | None
    league: str
    country: str
    home: str
    away: str
    selection: str
    side: str
    odds: float
    true_probability: float
    market_probability: float
    value_pct: float
    kelly_half: float
    suggested_stake: float
    tier: str
    action: str
    confidence: float
    reasons: list[str]
    risk_flags: list[str]
    ba_match: str | None = None
    ba_match_score: float | None = None


def post_json(url: str, payload: dict[str, Any], timeout: float = 10) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def ba_balance() -> dict[str, Any]:
    try:
        return post_json(f"{BA_BASE}/markets/v1.0/getBalance", {})
    except Exception as exc:  # noqa: BLE001 - CLI diagnostic
        return {"error": str(exc)}


def ba_markets() -> list[dict[str, Any]]:
    try:
        data = post_json(
            f"{BA_BASE}/markets/v1.0/getMarkets",
            {"dataRequired": ["ID", "NAME", "MARKET_START_TIME", "SELECTION_IDS", "SELECTION_NAMES"]},
            timeout=20,
        )
        return data.get("result", {}).get("markets", [])
    except Exception:
        return []


def normalize_name(value: str) -> str:
    value = value.lower()
    keep = []
    for ch in value:
        keep.append(ch if ch.isalnum() else " ")
    parts = [p for p in "".join(keep).split() if p not in {"fc", "sc", "cf", "fk", "ec", "ac"}]
    return " ".join(parts)


def category_tokens(value: str) -> set[str]:
    v = normalize_name(value)
    found = set()
    for token in ("u20", "u21", "u19", "res", "women", "w"):
        if token in v.split():
            found.add(token)
    return found


def split_ba_match_name(name: str) -> tuple[str, str] | None:
    base = name.replace(" - Match Odds", "")
    if " v " not in base:
        return None
    home, away = base.split(" v ", 1)
    return home.strip(), away.strip()


def match_ba_market(home: str, away: str, markets: list[dict[str, Any]]) -> tuple[str | None, float | None]:
    canonical_home, canonical_away = (canonical_pair(home, away) if canonical_pair else (home, away))
    best_name = None
    best_score = 0.0
    target_cats = category_tokens(home) | category_tokens(away)
    for market in markets:
        name = str(market.get("name", ""))
        if "Match Odds" not in name:
            continue
        pair = split_ba_match_name(name)
        if not pair:
            continue
        ba_home, ba_away = pair
        home_score = difflib.SequenceMatcher(None, normalize_name(canonical_home), normalize_name(ba_home)).ratio()
        away_score = difflib.SequenceMatcher(None, normalize_name(canonical_away), normalize_name(ba_away)).ratio()
        score = (home_score + away_score) / 2.0

        # Penalize category mismatches hard. A senior Criciuma match must not
        # resolve to Criciuma U20 just because the home name is close.
        ba_cats = category_tokens(ba_home) | category_tokens(ba_away)
        if ba_cats != target_cats:
            score -= 0.30

        if score > best_score:
            best_name = name
            best_score = score
    if best_score < 0.55:
        return None, None
    return best_name, round(best_score, 3)


def query_matches(db_path: str, date_value: str, days: int) -> list[sqlite3.Row]:
    start = dt.date.fromisoformat(date_value)
    end = start + dt.timedelta(days=max(days - 1, 0))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        sql = """
        SELECT
          m.MatchId, m.Date, m.Time, m.Status, m.StatusCode,
          ht.Name AS Home, at.Name AS Away,
          l.Name AS League, l.Country AS Country,
          o.Odd1, o.OddX, o.Odd2, o.OddO25, o.OddU25,
          r.EloHome, r.EloAway, r.FormHome, r.FormAway
        FROM Matches m
        JOIN Teams ht ON ht.Id = m.HomeTeamId
        JOIN Teams at ON at.Id = m.AwayTeamId
        LEFT JOIN Leagues l ON l.Id = substr(CAST(m.MatchId AS TEXT), 1, 2)
        LEFT JOIN Odds o ON o.MatchId = m.MatchId
        LEFT JOIN Ratings r ON r.MatchId = m.MatchId
        WHERE m.Date BETWEEN ? AND ?
        ORDER BY m.Date, m.Time
        """
        return conn.execute(sql, (start.isoformat(), end.isoformat())).fetchall()
    finally:
        conn.close()


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def estimate_probs(row: sqlite3.Row) -> dict[str, float]:
    elo_home = float(row["EloHome"] or 0)
    elo_away = float(row["EloAway"] or 0)
    form_home = float(row["FormHome"] or 0)
    form_away = float(row["FormAway"] or 0)

    if elo_home == 0 and elo_away == 0:
        home_strength = 0.5
    else:
        # 400 Elo points ~= strong favorite. Form nudges but does not dominate.
        diff = ((elo_home - elo_away) / 400.0) + ((form_home - form_away) / 80.0)
        home_strength = sigmoid(diff)

    draw = GLOBAL_DRAW_PROB
    non_draw = 1.0 - draw
    home = non_draw * home_strength
    away = non_draw * (1.0 - home_strength)
    return {"Home": home, "Draw": draw, "Away": away}


def kelly_half(prob: float, odds: float) -> float:
    if odds <= 1:
        return 0.0
    b = odds - 1.0
    q = 1.0 - prob
    kelly = (b * prob - q) / b
    return max(0.0, kelly * 0.5)


def classify(value_pct: float, kelly: float, odds: float, confidence: float, flags: list[str]) -> tuple[str, str]:
    if kelly <= 0:
        return "SKIP", "NO_EDGE"
    if odds < 2.0:
        return "SKIP", "LOW_ODDS_TRAP"
    if value_pct < 5:
        return "SKIP", "LOW_VALUE"
    if confidence < 0.55:
        return "WATCH", "LOW_CONFIDENCE"
    if flags:
        return "WATCH", "RISK_FLAG"
    if value_pct >= 20:
        return "BACK", "T1"
    if value_pct >= 10:
        return "BACK", "T2"
    return "WATCH", "MARGINAL"


def build_recommendations(
    rows: list[sqlite3.Row],
    bankroll: float,
    max_items: int,
    ba: bool,
) -> tuple[list[Recommendation], dict[str, Any]]:
    markets = ba_markets() if ba else []
    meta = {"ba_enabled": ba, "ba_markets": len(markets) if ba else None, "balance": ba_balance() if ba else None}
    recs: list[Recommendation] = []

    for row in rows:
        probs = estimate_probs(row)
        options = [
            ("Home", row["Home"], row["Odd1"], probs["Home"]),
            ("Draw", "Draw", row["OddX"], probs["Draw"]),
            ("Away", row["Away"], row["Odd2"], probs["Away"]),
        ]
        best: Recommendation | None = None
        ba_name, ba_score = match_ba_market(row["Home"], row["Away"], markets) if markets else (None, None)
        match_conf = ba_score if ba_score is not None else 0.65

        for label, selection, odds_raw, prob in options:
            if not odds_raw:
                continue
            odds = float(odds_raw)
            market_prob = 1.0 / odds if odds > 0 else 0.0
            value_pct = ((prob - market_prob) / market_prob * 100.0) if market_prob else -100.0
            kh = kelly_half(prob, odds)
            flags: list[str] = []
            reasons = [f"model p={prob:.1%}", f"market p={market_prob:.1%}", f"value={value_pct:.1f}%"]

            elo_home = float(row["EloHome"] or 0)
            elo_away = float(row["EloAway"] or 0)
            form_home = float(row["FormHome"] or 0)
            form_away = float(row["FormAway"] or 0)
            elo_diff = elo_home - elo_away
            form_diff = form_home - form_away
            if abs(elo_diff) > 100 and abs(form_diff) > 10 and (elo_diff * form_diff < 0):
                flags.append("strong Form-ELO divergence")
                reasons.append(f"ELO diff={elo_diff:.0f}, Form diff={form_diff:.0f}")

            if odds > 8:
                flags.append("high odds; reduce stake")
            if ba and not ba_name:
                flags.append("no Bet Angel market match")
            if ba_score is not None and ba_score < 0.75:
                flags.append(f"weak BA name match {ba_score:.2f}")

            action, tier = classify(value_pct, kh, odds, match_conf, flags)
            stake = round(bankroll * kh, 2)
            if odds >= 8:
                stake = round(stake * 0.5, 2)
            stake = min(stake, round(bankroll * 0.01, 2))

            rec = Recommendation(
                match_id=str(row["MatchId"]),
                date=str(row["Date"]),
                time=row["Time"],
                league=str(row["League"] or ""),
                country=str(row["Country"] or ""),
                home=str(row["Home"]),
                away=str(row["Away"]),
                selection=str(selection),
                side="BACK",
                odds=round(odds, 3),
                true_probability=round(prob, 4),
                market_probability=round(market_prob, 4),
                value_pct=round(value_pct, 2),
                kelly_half=round(kh, 4),
                suggested_stake=stake,
                tier=tier,
                action=action,
                confidence=round(match_conf, 3),
                reasons=reasons,
                risk_flags=flags,
                ba_match=ba_name,
                ba_match_score=ba_score,
            )
            if best is None or rec.value_pct > best.value_pct:
                best = rec
        if best:
            recs.append(best)

    recs.sort(key=lambda r: (r.action == "BACK", r.value_pct, r.kelly_half), reverse=True)
    return recs[:max_items], meta


def render_markdown(recs: list[Recommendation], meta: dict[str, Any]) -> str:
    lines = []
    lines.append("# Football Trading Advisor")
    if meta.get("balance"):
        balance = meta["balance"]
        if "error" in balance:
            lines.append(f"- Bet Angel balance: unavailable ({balance['error']})")
        else:
            lines.append(f"- Bet Angel balance response: {json.dumps(balance.get('result', balance), ensure_ascii=False)[:200]}")
    if meta.get("ba_enabled"):
        lines.append(f"- Bet Angel markets loaded: {meta.get('ba_markets')}")
    lines.append("")
    lines.append("| Action | Tier | Match | Pick | Odds | Value | Kelly(1/2) | Stake | Flags |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|---|")
    for r in recs:
        match = f"{r.home} v {r.away}"
        flags = "; ".join(r.risk_flags) if r.risk_flags else "-"
        lines.append(
            f"| {r.action} | {r.tier} | {match} | {r.side} {r.selection} | "
            f"{r.odds:.2f} | {r.value_pct:.1f}% | {r.kelly_half:.3f} | {r.suggested_stake:.2f} | {flags} |"
        )
    lines.append("")
    lines.append("Advice only. No bets were placed.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="CGMBet26 + Bet Angel football betting advisor")
    parser.add_argument("--db", default=DEFAULT_DB, help="CGMBet26 SQLite database path")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Start date YYYY-MM-DD")
    parser.add_argument("--days", type=int, default=1, help="Number of days to scan")
    parser.add_argument("--bankroll", type=float, default=1000.0, help="Bankroll used for stake sizing")
    parser.add_argument("--max", type=int, default=20, help="Maximum rows to output")
    parser.add_argument("--ba", action="store_true", help="Include Bet Angel API balance and market matching")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    db = Path(args.db)
    if not db.exists():
        print(json.dumps({"error": f"CGMBet26 DB not found: {db}"}, ensure_ascii=False), file=sys.stderr)
        return 2

    try:
        rows = query_matches(str(db), args.date, args.days)
        recs, meta = build_recommendations(rows, args.bankroll, args.max, args.ba)
    except (sqlite3.Error, ValueError, urllib.error.URLError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"meta": meta, "recommendations": [asdict(r) for r in recs]}, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(recs, meta))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
