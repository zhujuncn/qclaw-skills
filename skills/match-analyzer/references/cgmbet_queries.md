# CGMBet26 Query Patterns

## Database Location
```
C:\Users\zhuju\AppData\Roaming\CGMBetSystem\CGMBetStats_v3.db
```

## Common Query Patterns

### 1. Time-Based Goal Probability

Query historical goal probability for a specific match time and scoreline.

```sql
-- Probability of at least one more goal from minute X
SELECT 
    COUNT(*) as sample_size,
    ROUND(AVG(CASE WHEN home_goals + away_goals > current_total THEN 1 ELSE 0 END) * 100, 2) as goal_probability
FROM matches 
WHERE minute >= ? 
AND minute < ?
AND home_goals + away_goals = ?
AND status = 'J'  -- 'J' = Finished (not 'F')
```

### 2. Scoreline Patterns

```sql
-- Historical outcomes when score is X-Y at minute Z
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN final_home > final_away THEN 1 ELSE 0 END) as home_wins,
    SUM(CASE WHEN final_home = final_away THEN 1 ELSE 0 END) as draws,
    SUM(CASE WHEN final_home < final_away THEN 1 ELSE 0 END) as away_wins
FROM matches
WHERE minute = ?
AND home_goals = ?
AND away_goals = ?
```

### 3. League-Specific Analysis

```sql
-- Average goals in specific league
SELECT 
    AVG(home_goals + away_goals) as avg_goals,
    AVG(CASE WHEN home_goals > 0 AND away_goals > 0 THEN 1 ELSE 0 END) as btts_rate
FROM matches
WHERE league = ?
AND status = 'J'
```

### 4. Team Form

```sql
-- Recent form (last 5 matches)
SELECT 
    AVG(goals_for) as avg_goals_for,
    AVG(goals_against) as avg_goals_against,
    AVG(xg) as avg_xg
FROM (
    SELECT * FROM matches
    WHERE (home_team = ? OR away_team = ?)
    AND status = 'J'
    ORDER BY date DESC
    LIMIT 5
)
```

## Key Notes

- **Status Codes**: 'J' = Finished (has data), 'F' = Finished (no data)
- **Time Fields**: Match minute (0-90+, excluding ET)
- **xG Data**: Available in Advanced Poisson module tables

## Integration with Sofascore

Combine CGMBet26 historical patterns with Sofascore live data:

1. Get current match state from Sofascore (score, time, xG)
2. Query CGMBet26 for similar historical situations
3. Weight: 60% live data (Sofascore) + 40% historical (CGMBet26)
