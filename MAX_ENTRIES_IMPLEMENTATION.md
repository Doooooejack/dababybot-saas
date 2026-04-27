# Max 2 Entries Per Symbol - Implementation Summary

## Overview
Implemented a maximum of **2 concurrent entries per symbol** feature in the trading bot. This prevents over-concentration of capital in a single symbol and helps with risk management.

## Changes Made

### 1. New Helper Functions (Line 16345-16373)

#### `count_open_positions_for_symbol(symbol)`
- Counts the number of currently open positions for a given symbol
- Safely retrieves positions from MT5 using the safe wrapper if available
- Returns 0 if no positions exist or on error
- **Location**: Lines 16345-16353

#### `can_enter_symbol(symbol, max_entries_per_symbol=2)`
- Validates whether a new position can be opened for a symbol
- Checks if current open positions are below the max allowed (default: 2)
- Returns tuple: `(can_enter: bool, reason: str)`
- Provides clear feedback on entry permission and current position count
- **Location**: Lines 16355-16372

### 2. Integration into Entry Decision Logic (Line 16400-16404)

Modified `should_trade_advanced()` function to include the max entries per symbol check:
- Added at the beginning of validation checks (after FVG validation)
- Only executes the check if a symbol is provided
- Prevents entry if max entries are already open for the symbol
- Logs entry check status for debugging
- Returns rejection reason if max entries reached

**Implementation**:
```python
# --- Check max entries per symbol (max 2 concurrent entries) ---
if symbol:
    can_enter, entry_check_reason = can_enter_symbol(symbol, max_entries_per_symbol=2)
    if not can_enter:
        return False, entry_check_reason
    print(f"[ENTRY CHECK] {symbol}: {entry_check_reason}")
```

## How It Works

1. **Entry Attempt**: When a trade signal is generated for a symbol
2. **Position Count**: The bot counts all open positions matching that symbol
3. **Validation**: If count >= 2, the entry is rejected with a clear reason
4. **Logging**: Entry check status is logged for monitoring and debugging

## Example Scenarios

| Symbol | Open Positions | Can Enter? | Action |
|--------|-----------------|-----------|---------|
| EURUSD | 0 | ✓ Yes | Execute trade |
| EURUSD | 1 | ✓ Yes | Execute trade |
| EURUSD | 2 | ✗ No | Reject with reason |
| GBPUSD | 1 | ✓ Yes | Execute trade |
| XAUUSD | 0 | ✓ Yes | Execute trade |

## Log Output Examples

**When entry is allowed**:
```
[ENTRY CHECK] EURUSD: Can enter (1/2 entries used)
```

**When entry is rejected**:
```
[ENTRY CHECK] EURUSD: Max 2 entries per symbol reached. Currently have 2 open position(s) for EURUSD
[ENTRY DEBUG] EURUSD | ... | Max 2 entries per symbol reached. Currently have 2 open position(s) for EURUSD
```

## Testing

A test script (`test_max_entries.py`) was created and verified:
- ✓ Correctly counts positions per symbol
- ✓ Allows entry when below max (0-1 positions)
- ✓ Rejects entry when at max (2 positions)

## Benefits

1. **Risk Management**: Prevents over-concentration in a single symbol
2. **Capital Efficiency**: Allows diversification across multiple symbols
3. **Recovery Flexibility**: Enables both recovery and new entry strategies
4. **Clear Logging**: Easy to monitor and debug entry decisions

## Configuration

The maximum entries per symbol is hardcoded to **2** in the `can_enter_symbol()` call:
```python
can_enter, entry_check_reason = can_enter_symbol(symbol, max_entries_per_symbol=2)
```

To change this limit in the future, modify the `max_entries_per_symbol` parameter value.

## Integration Points

The check is integrated into the main entry validation at the earliest stage:
- **File**: `botfriday6000th.py`
- **Function**: `should_trade_advanced()`
- **Order**: After FVG checks, before confidence validation
- **Impact**: Affects all entry models that use `should_trade_advanced()`
