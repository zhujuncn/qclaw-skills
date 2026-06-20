#!/usr/bin/env python3
"""
Form-ELO Divergence Detection System - Standalone Example
==========================================================

This script demonstrates the core divergence detection without
requiring the full Bet Angel X2 framework.

Usage:
    python example_standalone.py --date 2026-04-21
"""

import sys
import sqlite3
import json
from datetime import datetime, timedelta

# Path to CGMBet26 database
DB_PATH = r'C:\Users\%USERNAME%\AppData\Roaming\CGMBetSystem\CGMBetStats_v3.db'


def detect_divergence(target_date, days_ahead=1):
    """
    Simple divergence detection example.
    
    Returns list of matches where ELO and Form contradict.
    """
    conn = sqlite3.connect(DB_PATH.replace('%USERNAME%', 'zhuju'))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    end_date = (datetime.strptime(target_date, '%Y-%m-%d') + 
                timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    
    # Query matches with both ELO and Form data
    cur.execute("""
    SELECT
        m.MatchId, m.Date, m.Time,
        t1.Name as Home, t2.Name as Away,
        l.Name as League, l.Country,
        r.EloHome, r.EloAway,
        r.EloHome - r.EloAway as EloDiff,
        r.FormHome, r.FormAway,
        r.FormHome - r.FormAway as FormDiff
    FROM Matches m
    JOIN Teams t1 ON m.HomeTeamId = t1.Id
    JOIN Teams t2 ON m.AwayTeamId = t2.Id
    JOIN Leagues l ON substr(m.MatchId, 1, 4) = l.Id
    JOIN Ratings r ON m.MatchId = r.MatchId
    WHERE m.Date >= ? AND m.Date <= ?
      AND m.Status NOT IN ('J', 'C')
      AND r.FormHome IS NOT NULL
      AND (r.FormHome != 0 OR r.FormAway != 0)
      AND r.EloHome != 0
    ORDER BY m.Date, m.Time
    """, (target_date, end_date))
    
    matches = cur.fetchall()
    conn.close()
    
    divergences = []
    
    for m in matches:
        elo_diff = m['EloDiff'] or 0
        form_diff = m['FormDiff'] or 0
        
        # Divergence condition: ELO and Form point opposite directions
        is_diverge = (elo_diff > 50 and form_diff < -3) or (elo_diff < -50 and form_diff > 3)
        
        if is_diverge:
            # Classify severity
            if abs(elo_diff) > 100 and abs(form_diff) > 10:
                tier = 1  # Strong
            elif abs(elo_diff) > 50 and abs(form_diff) > 5:
                tier = 2  # Moderate
            else:
                tier = 3  # Weak
            
            divergences.append({
                'date': m['Date'],
                'time': f"{m['Time']:04d}",
                'match': f"{m['Home']} vs {m['Away']}",
                'league': m['League'],
                'elo_diff': elo_diff,
                'form_diff': form_diff,
                'tier': tier,
                'signal': 'ELO favorite overrated' if elo_diff > 0 else 'ELO underdog underrated'
            })
    
    return divergences


def print_report(divergences):
    """Print formatted divergence report."""
    print("=" * 70)
    print("FORM-ELO DIVERGENCE REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    if not divergences:
        print("\nNo divergences found for the specified period.")
        return
    
    tier_names = {1: '!!! STRONG', 2: '!! MODERATE', 3: '! WEAK'}
    
    for d in divergences:
        print(f"\n{tier_names[d['tier']]} | {d['date']} {d['time']}")
        print(f"  {d['match']}")
        print(f"  {d['league']}")
        print(f"  ELO diff: {d['elo_diff']:+d} | Form diff: {d['form_diff']:+d}")
        print(f"  Signal: {d['signal']}")
    
    print(f"\n{'='*70}")
    print(f"Total divergences: {len(divergences)}")
    print(f"  Tier 1 (Strong): {sum(1 for d in divergences if d['tier']==1)}")
    print(f"  Tier 2 (Moderate): {sum(1 for d in divergences if d['tier']==2)}")
    print(f"  Tier 3 (Weak): {sum(1 for d in divergences if d['tier']==3)}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple divergence detection')
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'),
                       help='Target date (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=1,
                       help='Days ahead to scan')
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')
    
    args = parser.parse_args()
    
    divergences = detect_divergence(args.date, args.days)
    
    if args.json:
        print(json.dumps(divergences, indent=2))
    else:
        print_report(divergences)
