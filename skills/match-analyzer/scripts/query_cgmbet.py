#!/usr/bin/env python3
"""
Query CGMBet26 database for statistical patterns.
"""

import sys
import sqlite3
import json

def query_time_based_goals(minute, score_diff=0):
    """Query goal probability based on match time and current score."""
    db_path = r'C:\Users\zhuju\AppData\Roaming\CGMBetSystem\CGMBetStats_v3.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query for similar time periods and scorelines
        # This is a simplified example - actual queries would be more complex
        query = """
        SELECT 
            COUNT(*) as total_matches,
            AVG(CASE WHEN total_goals > ? THEN 1 ELSE 0 END) as over_prob,
            AVG(CASE WHEN home_goals + away_goals = ? THEN 1 ELSE 0 END) as exact_prob
        FROM (
            SELECT 
                home_goals + away_goals as total_goals,
                home_goals,
                away_goals
            FROM matches 
            WHERE minute >= ? AND minute < ?
            AND ABS(home_goals - away_goals) = ?
            AND status = 'J'
        )
        """
        
        # Simplified parameters
        cursor.execute(query, (0, 0, minute, minute + 15, score_diff))
        result = cursor.fetchone()
        conn.close()
        
        return {
            'sample_size': result[0] if result else 0,
            'over_probability': round(result[1] * 100, 2) if result and result[1] else 0,
            'context': f"Historical data for minute {minute}, score diff {score_diff}"
        }
        
    except Exception as e:
        return {'error': str(e)}

def query_league_patterns(league_name, home_team, away_team):
    """Query league-specific patterns."""
    # Placeholder for league-specific analysis
    return {
        'league': league_name,
        'avg_goals': 2.8,
        'home_advantage': 0.15,
        'notes': 'League pattern analysis'
    }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: query_cgmbet.py <command> [args...]", file=sys.stderr)
        print("Commands: time_goals <minute> [score_diff]", file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'time_goals':
        minute = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        score_diff = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        result = query_time_based_goals(minute, score_diff)
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({'error': f'Unknown command: {command}'}), indent=2)
        sys.exit(1)
