#!/usr/bin/env python3
"""
Fetch and parse Sofascore match data for analysis.
v2.0 - Fixed statistics parsing to match actual API response format.
- API uses item['name'] not item['key']
- API uses item['home']/'away' not item['homeValue']/'awayValue']
- Values are strings ("7", "43%") requiring numeric parsing
- Statistics searched across ALL groups/periods, not just first
- Incidents use correct field names (incidentType, isHome, player.name)
- Added many more useful metrics
"""

import sys
import json
import re
from curl_cffi import requests


def parse_stat_value(val):
    """Parse a Sofascore statistic value to a number.
    Handles: "7", "43%", "5/12 (42%)", empty strings, None
    """
    if val is None:
        return 0
    val = str(val).strip()
    if not val or val == '-':
        return 0
    # Match percentage first: "43%" -> 43
    pct_match = re.search(r'(\d+)%', val)
    if pct_match:
        return int(pct_match.group(1))
    # Match plain number: "7" -> 7.0, "0.86" -> 0.86
    num_match = re.search(r'(\d+\.?\d*)', val)
    if num_match:
        return float(num_match.group(1))
    return 0


def find_stat(all_periods, search_name):
    """Find a statistic by name (case-insensitive partial match) across ALL groups and periods.
    Returns (home_value, away_value) or (0, 0) if not found.
    """
    search_lower = search_name.lower()
    for period_data in all_periods:
        for grp in period_data.get('groups', []):
            for item in grp.get('statisticsItems', []):
                item_name = item.get('name', '').lower()
                # Exact match or contains match
                if item_name == search_lower or search_lower in item_name:
                    h = parse_stat_value(item.get('home', ''))
                    a = parse_stat_value(item.get('away', ''))
                    return h, a
    return 0, 0


def fetch_match_data(match_id):
    """Fetch comprehensive match data from Sofascore API."""
    session = requests.Session(impersonate='chrome')
    base = 'https://api.sofascore.com/api/v1'

    try:
        # Core match data
        event_resp = session.get(f'{base}/event/{match_id}', timeout=15)
        event_resp.raise_for_status()
        event_data = event_resp.json()['event']

        # Statistics
        stats_resp = session.get(f'{base}/event/{match_id}/statistics', timeout=15)
        stats_data = stats_resp.json() if stats_resp.status_code == 200 else {}

        # Momentum graph
        graph_resp = session.get(f'{base}/event/{match_id}/graph', timeout=15)
        graph_data = graph_resp.json() if graph_resp.status_code == 200 else {}

        # Incidents (goals, cards, subs)
        incidents_resp = session.get(f'{base}/event/{match_id}/incidents', timeout=15)
        incidents_data = incidents_resp.json() if incidents_resp.status_code == 200 else {}

        return {
            'event': event_data,
            'statistics': stats_data,
            'graph': graph_data,
            'incidents': incidents_data
        }

    except Exception as e:
        return {'error': str(e)}


def parse_key_metrics(data):
    """Extract key metrics for betting analysis."""
    event = data.get('event', {})
    stats = data.get('statistics', {})
    graph = data.get('graph', {})
    incidents = data.get('incidents', {})

    home_team = event.get('homeTeam', {}).get('name', 'Home')
    away_team = event.get('awayTeam', {}).get('name', 'Away')
    status = event.get('status', {}).get('description', '')

    # Current score
    home_score = event.get('homeScore', {}).get('current', 0)
    away_score = event.get('awayScore', {}).get('current', 0)

    # Get all statistics periods (each period has groups)
    all_periods = stats.get('statistics', [])

    # ---- Core metrics ----
    xg_h, xg_a = find_stat(all_periods, 'expected goals')
    if xg_h == 0 and xg_a == 0:
        xg_h, xg_a = find_stat(all_periods, 'xg')

    shots_h, shots_a = find_stat(all_periods, 'total shots')
    sot_h, sot_a = find_stat(all_periods, 'shots on target')
    shots_off_h, shots_off_a = find_stat(all_periods, 'shots off target')
    blocked_h, blocked_a = find_stat(all_periods, 'blocked shots')
    shots_inside_h, shots_inside_a = find_stat(all_periods, 'shots inside box')
    shots_outside_h, shots_outside_a = find_stat(all_periods, 'shots outside box')
    hit_woodwork_h, hit_woodwork_a = find_stat(all_periods, 'hit woodwork')

    bc_h, bc_a = find_stat(all_periods, 'big chances')
    if bc_h == 0 and bc_a == 0:
        bc_h, bc_a = find_stat(all_periods, 'big chance')
    bc_missed_h, bc_missed_a = find_stat(all_periods, 'big chances missed')

    corners_h, corners_a = find_stat(all_periods, 'corner')

    poss_h, poss_a = find_stat(all_periods, 'ball possession')

    # ---- Passing metrics ----
    accurate_passes_h, accurate_passes_a = find_stat(all_periods, 'accurate passes')
    final_third_h, final_third_a = find_stat(all_periods, 'final third entries')
    crosses_h, crosses_a = find_stat(all_periods, 'crosses')
    long_balls_h, long_balls_a = find_stat(all_periods, 'long balls')

    # ---- Duel metrics ----
    tackles_won_pct_h, tackles_won_pct_a = find_stat(all_periods, 'tackles won')
    total_tackles_h, total_tackles_a = find_stat(all_periods, 'total tackles')
    aerial_h, aerial_a = find_stat(all_periods, 'aerial duels')
    ground_duels_h, ground_duels_a = find_stat(all_periods, 'ground duels')
    dribbles_h, dribbles_a = find_stat(all_periods, 'dribbles')
    dispossessed_h, dispossessed_a = find_stat(all_periods, 'dispossessed')

    # ---- Defensive metrics ----
    interceptions_h, interceptions_a = find_stat(all_periods, 'interceptions')
    recoveries_h, recoveries_a = find_stat(all_periods, 'recoveries')
    clearances_h, clearances_a = find_stat(all_periods, 'clearances')

    # ---- Discipline ----
    fouls_h, fouls_a = find_stat(all_periods, 'fouls')
    yellow_h, yellow_a = find_stat(all_periods, 'yellow cards')
    red_h, red_a = find_stat(all_periods, 'red cards')
    offsides_h, offsides_a = find_stat(all_periods, 'offsides')

    # ---- GK metrics ----
    saves_h, saves_a = find_stat(all_periods, 'total saves')

    # ---- Attack metrics ----
    touches_box_h, touches_box_a = find_stat(all_periods, 'touches in penalty area')

    # ---- Momentum analysis (last 10 data points) ----
    momentum_points = graph.get('graphPoints', [])
    if not momentum_points:
        momentum_points = graph.get('momentum', [])
    recent_momentum = momentum_points[-10:] if len(momentum_points) >= 10 else momentum_points
    momentum_sum = sum(p.get('value', 0) for p in recent_momentum) if recent_momentum else 0

    # ---- Incidents (proper field names) ----
    all_incidents_list = incidents.get('incidents', [])
    recent_events = []
    for inc in all_incidents_list[-8:]:
        inc_type = inc.get('incidentType', inc.get('type', ''))
        is_home = inc.get('isHome', None)
        time_min = inc.get('time', 0)
        player_obj = inc.get('player')
        player_name = player_obj.get('name', '') if isinstance(player_obj, dict) else ''
        assist_obj = inc.get('assist1')
        assist_name = assist_obj.get('name', '') if isinstance(assist_obj, dict) else ''

        team_label = ''
        if is_home is True:
            team_label = home_team
        elif is_home is False:
            team_label = away_team

        desc = f"{team_label} {inc_type}"
        if player_name:
            desc += f" - {player_name}"
        if assist_name:
            desc += f" (for {assist_name})"

        recent_events.append({
            'time': time_min,
            'type': inc_type,
            'team': team_label,
            'player': player_name,
            'description': desc
        })

    # ---- Build result ----
    result = {
        'home_team': home_team,
        'away_team': away_team,
        'status': status,
        'score': f"{home_score}-{away_score}",
        # xG
        'xg_home': xg_h,
        'xg_away': xg_a,
        # Shots
        'shots_home': int(shots_h),
        'shots_away': int(shots_a),
        'shots_on_target_home': int(sot_h),
        'shots_on_target_away': int(sot_a),
        'shots_off_target_home': int(shots_off_h),
        'shots_off_target_away': int(shots_off_a),
        'blocked_shots_home': int(blocked_h),
        'blocked_shots_away': int(blocked_a),
        'shots_inside_box_home': int(shots_inside_h),
        'shots_inside_box_away': int(shots_inside_a),
        'shots_outside_box_home': int(shots_outside_h),
        'shots_outside_box_away': int(shots_outside_a),
        'hit_woodwork_home': int(hit_woodwork_h),
        'hit_woodwork_away': int(hit_woodwork_a),
        # Chances
        'big_chances_home': int(bc_h),
        'big_chances_away': int(bc_a),
        'big_chances_missed_home': int(bc_missed_h),
        'big_chances_missed_away': int(bc_missed_a),
        # Set pieces
        'corners_home': int(corners_h),
        'corners_away': int(corners_a),
        # Possession
        'possession_home': int(poss_h),
        'possession_away': int(poss_a),
        # Passing
        'accurate_passes_home': int(accurate_passes_h),
        'accurate_passes_away': int(accurate_passes_a),
        'final_third_entries_home': int(final_third_h),
        'final_third_entries_away': int(final_third_a),
        'crosses_home': int(crosses_h),
        'crosses_away': int(crosses_a),
        # Duels
        'tackles_won_pct_home': int(tackles_won_pct_h),
        'tackles_won_pct_away': int(tackles_won_pct_a),
        'total_tackles_home': int(total_tackles_h),
        'total_tackles_away': int(total_tackles_a),
        'dribbles_home': int(dribbles_h),
        'dribbles_away': int(dribbles_a),
        'dispossessed_home': int(dispossessed_h),
        'dispossessed_away': int(dispossessed_a),
        # Defense
        'interceptions_home': int(interceptions_h),
        'interceptions_away': int(interceptions_a),
        'recoveries_home': int(recoveries_h),
        'recoveries_away': int(recoveries_a),
        'clearances_home': int(clearances_h),
        'clearances_away': int(clearances_a),
        # Discipline
        'fouls_home': int(fouls_h),
        'fouls_away': int(fouls_a),
        'yellow_cards_home': int(yellow_h),
        'yellow_cards_away': int(yellow_a),
        'red_cards_home': int(red_h),
        'red_cards_away': int(red_a),
        'offsides_home': int(offsides_h),
        'offsides_away': int(offsides_a),
        # GK
        'saves_home': int(saves_h),
        'saves_away': int(saves_a),
        # Attack
        'touches_in_box_home': int(touches_box_h),
        'touches_in_box_away': int(touches_box_a),
        # Momentum
        'momentum_10min': momentum_sum,
        # Events
        'recent_events': recent_events,
        'total_incidents': len(all_incidents_list)
    }

    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: fetch_sofascore.py <match_id>", file=sys.stderr)
        sys.exit(1)

    match_id = sys.argv[1]
    raw_data = fetch_match_data(match_id)

    if 'error' in raw_data:
        print(json.dumps({'error': raw_data['error']}))
        sys.exit(1)

    parsed = parse_key_metrics(raw_data)
    print(json.dumps(parsed, indent=2, ensure_ascii=False))
