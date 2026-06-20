# Bet Angel Guardian .baf File Format Reference

> Version: 6.0 | Based on reverse-engineered Signal Goals files

---

## Overview

`.baf` (Bet Angel File) is the proprietary format for Bet Angel Guardian automation rules. Files are plain text with LF or CRLF line endings.

## File Structure

```
Line 1:     Version number (e.g., "6.0")
Line 2:     Blank
Line 3:     Rule count (integer)
Line 4+:    Rules (concatenated)
```

## Rule Structure

Each rule consists of three sections: **Header**, **Action**, and **Conditions**.

### Header Section

```
{rule_id}              4-digit rule ID (0001, 0002, ...)
{rule_name}            Human-readable name
{rule_type}            Rule type: SIGNAL_ONLY, BACK, LAY, GREEN_UP, etc.
{param_1}              Usually "2"
{bool_1}               True/False
{bool_2}               True/False
{repeat_count}         Execution repeat count (usually "1")
{bool_3}               True/False
{bool_4}               True/False
{interval_ms}          Polling interval in milliseconds (usually "3000")
{time_period}          Time period in seconds (usually "90")
{param_2}              Usually "5"
{param_3}              Usually "2"
{market_category}      3 = Match Odds, 2 = Over/Under
                       Blank line
{selection_mode}       Selection targeting: CUSTOM_BELOW
{selection_val_1}      Selection parameter 1 (usually "10")
{selection_val_2}      Selection parameter 2 (usually "10")
{stake_mode}           Stake mode: FIXED
{bool_5}               True/False
{bool_6}               True/False
{bool_7}               True/False
{bool_8}               True/False
{bool_9}               True/False
                       Blank line
{bool_10}              True/False
                       Blank line
```

### Signal Action Section

```
{signal_action}        INCREMENT / DECREMENT
{signal_name}          Signal variable name (e.g., "goal")
{signal_value}         Value to add/subtract (usually "1")
{signal_reset}         Reset mode: NONE
                       Blank line
```

### Conditions Section

```
{condition_groups}     Number of condition groups (usually "1")
{group_logic}          True = AND, False = OR
{condition_count}      Number of conditions in group
```

#### Condition Type: TIME_UNSUSPENDED

```
TIME_UNSUSPENDED
{description}          "Time since unsuspended > X seconds"
{param}                "2"
{comparison}           GREATER / LESS
{value}                Seconds (e.g., "60")
```

#### Condition Type: HISTORIC_RELATIVE_ODDS

```
HISTORIC_RELATIVE_ODDS
{description}          "Last Traded price [<>] Last Traded price X seconds ago [+/-] Y ticks"
{cond_param_1}         "18"
{bool_1}               True
{cond_param_2}         "2"
{cond_param_3}         "1"
{odds_reference_1}     LTP (Last Traded Price)
{bool_2}               True
{cond_param_4}         "0"
{comparison}           GREATER / LESS
{bool_3}               True
{cond_param_5}         "2"
{cond_param_6}         "1"
{odds_reference_2}     LTP
{historic_flag}        False = current market LTP, True = historic
{historic_seconds}     Seconds to look back (e.g., "65")
{arithmetic_op}        PLUS / MINUS
{arithmetic_value}     Tick offset (e.g., "10" or "15")
{arithmetic_unit}      TICKS
```

---

## Rule Types

| Type | Description | Signal/Action |
|------|-------------|---------------|
| `SIGNAL_ONLY` | Only sets signal, no bet placement | INCREMENT/DECREMENT |
| `BACK` | Places a BACK bet when conditions met | Bet parameters |
| `LAY` | Places a LAY bet when conditions met | Bet parameters |
| `GREEN_UP` | Greens up position when conditions met | Market calculation |

## Signal Actions

| Action | Effect | Use Case |
|--------|--------|----------|
| `INCREMENT` | signal += value | Goal detected |
| `DECREMENT` | signal -= value | Distinguish which team scored |
| `SET` | signal = value | Reset to specific value |

## Known Limitations

1. **API inaccessible**: No API endpoints for reading/writing signals or automation rules
2. **GUI import only**: Must use Bet Angel Guardian → Import a Rules File
3. **Version 6.0**: Current format version, older versions may differ
4. **Proprietary**: Format is not officially documented
