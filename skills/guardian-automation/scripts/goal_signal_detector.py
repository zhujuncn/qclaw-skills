#!/usr/bin/env python3
"""
goal_signal_detector.py - Bet Angel API Goal Signal Detector

Monitors LTP (Last Traded Price) changes to detect goals in football matches.
Replicates Guardian automation signal logic via Python + Bet Angel API.

Usage:
    python goal_signal_detector.py monitor <market_id> [options]
    python goal_signal_detector.py test <market_id> [options]
    python goal_signal_detector.py multi <id1> <id2> ... [options]
"""

import requests
import json
import time
import argparse
import threading
import subprocess
from datetime import datetime, timezone, timedelta
from collections import deque

BASE = "http://localhost:9000"
MARKETS = f"{BASE}/api/markets/v1.0"
BETTING = f"{BASE}/api/betting/v1.0"
GUARDIAN = f"{BASE}/api/guardian/v1.0"
TZ = timezone(timedelta(hours=3))  # Bucharest


def post(endpoint, payload=None):
    try:
        r = requests.post(f"{BASE}{endpoint}", json=payload or {}, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def get_ltps(market_id):
    """Get LTP for all selections in a market."""
    post(f"{GUARDIAN}/displayMarket", {"marketId": str(market_id)})
    time.sleep(0.2)

    prices = post(f"{MARKETS}/getMarketPrices", {
        "marketId": str(market_id),
        "dataRequired": ["BEST_PRICE_ONLY"]
    })

    if isinstance(prices, dict) and prices.get("status") == "OK":
        markets = prices.get("result", {}).get("markets", [])
        for m in markets:
            if str(m.get("id")) == str(market_id):
                sels = m.get("selections", [])
                ltps = {}
                # selections can be list or dict depending on API version
                if isinstance(sels, dict):
                    items = sels.items()
                elif isinstance(sels, list):
                    items = [(str(s.get("id", "")), s) for s in sels]
                else:
                    return None
                for sid, sd in items:
                    back = sd.get("back1", {})
                    p = back.get("prc", 0)
                    if p and p > 0:
                        ltps[str(sid)] = p
                return ltps

    return None


def get_market_name(market_id):
    """Get market name from getMarkets."""
    r = post(f"{MARKETS}/getMarkets", {"dataRequired": ["SELECTION_NAMES"]})
    if isinstance(r, dict) and r.get("status") == "OK":
        markets = r.get("result", {}).get("markets", [])
        for m in markets:
            if str(m.get("id")) == str(market_id):
                return m.get("name", "Unknown")
    return "Unknown"


# ─── Tick conversion (Betfair tick table) ───────────────────────────────

TICK_TABLE = []
def _build_ticks():
    p = 1.0
    while p <= 1000:
        TICK_TABLE.append(round(p, 2))
        if p < 2: p += 0.01
        elif p < 3: p += 0.02
        elif p < 4: p += 0.05
        elif p < 6: p += 0.1
        elif p < 10: p += 0.2
        elif p < 20: p += 0.5
        elif p < 30: p += 1.0
        elif p < 50: p += 2.0
        else: p += 5.0

_build_ticks()
_TICK_MAP = {v: i for i, v in enumerate(TICK_TABLE)}


def to_ticks(price):
    """Convert odds to tick index."""
    if price <= 0:
        return 0
    # Exact match
    if price in _TICK_MAP:
        return _TICK_MAP[price]
    # Nearest
    best_i = 0
    best_d = abs(TICK_TABLE[0] - price)
    for i, t in enumerate(TICK_TABLE):
        d = abs(t - price)
        if d < best_d:
            best_d = d
            best_i = i
    return best_i


def tick_diff(p_before, p_after):
    """Tick difference (positive = price went up)."""
    return to_ticks(p_after) - to_ticks(p_before)


# ─── Monitor ─────────────────────────────────────────────────────────────

class GoalMonitor:
    def __init__(self, market_id, market_type="match_odds",
                 tick_threshold=10, history_seconds=65,
                 guard_delay=60, check_interval=3,
                 on_goal=None, known_goals=0, verbose=False):
        self.market_id = str(market_id)
        self.market_type = market_type
        self.tick_threshold = tick_threshold
        self.history_seconds = history_seconds
        self.guard_delay = guard_delay
        self.check_interval = check_interval
        self.on_goal = on_goal
        self.goal_count = known_goals
        self.market_name = ""
        self.running = False
        self.start_time = None
        self.verbose = verbose
        self._tick_count = 0
        self._prev_ltps = None
        max_len = max(200, history_seconds * 3 // check_interval)
        self.history = deque(maxlen=max_len)  # (timestamp, {sid: ltp})
        self.last_ltps = None

    def _log(self, msg):
        ts = datetime.now(TZ).strftime("%H:%M:%S")
        print(f"[{ts}] {msg}", flush=True)

    def _snapshot(self, ltps):
        """Take a snapshot of current LTPs."""
        if ltps:
            self.history.append((time.time(), dict(ltps)))
            self.last_ltps = ltps

    def _detect(self):
        """Check for goal signal based on LTP change."""
        if not self.history or not self.last_ltps:
            return None

        now = time.time()
        cutoff = now - self.history_seconds

        # Find oldest entry within history window
        old_entry = None
        for ts, ltps in self.history:
            if ts >= cutoff:
                break
            old_entry = (ts, ltps)

        if not old_entry:
            return None

        _, old_ltps = old_entry
        signals = []

        for sid, cur_p in self.last_ltps.items():
            old_p = old_ltps.get(sid)
            if not old_p or old_p <= 0 or cur_p <= 0:
                continue

            dt = tick_diff(old_p, cur_p)  # positive = price up

            if self.market_type == "match_odds":
                # Price UP = this team conceded (opponent scored)
                if dt > self.tick_threshold:
                    signals.append(("decrement", sid, dt, old_p, cur_p))
                # Price DOWN = this team scored
                elif dt < -self.tick_threshold:
                    signals.append(("increment", sid, dt, old_p, cur_p))

            elif self.market_type == "over_under":
                # Price DOWN = goal scored (Over price drops on goals)
                if dt < -self.tick_threshold:
                    signals.append(("increment", sid, dt, old_p, cur_p))

        return signals if signals else None

    def _fire_goal(self, direction, sid, dt, p_before, p_after):
        """Fire goal event."""
        if direction == "increment":
            self.goal_count += 1
        else:
            self.goal_count -= 1

        event = {
            "event": "goal_detected",
            "market": self.market_name,
            "market_id": self.market_id,
            "direction": direction,
            "selection_id": sid,
            "ltp_before": p_before,
            "ltp_after": p_after,
            "tick_change": dt,
            "goal_count": self.goal_count,
            "timestamp": datetime.now(TZ).isoformat()
        }

        self._log(
            f"GOAL! {direction.upper()} | Sel {sid} | "
            f"{p_before:.2f} -> {p_after:.2f} ({dt:+d} ticks) | "
            f"Total: {self.goal_count}"
        )
        print(json.dumps(event))

        if self.on_goal:
            try:
                self.on_goal(event)
            except Exception as e:
                self._log(f"Callback error: {e}")

    def tick(self):
        """Single check cycle. Returns list of goal events or None."""
        ltps = get_ltps(self.market_id)
        if ltps:
            self._snapshot(ltps)

            # Verbose: show LTP changes
            self._tick_count += 1
            if self.verbose and self._prev_ltps:
                parts = []
                for sid, p in ltps.items():
                    old = self._prev_ltps.get(sid, 0)
                    if old > 0 and p > 0:
                        dt = tick_diff(old, p)
                        if dt != 0:
                            parts.append(f"Sel{sid} {old:.2f}->{p:.2f}({dt:+d})")
                if parts:
                    self._log(f"LTP: {' | '.join(parts)}")
            elif self.verbose and not self._prev_ltps:
                parts = [f"Sel{k}={v:.2f}" for k, v in ltps.items()]
                self._log(f"LTP init: {' | '.join(parts)}")
            self._prev_ltps = dict(ltps)

        # Guard delay
        if self.start_time and (time.time() - self.start_time) < self.guard_delay:
            remaining = self.guard_delay - (time.time() - self.start_time)
            if self.verbose and self._tick_count % 10 == 1:
                self._log(f"Guard active, {remaining:.0f}s remaining")
            return None

        results = self._detect()
        if results:
            events = []
            for direction, sid, dt, pb, pa in results:
                self._fire_goal(direction, sid, dt, pb, pa)
                events.append(direction)
            return events
        return None

    def run(self, duration=None):
        """Main loop."""
        self.market_name = get_market_name(self.market_id)
        self.running = True
        self.start_time = time.time()

        self._log(f"Monitor: {self.market_name}")
        self._log(f"ID: {self.market_id} | Type: {self.market_type}")
        self._log(f"Threshold: {self.tick_threshold} ticks | Lookback: {self.history_seconds}s")
        self._log(f"Guard: {self.guard_delay}s | Interval: {self.check_interval}s")
        if self.verbose:
            self._log(f"Verbose: ON (showing LTP changes)")
        print("-" * 60)

        start_wall = time.time()
        detected = 0

        try:
            while self.running:
                if duration and (time.time() - start_wall) > duration:
                    self._log(f"Test duration reached ({duration}s).")
                    break

                events = self.tick()
                if events:
                    detected += len(events)

                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self._log("Stopped by user.")
        finally:
            self.running = False

        self._log(f"Done. Goals detected: {detected} | Total count: {self.goal_count}")


def main():
    p = argparse.ArgumentParser(description="Bet Angel Goal Signal Detector")
    sub = p.add_subparsers(dest="cmd")

    # monitor
    pm = sub.add_parser("monitor", help="Monitor a market for goal signals")
    pm.add_argument("market_id")
    pm.add_argument("--market-type", choices=["match_odds", "over_under"], default="match_odds")
    pm.add_argument("--tick-threshold", type=int, default=10)
    pm.add_argument("--history-seconds", type=int, default=65)
    pm.add_argument("--guard-delay", type=int, default=60)
    pm.add_argument("--check-interval", type=int, default=3)
    pm.add_argument("--on-goal", help="Shell command on goal ({market_id}, {goal_count})")
    pm.add_argument("--goal-count", type=int, default=0)
    pm.add_argument("--verbose", "-v", action="store_true", help="Show LTP changes each tick")

    # test (60s)
    pt = sub.add_parser("test", help="Test mode (60s)")
    pt.add_argument("market_id")
    pt.add_argument("--market-type", choices=["match_odds", "over_under"], default="match_odds")
    pt.add_argument("--tick-threshold", type=int, default=10)
    pt.add_argument("--history-seconds", type=int, default=65)
    pt.add_argument("--check-interval", type=int, default=3)
    pt.add_argument("--on-goal", help="Shell command on goal")
    pt.add_argument("--verbose", "-v", action="store_true", help="Show LTP changes each tick")

    # multi
    pml = sub.add_parser("multi", help="Monitor multiple markets")
    pml.add_argument("markets", nargs="+")
    pml.add_argument("--market-type", choices=["match_odds", "over_under"], default="match_odds")
    pml.add_argument("--tick-threshold", type=int, default=10)
    pml.add_argument("--history-seconds", type=int, default=65)
    pml.add_argument("--guard-delay", type=int, default=60)
    pml.add_argument("--check-interval", type=int, default=3)

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return

    if args.cmd in ("monitor", "test"):
        kw = dict(
            market_id=args.market_id,
            market_type=args.market_type,
            tick_threshold=args.tick_threshold,
            history_seconds=args.history_seconds,
            check_interval=args.check_interval,
        )

        if args.cmd == "test":
            kw["guard_delay"] = 0  # no guard in test mode
        else:
            kw["guard_delay"] = args.guard_delay
            kw["known_goals"] = args.goal_count
        kw["verbose"] = args.verbose

        mon = GoalMonitor(**kw)

        # Callback
        on_goal_cmd = getattr(args, "on_goal", None)
        if on_goal_cmd:
            def cb(event):
                cmd = on_goal_cmd.replace("{market_id}", event["market_id"]) \
                                 .replace("{goal_count}", str(event["goal_count"]))
                subprocess.Popen(cmd, shell=True)
            mon.on_goal = cb

        dur = 60 if args.cmd == "test" else None
        mon.run(duration=dur)

    elif args.cmd == "multi":
        monitors = []
        threads = []
        for mid in args.markets:
            m = GoalMonitor(
                market_id=mid,
                market_type=args.market_type,
                tick_threshold=args.tick_threshold,
                history_seconds=args.history_seconds,
                guard_delay=args.guard_delay,
                check_interval=args.check_interval,
            )
            monitors.append(m)
            t = threading.Thread(target=m.run, daemon=True)
            threads.append(t)

        for t in threads:
            t.start()
        try:
            while any(t.is_alive() for t in threads):
                time.sleep(1)
        except KeyboardInterrupt:
            for m in monitors:
                m.running = False
        for t in threads:
            t.join(timeout=5)


if __name__ == "__main__":
    main()
