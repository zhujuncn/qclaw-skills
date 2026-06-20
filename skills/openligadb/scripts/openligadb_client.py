#!/usr/bin/env python3
"""OpenLigaDB API Client - 德国足球数据查询工具

Usage:
    python openligadb_client.py current bl1
    python openligadb_client.py matchday bl1 2024 11
    python openligadb_client.py season bl1 2024
    python openligadb_client.py table bl1 2024
    python openligadb_client.py scorers bl1 2024
    python openligadb_client.py teams bl1 2024
    python openligadb_client.py groups bl1 2024
    python openligadb_client.py match 39738
    python openligadb_client.py nextmatch <leagueId> <teamId>
    python openligadb_client.py head2head <teamId1> <teamId2>
    python openligadb_client.py lastchange bl1 2024 11
    python openligadb_client.py leagues
    python openligadb_client.py sports
"""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime


BASE_URL = "https://api.openligadb.de"


def _fetch(path: str, timeout: int = 15) -> dict | list:
    """Fetch JSON from OpenLigaDB API."""
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}", file=sys.stderr)
        return None


class OpenLigaDB:
    """OpenLigaDB API client."""

    # ── 比赛数据 ──────────────────────────────────────

    def get_current_matches(self, league_shortcut: str) -> list:
        """获取当前轮次比赛 (GET /getmatchdata/{leagueShortcut})"""
        return _fetch(f"/getmatchdata/{league_shortcut}")

    def get_matchday(self, league_shortcut: str, season: int, group_order_id: int) -> list:
        """获取指定轮次比赛 (GET /getmatchdata/{leagueShortcut}/{leagueSeason}/{groupOrderId})"""
        return _fetch(f"/getmatchdata/{league_shortcut}/{season}/{group_order_id}")

    def get_season_matches(self, league_shortcut: str, season: int) -> list:
        """获取整个赛季比赛 (GET /getmatchdata/{leagueShortcut}/{leagueSeason})"""
        return _fetch(f"/getmatchdata/{league_shortcut}/{season}")

    def get_team_matches(self, league_shortcut: str, season: int, team_name: str) -> list:
        """获取某队在某赛季的比赛 (GET /getmatchdata/{leagueShortcut}/{leagueSeason}/{teamFilterstring})"""
        return _fetch(f"/getmatchdata/{league_shortcut}/{season}/{team_name}")

    def get_match_by_id(self, match_id: int) -> dict:
        """按 ID 获取比赛 (GET /getmatchdata/{matchId})"""
        return _fetch(f"/getmatchdata/{match_id}")

    def get_head2head(self, team_id1: int, team_id2: int) -> list:
        """两队历史交锋 (GET /getmatchdata/{teamId1}/{teamId2})"""
        return _fetch(f"/getmatchdata/{team_id1}/{team_id2}")

    # ── 下一场/最后一场 ─────────────────────────────────

    def get_next_match_by_league_team(self, league_id: int, team_id: int) -> dict:
        """获取某队下一场比赛 (GET /getnextmatchbyleagueteam/{leagueId}/{teamId})"""
        return _fetch(f"/getnextmatchbyleagueteam/{league_id}/{team_id}")

    def get_next_match_by_shortcut(self, league_shortcut: str) -> dict:
        """获取联赛下一场比赛 (GET /getnextmatchbyleagueshortcut/{leagueShortcut})"""
        return _fetch(f"/getnextmatchbyleagueshortcut/{league_shortcut}")

    def get_last_match_by_league_team(self, league_id: int, team_id: int) -> dict:
        """获取某队最后一场比赛 (GET /getlastmatchbyleagueteam/{leagueId}/{teamId})"""
        return _fetch(f"/getlastmatchbyleagueteam/{league_id}/{team_id}")

    def get_last_match_by_shortcut(self, league_shortcut: str) -> dict:
        """获取联赛最后一场比赛 (GET /getlastmatchbyleagueshortcut/{leagueShortcut})"""
        return _fetch(f"/getlastmatchbyleagueshortcut/{league_shortcut}")

    # ── 轮次/分组 ──────────────────────────────────────

    def get_current_group(self, league_shortcut: str) -> dict:
        """获取当前轮次 (GET /getcurrentgroup/{leagueShortcut})"""
        return _fetch(f"/getcurrentgroup/{league_shortcut}")

    def get_available_groups(self, league_shortcut: str, season: int) -> list:
        """获取所有轮次 (GET /getavailablegroups/{leagueShortcut}/{leagueSeason})"""
        return _fetch(f"/getavailablegroups/{league_shortcut}/{season}")

    # ── 积分榜/射手榜/球队 ──────────────────────────────

    def get_league_table(self, league_shortcut: str, season: int) -> list:
        """获取积分榜 (GET /getbltable/{leagueShortcut}/{leagueSeason})"""
        return _fetch(f"/getbltable/{league_shortcut}/{season}")

    def get_goal_getters(self, league_shortcut: str, season: int) -> list:
        """获取射手榜 (GET /getgoalgetters/{leagueShortcut}/{leagueSeason})"""
        return _fetch(f"/getgoalgetters/{league_shortcut}/{season}")

    def get_teams(self, league_shortcut: str, season: int) -> list:
        """获取球队列表 (GET /getavailableteams/{leagueShortcut}/{leagueSeason})"""
        return _fetch(f"/getavailableteams/{league_shortcut}/{season}")

    # ── 元数据 ─────────────────────────────────────────

    def get_last_change_date(self, league_shortcut: str, season: int, group_order_id: int) -> str:
        """获取最后变更时间 (GET /getlastchangedate/{leagueShortcut}/{leagueSeason}/{groupOrderId})"""
        return _fetch(f"/getlastchangedate/{league_shortcut}/{season}/{group_order_id}")

    def get_available_leagues(self) -> list:
        """获取所有可用联赛 (GET /getavailableleagues)"""
        return _fetch("/getavailableleagues")

    def get_available_sports(self) -> list:
        """获取所有运动类型 (GET /getavailablesports)"""
        return _fetch("/getavailablesports")

    def get_result_infos(self, league_id: int) -> list:
        """获取联赛结果类型 (GET /getresultinfos/{leagueId})"""
        return _fetch(f"/getresultinfos/{league_id}")


# ── 格式化输出辅助函数 ──────────────────────────────────

def _fmt_match(m: dict) -> str:
    """格式化单场比赛信息"""
    t1 = m.get("team1", {}).get("teamName", "?")
    t2 = m.get("team2", {}).get("teamName", "?")
    dt = m.get("matchDateTime", "?")[:16]
    finished = m.get("matchIsFinished", False)

    # 获取比分
    results = m.get("matchResults", [])
    score_str = ""
    if results:
        # 找 Endergebnis (resultTypeID=2)
        end_result = next((r for r in results if r.get("resultTypeID") == 2), None)
        if end_result:
            score_str = f" {end_result['pointsTeam1']}:{end_result['pointsTeam2']}"
        elif results:
            r = results[-1]
            score_str = f" {r['pointsTeam1']}:{r['pointsTeam2']}"

    status = "✅" if finished else "⏳"
    return f"  {status} {dt}  {t1} vs {t2}{score_str}"


def _fmt_table_row(t: dict, rank: int) -> str:
    """格式化积分榜行"""
    name = t.get("teamName", "?")
    pts = t.get("points", 0)
    won = t.get("won", 0)
    draw = t.get("draw", 0)
    lost = t.get("lost", 0)
    goals = t.get("goals", 0)
    opp_goals = t.get("opponentGoals", 0)
    goal_diff = goals - opp_goals
    matches = t.get("matches", 0)
    return f"  {rank:>2}. {name:<30} {matches:>2}场 {won}胜{draw}平{lost}负 {goals}:{opp_goals} ({goal_diff:+d}) {pts}分"


def _fmt_scorer(s: dict, rank: int) -> str:
    """格式化射手榜行"""
    name = s.get("goalGetterName", "?")
    goals = s.get("goalCount", s.get("goalGetterGoals", 0))
    team = s.get("teamName", "")
    team_str = f" ({team})" if team else ""
    return f"  {rank:>2}. {name}{team_str} - {goals}球"


# ── CLI 入口 ──────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    api = OpenLigaDB()
    cmd = sys.argv[1].lower()

    if cmd == "current" and len(sys.argv) >= 3:
        league = sys.argv[2]
        data = api.get_current_matches(league)
        if data:
            group = data[0].get("group", {}) if data else {}
            print(f"=== {league.upper()} 当前轮次 (第{group.get('groupOrderID','?')}轮) ===")
            for m in data:
                print(_fmt_match(m))

    elif cmd == "matchday" and len(sys.argv) >= 5:
        league, season, goid = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
        data = api.get_matchday(league, season, goid)
        if data:
            print(f"=== {league.upper()} {season}赛季 第{goid}轮 ===")
            for m in data:
                print(_fmt_match(m))

    elif cmd == "season" and len(sys.argv) >= 4:
        league, season = sys.argv[2], int(sys.argv[3])
        data = api.get_season_matches(league, season)
        if data:
            print(f"=== {league.upper()} {season}赛季 ({len(data)}场比赛) ===")
            for m in data:
                print(_fmt_match(m))

    elif cmd == "table" and len(sys.argv) >= 4:
        league, season = sys.argv[2], int(sys.argv[3])
        data = api.get_league_table(league, season)
        if data:
            print(f"=== {league.upper()} {season}赛季 积分榜 ===")
            for i, t in enumerate(data, 1):
                print(_fmt_table_row(t, i))

    elif cmd == "scorers" and len(sys.argv) >= 4:
        league, season = sys.argv[2], int(sys.argv[3])
        data = api.get_goal_getters(league, season)
        if data:
            print(f"=== {league.upper()} {season}赛季 射手榜 (Top 20) ===")
            for i, s in enumerate(data[:20], 1):
                print(_fmt_scorer(s, i))

    elif cmd == "teams" and len(sys.argv) >= 4:
        league, season = sys.argv[2], int(sys.argv[3])
        data = api.get_teams(league, season)
        if data:
            print(f"=== {league.upper()} {season}赛季 球队 ===")
            for t in data:
                print(f"  [{t.get('teamId')}] {t.get('teamName')}")

    elif cmd == "groups" and len(sys.argv) >= 4:
        league, season = sys.argv[2], int(sys.argv[3])
        data = api.get_available_groups(league, season)
        if data:
            print(f"=== {league.upper()} {season}赛季 轮次列表 ===")
            for g in data:
                print(f"  第{g.get('groupOrderID')}轮: {g.get('groupName')}")

    elif cmd == "match" and len(sys.argv) >= 3:
        match_id = int(sys.argv[2])
        data = api.get_match_by_id(match_id)
        if data:
            print(f"=== 比赛 #{match_id} ===")
            print(_fmt_match(data))
            for r in data.get("matchResults", []):
                print(f"    {r.get('resultName')}: {r.get('pointsTeam1')}:{r.get('pointsTeam2')}")

    elif cmd == "nextmatch" and len(sys.argv) >= 4:
        league_id, team_id = int(sys.argv[2]), int(sys.argv[3])
        data = api.get_next_match_by_league_team(league_id, team_id)
        if data:
            print("=== 下一场比赛 ===")
            print(_fmt_match(data))

    elif cmd == "head2head" and len(sys.argv) >= 4:
        t1, t2 = int(sys.argv[2]), int(sys.argv[3])
        data = api.get_head2head(t1, t2)
        if data:
            print(f"=== 历史交锋 ({len(data)}场) ===")
            for m in data:
                print(_fmt_match(m))

    elif cmd == "lastchange" and len(sys.argv) >= 5:
        league, season, goid = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
        data = api.get_last_change_date(league, season, goid)
        if data:
            print(f"最后变更时间: {data}")

    elif cmd == "leagues":
        data = api.get_available_leagues()
        if data:
            print(f"=== 可用联赛 ({len(data)}) ===")
            for lg in data:
                print(f"  [{lg.get('leagueId')}] {lg.get('leagueName')} ({lg.get('leagueShortcut')}) S{lg.get('leagueSeason')}")

    elif cmd == "sports":
        data = api.get_available_sports()
        if data:
            print(f"=== 运动类型 ({len(data)}) ===")
            for sp in data:
                print(f"  [{sp.get('sportID')}] {sp.get('sportName')}")

    else:
        print(f"未知命令或参数不足: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
