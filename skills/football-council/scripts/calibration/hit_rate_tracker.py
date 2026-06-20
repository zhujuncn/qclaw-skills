import sqlite3, json, os, sys
from collections import defaultdict
from datetime import datetime

DB = r'C:\Users\zhuju\AppData\Roaming\CGMBetSystem\CGMBetStats_v3.db'
CAL_DIR = r'C:\Users\zhuju\.self-improving\calibration'
os.makedirs(CAL_DIR, exist_ok=True)

FALLBACK_DRAW = 0.305  # 从全局数据实测


def get_season_league_mapping() -> dict:
    """
    通过同 Round 的多场比赛识别联赛
    同一 Round 内的所有比赛 → 同一联赛
    用 team → league 的团队名映射建立标准
    """
    conn = sqlite3.connect(DB, timeout=10)
    cur = conn.cursor()
    
    # 已知的 team → league 标准映射（持续扩展）
    KNOWN_TEAMS = {
        # Chile
        'U de Concepcion': 'Chile Primera Division',
        'Universidad Catolica': 'Chile Primera Division',
        'U de Chile': 'Chile Primera Division',
        'Palestino': 'Chile Primera Division',
        'Everton': 'Chile Primera Division',
        'Colo-Colo': 'Chile Primera Division',
        'Huachipato': 'Chile Primera Division',
        'Cobresal': 'Chile Primera Division',
        'Nublense': 'Chile Primera Division',
        # Norway
        'Viking': 'Norwegian Eliteserien',
        'Ham-Kam': 'Norwegian Eliteserien',
        'Start': 'Norwegian Eliteserien',
        'Kristiansund': 'Norwegian Eliteserien',
        'Sandefjord': 'Norwegian Eliteserien',
        'Valerenga': 'Norwegian Eliteserien',
        'Rosenborg': 'Norwegian Eliteserien',
        'Lillestrom': 'Norwegian Eliteserien',
        'Tromsoe': 'Norwegian Eliteserien',
        'Fredrikstad': 'Norwegian Eliteserien',
        'Molde': 'Norwegian Eliteserien',
        'Brann': 'Norwegian Eliteserien',
        'Aalesund': 'Norwegian Eliteserien',
        'Bodo/Glimt': 'Norwegian Eliteserien',
        'Sarpsborg': 'Norwegian Eliteserien',
        # Brazil Serie B
        'Vasco da Gama': 'Brazil Serie B',
        'Santos': 'Brazil Serie B',
        'Corinthians': 'Brazil Serie B',
        'Palmeiras': 'Brazil Serie B',
        'Botafogo RJ': 'Brazil Serie B',
        'Coritiba': 'Brazil Serie B',
        'Vitoria': 'Brazil Serie B',
        'Remo': 'Brazil Serie B',
    }
    
    # 从最近完成的比赛 (Season 26, StatusCode=0) 建立 team→league 映射
    cur.execute("""
        SELECT m.HomeTeamId, t1.Name as home, m.AwayTeamId, t2.Name as away, m.HomeGoals, m.AwayGoals
        FROM Matches m
        JOIN Teams t1 ON m.HomeTeamId = t1.Id
        JOIN Teams t2 ON m.AwayTeamId = t2.Id
        WHERE m.StatusCode IN (1, 2) AND m.Season=26
    """)
    
    team_to_league = {}
    for hid, home, aid, away, hg, ag in cur.fetchall():
        for team, league in KNOWN_TEAMS.items():
            if home and (home in team or team in home):
                team_to_league[home] = league
            if away and (away in team or team in away):
                team_to_league[away] = league
    
    conn.close()
    return team_to_league, KNOWN_TEAMS


def get_global_draw_rates() -> dict:
    """
    计算全局（跨联赛）Draw/Home/Away 胜率
    StatusCode=1 和 2 = 真实比分（已完成的比赛）
    """
    conn = sqlite3.connect(DB, timeout=15)
    cur = conn.cursor()
    
    # StatusCode=1 和 2 有真实比分
    cur.execute("""
        SELECT HomeGoals, AwayGoals 
        FROM Matches 
        WHERE StatusCode IN (1, 2)
          AND HomeGoals IS NOT NULL 
          AND AwayGoals IS NOT NULL
    """)
    
    total = draws = home_wins = away_wins = over25 = btts_yes = 0
    for hg, ag in cur:
        total += 1
        if hg == ag:
            draws += 1
        elif hg > ag:
            home_wins += 1
        else:
            away_wins += 1
        if hg + ag > 2.5:
            over25 += 1
        if hg > 0 and ag > 0:
            btts_yes += 1
    
    conn.close()
    
    if total == 0:
        return {}
    
    return {
        'total': total,
        'draws': draws, 'home_wins': home_wins, 'away_wins': away_wins,
        'over25': over25, 'btts_yes': btts_yes,
        'draw_rate': round(draws/total, 4),
        'home_rate': round(home_wins/total, 4),
        'away_rate': round(away_wins/total, 4),
        'over25_rate': round(over25/total, 4),
        'btts_rate': round(btts_yes/total, 4),
        'implied_draw_odds': round(total/draws, 2) if draws > 0 else 999,
        'implied_home_odds': round(total/home_wins, 2) if home_wins > 0 else 999,
        'implied_away_odds': round(total/away_wins, 2) if away_wins > 0 else 999,
    }


def get_recent_season_draw_rates() -> dict:
    """
    当前赛季 (Season=26) 分联赛 Draw 率
    通过已知的 team→league 映射统计
    """
    known_leagues = {
        'Chile Primera Division': ['U de Concepcion','Universidad Catolica','U de Chile','Union La Calera',
                                    'Palestino','Everton','O\u014dHiggins','Coquimbo','Limache','D. Concepcion',
                                    'Deportes La Serena','A. Italiano','Huachipato','Nublense','Cobresal',
                                    'Colo-Colo','Audax Italiano'],
        'Norwegian Eliteserien': ['Viking','Ham-Kam','Start','Kristiansund','Sandefjord','Valerenga',
                                   'Rosenborg','KFUM Oslo','Lillestrom','Tromsoe','Fredrikstad','Molde',
                                   'Brann','Aalesund','Bodo/Glimt','Sarpsborg'],
        'Brazil Serie B': ['Vasco da Gama','Vitoria','Santos','Botafogo RJ','Remo','Corinthians',
                           'Palmeiras','Coritiba'],
    }
    
    league_teams = {v: k for k, vv in known_leagues.items() for v in vv}
    
    conn = sqlite3.connect(DB, timeout=15)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT t1.Name as home, t2.Name as away, m.HomeGoals, m.AwayGoals
        FROM Matches m
        JOIN Teams t1 ON m.HomeTeamId = t1.Id
        JOIN Teams t2 ON m.AwayTeamId = t2.Id
        WHERE m.StatusCode IN (1, 2) AND m.Season=26
    """)
    
    league_stats = defaultdict(lambda: {'total': 0, 'draws': 0, 'home': 0, 'away': 0, 'teams': set()})
    unmatched = 0
    
    for home, away, hg, ag in cur:
        identified = False
        for team_set_name, teams in known_leagues.items():
            for t in teams:
                if home and (home in t or t in home):
                    league_stats[team_set_name]['teams'].add(home)
                    identified = True
                if away and (away in t or t in away):
                    league_stats[team_set_name]['teams'].add(away)
                    identified = True
                if identified:
                    league_stats[team_set_name]['total'] += 1
                    if hg == ag:
                        league_stats[team_set_name]['draws'] += 1
                    elif hg > ag:
                        league_stats[team_set_name]['home'] += 1
                    else:
                        league_stats[team_set_name]['away'] += 1
                    break
            if identified:
                break
        
        if not identified:
            unmatched += 1
    
    conn.close()
    
    # 计算比率
    result = {}
    for league, stats in league_stats.items():
        t = stats['total']
        if t >= 5:
            dr = stats['draws'] / t
            result[league] = {
                'total': t, 'draws': stats['draws'],
                'home_wins': stats['home'], 'away_wins': stats['away'],
                'draw_rate': round(dr, 4),
                'home_rate': round(stats['home']/t, 4),
                'away_rate': round(stats['away']/t, 4),
                'implied_draw_odds': round(t/stats['draws'], 2) if stats['draws'] > 0 else 999,
                'teams': sorted(stats['teams']),
            }
    
    print(f"  匹配 {len(result)} 个联赛, {sum(s['total'] for s in league_stats.values())} 场比赛")
    print(f"  未匹配 {unmatched} 场比赛")
    return result


def save_calibration() -> dict:
    print("正在计算 CGMBet26 全局基准...")
    overall = get_global_draw_rates()
    print(f"  全局 Draw 率: {overall['draw_rate']*100:.1f}% (n={overall['total']:,})")
    
    print("\n正在计算分联赛 Draw 率...")
    league_stats = get_recent_season_draw_rates()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    sorted_leagues = sorted(league_stats.items(),
        key=lambda x: x[1]['draw_rate'], reverse=True)
    
    output = {
        'updated': today,
        'overall': overall,
        'leagues': {k: v for k, v in sorted_leagues},
        'fallback': {
            'draw_rate': FALLBACK_DRAW,
            'implied_draw_odds': round(1/FALLBACK_DRAW, 2),
            'source': 'CGMBet26 global average (no LeagueId in Matches table)',
        },
        'note': 'Matches table has no LeagueId FK. League stats are estimated via team name matching to known leagues.'
    }
    
    out_path = os.path.join(CAL_DIR, 'league_calibration.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    return output


def print_report():
    print("=" * 70)
    print("  CGMBet26 联赛平局率校准报告")
    print("=" * 70)
    
    try:
        with open(os.path.join(CAL_DIR, 'league_calibration.json')) as f:
            data = json.load(f)
        print(f"更新时间: {data.get('updated', 'N/A')}")
    except:
        print("无本地缓存，请先运行 update")
        return

    ov = data.get('overall', {})
    if ov:
        print(f"\n全局基准 (n={ov.get('total',0):,} 场):")
        print(f"  Draw: {ov.get('draw_rate',0)*100:.1f}% → implied {ov.get('implied_draw_odds',999):.2f}x")
        print(f"  Home: {ov.get('home_rate',0)*100:.1f}% → implied {ov.get('implied_home_odds',999):.2f}x")
        print(f"  Away: {ov.get('away_rate',0)*100:.1f}% → implied {ov.get('implied_away_odds',999):.2f}x")
        print(f"  O2.5: {ov.get('over25_rate',0)*100:.1f}%")
        print(f"  BTTS: {ov.get('btts_rate',0)*100:.1f}%")
    
    leagues = data.get('leagues', {})
    if leagues:
        print(f"\n分联赛 Draw 率 (Season 26):\n")
        print(f"  {'联赛':<30} {'场次':>5} {'Draw%':>7} {'Implied':>8} {'Home%':>7} {'Away%':>7}")
        print("  " + "-" * 70)
        for league, s in leagues.items():
            print(f"  {league:<30} {s['total']:>5} {s['draw_rate']*100:>5.1f}% "
                  f"{s['implied_draw_odds']:>8.2f}  {s['home_rate']*100:>5.1f}%  {s['away_rate']*100:>5.1f}%")
    else:
        print("\n⚠️  Matches 表无 LeagueId，无法按联赛统计")
    
    fb = data.get('fallback', {})
    print(f"\nFallback Draw Rate: {fb.get('draw_rate', FALLBACK_DRAW)*100:.1f}%")
    print(f"  (用于未识别联赛，使用全局平均)")
    print(f"\n⚠️  博弈论提醒:")
    print(f"  - 这是历史统计均值，不是预测值")
    print(f"  - 需配合 Poisson xG 建模才能产生真正的价值信号")
    print(f"  - 当前全局 {FALLBACK_DRAW*100:.1f}% 平局率 = 3.28x implied")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print_report()
    elif sys.argv[1] == 'update':
        result = save_calibration()
        print("\n✅ 校准完成!")
        print_report()
    elif sys.argv[1] == 'get' and len(sys.argv) > 2:
        import json
        with open(os.path.join(CAL_DIR, 'league_calibration.json')) as f:
            data = json.load(f)
        league = sys.argv[2]
        info = data.get('leagues', {}).get(league, {})
        if info:
            print(f"{league}: Draw={info['draw_rate']*100:.1f}% (n={info['total']})")
        else:
            print(f"{league}: 未找到，使用 fallback {FALLBACK_DRAW*100:.1f}%")
    else:
        print("用法: hit_rate_tracker.py [update|report|get <league>]")