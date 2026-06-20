#!/usr/bin/env python3
"""Betfair-first team-name index and matcher.

The Betfair/Bet Angel market name is the canonical name. External names from
CGMBet26, Sofascore, DJYY, FlashScore, or historical aliases are mapped to it.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "references" / "betfair_name_index.json"
SOURCE_FILES = [
    Path(__file__).resolve().parents[1] / "references" / "name_overrides.json",
    Path(r"C:\Users\zhuju\.qclaw\workspace\betangel\ba_team_aliases.json"),
    Path(r"C:\Users\zhuju\.codex\skills\football-council\data\team_aliases.json"),
    Path(r"C:\Users\zhuju\.qclaw\skills\football-council\data\team_aliases.json"),
    Path(r"C:\Users\zhuju\.codex\skills\football-council\data\ba_teams_snapshot.json"),
    Path(r"C:\Users\zhuju\.qclaw\skills\football-council\data\ba_teams_snapshot.json"),
]


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().replace("&", " and ")
    value = re.sub(r"\b(fc|sc|cf|fk|afc|bk)\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        try:
            return json.loads(path.read_text(encoding="cp1252"))
        except Exception:
            return None


def add_alias(index: dict[str, str], alias: str, canonical: str) -> None:
    alias_n = normalize(alias)
    canonical = str(canonical).strip()
    if not alias_n or not canonical:
        return
    index.setdefault(alias_n, canonical)
    index.setdefault(normalize(canonical), canonical)


def build_index(source_files: list[Path] | None = None) -> dict[str, Any]:
    source_files = source_files or SOURCE_FILES
    aliases: dict[str, str] = {}
    sources: list[str] = []

    for path in source_files:
        data = load_json(path)
        if data is None:
            continue
        sources.append(str(path))
        if isinstance(data, dict):
            for k, v in data.items():
                if str(k).startswith("_"):
                    continue
                if isinstance(v, str):
                    add_alias(aliases, k, v)
                elif isinstance(v, dict):
                    canonical = v.get("canonical") or v.get("ba") or v.get("name")
                    if canonical:
                        add_alias(aliases, k, canonical)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    add_alias(aliases, item, item)
                elif isinstance(item, dict):
                    canonical = item.get("ba_name") or item.get("ba") or item.get("name") or item.get("team")
                    if canonical:
                        if " - Match Odds" in canonical:
                            left = canonical.split(" - Match Odds", 1)[0]
                            for side in left.split(" v "):
                                add_alias(aliases, side, side)
                        else:
                            add_alias(aliases, canonical, canonical)
                    for key in ("match", "home", "away", "external_home", "external_away"):
                        if item.get(key) and canonical and " v " not in str(item[key]):
                            add_alias(aliases, str(item[key]), str(item[key]))

    return {
        "version": 1,
        "canonical": "Betfair/Bet Angel market display names",
        "sources": sources,
        "count": len(aliases),
        "aliases": dict(sorted(aliases.items())),
    }


def load_index(path: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    data = load_json(path)
    if isinstance(data, dict) and isinstance(data.get("aliases"), dict):
        return data
    return build_index()


def canonical_team(name: str, index: dict[str, Any] | None = None) -> str:
    index = index or load_index()
    aliases = index.get("aliases", {})
    return aliases.get(normalize(name), str(name).strip())


def canonical_pair(home: str, away: str, index: dict[str, Any] | None = None) -> tuple[str, str]:
    index = index or load_index()
    return canonical_team(home, index), canonical_team(away, index)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Betfair-first football name index")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--lookup", help="Look up one team name")
    args = parser.parse_args()

    if args.lookup:
        idx = load_index(Path(args.output))
        print(canonical_team(args.lookup, idx))
        return 0

    idx = build_index()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(idx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "aliases": idx["count"], "sources": len(idx["sources"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
