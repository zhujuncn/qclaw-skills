#!/usr/bin/env python3
"""
baf_generator.py - Bet Angel Guardian .baf file generator and parser.

Generates standard Guardian automation rules for goal signal detection.
Parses existing .baf files to extract rule structure.

Usage:
    python baf_generator.py generate --type match_odds --output signal_goals.baf
    python baf_generator.py generate --type over_under --tick-threshold 15 -o ou.baf
    python baf_generator.py parse "C:\\path\\to\\file.baf"
    python baf_generator.py parse "C:\\path\\to\\file.baf" --json
"""

import argparse
import json
import re


# ─── GENERATORS ──────────────────────────────────────────────────────────

def _rule_header(rule_id, name, market_cat, signal_action, signal_name="goal",
                 signal_value="1"):
    """Build common rule header lines."""
    return [
        rule_id, name, "SIGNAL_ONLY", "2",
        "False", "False", "1", "False", "False",
        "3000", "90", "5", "2", str(market_cat), "",
        "CUSTOM_BELOW", "", "10", "10", "FIXED",
        "False", "False", "False", "False", "False", "", "", "False", "", "",
        signal_action, signal_name, signal_value, "NONE", "",
        "1", "True", "2",
    ]


def _condition_time_unsuspended(seconds):
    """TIME_UNSUSPENDED condition block."""
    return [
        "TIME_UNSUSPENDED",
        f"Time since unsuspended > {seconds} seconds",
        "2", "GREATER", str(seconds),
    ]


def _condition_historic_relative_odds(comparison, history_seconds, offset_dir,
                                       tick_threshold):
    """HISTORIC_RELATIVE_ODDS condition block."""
    op = "PLUS" if offset_dir == "+" else "MINUS"
    comp_word = "GREATER" if comparison == ">" else "LESS"
    return [
        "HISTORIC_RELATIVE_ODDS",
        (f"Last Traded price {comparison} Last Traded price "
         f"{history_seconds} seconds ago {offset_dir} {tick_threshold} ticks"),
        "18", "True", "2", "1", "", "LTP",
        "True", "0", comp_word, "True", "2", "1", "", "LTP",
        "False", str(history_seconds), op, str(tick_threshold), "TICKS",
    ]


def generate_match_odds(tick_threshold=10, history_seconds=65, guard_delay=60):
    """Generate Match Odds goal signal .baf (2 rules: INCREMENT + DECREMENT)."""
    L = ["6.0", "", "2"]

    # Rule 0001: price drops -> INCREMENT (this team scored)
    L += _rule_header("0001", "Signal Goal", 3, "INCREMENT")
    L += _condition_time_unsuspended(guard_delay)
    L += _condition_historic_relative_odds(">", history_seconds, "+", tick_threshold)
    L += [""]

    # Rule 0002: price rises -> DECREMENT (opponent scored)
    L += _rule_header("0002", "Signal Goal for Opposing Team", 3, "DECREMENT")
    L += _condition_time_unsuspended(guard_delay)
    L += _condition_historic_relative_odds("<", history_seconds, "-", tick_threshold)
    L += [""]

    return "\n".join(L)


def generate_over_under(tick_threshold=15, history_seconds=65, guard_delay=60):
    """Generate Over/Under goal signal .baf (1 rule: INCREMENT)."""
    L = ["6.0", "", "1"]

    # Rule 0001: Over price drops -> INCREMENT (goal scored)
    L += _rule_header("0001", "Goal for overs", 2, "INCREMENT")
    L += _condition_time_unsuspended(guard_delay)
    L += _condition_historic_relative_odds("<", history_seconds, "-", tick_threshold)
    L += [""]

    return "\n".join(L)


# ─── PARSER ──────────────────────────────────────────────────────────────

_SIGNAL_ACTIONS = {"INCREMENT", "DECREMENT", "SET"}
_COND_TYPES = {"TIME_UNSUSPENDED", "HISTORIC_RELATIVE_ODDS",
               "MARKET_STATUS", "SELECTION_STATUS", "SUSPENDED", "IN_PLAY"}


def parse_baf(filepath):
    """Parse a .baf file into structured dict.

    Strategy: Find SIGNAL_ONLY markers to identify rules, then parse backwards
    for rule header and forwards for signal/conditions.
    """
    with open(filepath, "r", encoding="utf-8-sig") as f:
        lines = [l.rstrip("\r\n") for l in f]

    result = {"version": None, "rules": []}
    n = len(lines)

    # Version
    result["version"] = lines[0].strip() if n > 0 else None

    # Find all SIGNAL_ONLY markers (each indicates start of a rule header)
    rule_starts = []
    for idx in range(n):
        if lines[idx].strip() == "SIGNAL_ONLY":
            # Rule header is 3 lines before: id, name, type
            if idx >= 2:
                rule_starts.append(idx - 2)

    # Parse each rule
    for ri, rs in enumerate(rule_starts):
        rule = {
            "id": lines[rs].strip() if rs < n else "",
            "name": lines[rs + 1].strip() if rs + 1 < n else "",
            "type": lines[rs + 2].strip() if rs + 2 < n else "",
            "signal": None,
            "conditions": [],
        }

        # Find next rule start or end of file
        next_rs = rule_starts[ri + 1] if ri + 1 < len(rule_starts) else n

        # Scan for signal action and condition types within rule range
        signal_line = None
        cond_lines = []
        for idx in range(rs + 3, next_rs):
            stripped = lines[idx].strip()
            if stripped in _SIGNAL_ACTIONS:
                signal_line = idx
            elif stripped in _COND_TYPES:
                cond_lines.append(idx)

        # Parse signal
        if signal_line is not None:
            rule["signal"] = {
                "action": lines[signal_line].strip(),
                "name": lines[signal_line + 1].strip() if signal_line + 1 < n else "",
                "value": lines[signal_line + 2].strip() if signal_line + 2 < n else "",
                "reset": lines[signal_line + 3].strip() if signal_line + 3 < n else "",
            }

        # Parse conditions
        for ci, cl in enumerate(cond_lines):
            desc = lines[cl + 1].strip() if cl + 1 < n else ""
            ctype = lines[cl].strip()
            cond = {"type": ctype, "description": desc}

            # Params: from desc+1 to next condition or next rule
            if ci + 1 < len(cond_lines):
                param_end = cond_lines[ci + 1]
            else:
                param_end = next_rs

            params = [lines[pi].strip() for pi in range(cl + 2, param_end)]
            while params and params[-1] == "":
                params.pop()
            cond["raw_params"] = params

            # Extract meaningful values
            non_empty = [p for p in params if p]
            if ctype == "TIME_UNSUSPENDED" and len(non_empty) >= 3:
                cond["comparison"] = non_empty[1]
                cond["value"] = non_empty[2]

            elif ctype == "HISTORIC_RELATIVE_ODDS":
                m = re.search(r"(\d+) seconds ago\s*([+\-])\s*(\d+) ticks", desc)
                if m:
                    cond["lookback_seconds"] = int(m.group(1))
                    cond["offset_direction"] = m.group(2)
                    cond["tick_offset"] = int(m.group(3))
                cond["comparison"] = "GREATER" if ">" in desc else "LESS"

            rule["conditions"].append(cond)

        # Condition logic: find after signal section (skip blanks, look for True/False)
        if signal_line is not None:
            sl = signal_line + 4  # after signal reset line
            while sl < n and lines[sl].strip() == "":
                sl += 1
            # sl = group_count, sl+1 = logic, sl+2 = cond_count
            if sl + 1 < n:
                logic_line = lines[sl + 1].strip()
                rule["condition_logic"] = "AND" if logic_line == "True" else "OR"

        result["rules"].append(rule)

    return result


def format_parsed(parsed):
    """Human-readable output of parsed .baf."""
    out = [f"Version: {parsed['version']}", f"Rules: {len(parsed['rules'])}", ""]

    for rule in parsed["rules"]:
        out.append(f"=== Rule {rule['id']}: {rule['name']} ===")
        out.append(f"  Type: {rule['type']}")
        if rule.get("signal"):
            s = rule["signal"]
            out.append(f"  Signal: {s['action']} {s['name']} {s['value']} (reset: {s['reset']})")

        logic = rule.get("condition_logic", "AND")
        out.append(f"  Conditions ({logic}):")
        for j, c in enumerate(rule["conditions"], 1):
            detail = ""
            if c["type"] == "TIME_UNSUSPENDED":
                detail = f"-> {c.get('comparison','?')} {c.get('value','?')}s"
            elif c["type"] == "HISTORIC_RELATIVE_ODDS":
                sec = c.get("lookback_seconds", "?")
                off = f"{c.get('offset_direction','?')}{c.get('tick_offset','?')}"
                detail = f"-> Lookback: {sec}s, Offset: {off} ticks"
            out.append(f"    {j}. [{c['type']}] {c['description']} {detail}")
        out.append("")

    return "\n".join(out)


# ─── MAIN ────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Bet Angel .baf Generator/Parser")
    sub = ap.add_subparsers(dest="cmd")

    pg = sub.add_parser("generate", help="Generate .baf file")
    pg.add_argument("--type", choices=["match_odds", "over_under"], required=True)
    pg.add_argument("--tick-threshold", type=int, default=None)
    pg.add_argument("--history-seconds", type=int, default=65)
    pg.add_argument("--guard-delay", type=int, default=60)
    pg.add_argument("--output", "-o")

    pp = sub.add_parser("parse", help="Parse .baf file")
    pp.add_argument("filepath")
    pp.add_argument("--json", action="store_true")

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        return

    if args.cmd == "generate":
        tick = args.tick_threshold or (10 if args.type == "match_odds" else 15)
        fn = generate_match_odds if args.type == "match_odds" else generate_over_under
        content = fn(tick, args.history_seconds, args.guard_delay)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Written: {args.output}")
            print(f"  Type: {args.type} | Ticks: {tick} | "
                  f"Lookback: {args.history_seconds}s | Guard: {args.guard_delay}s")
        else:
            print(content)

    elif args.cmd == "parse":
        parsed = parse_baf(args.filepath)
        if args.json:
            for r in parsed["rules"]:
                for c in r.get("conditions", []):
                    c.pop("raw_params", None)
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
        else:
            print(format_parsed(parsed))


if __name__ == "__main__":
    main()
