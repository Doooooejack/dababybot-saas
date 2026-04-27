# MT5 Symbol Info Tick Failures - Diagnosis & Fix

## Problem
You're seeing errors like:
```
WARNING:mt5_wrapper:MT5 symbol_info_tick(GBPUSD) returned None (attempt 1/3)
WARNING:mt5_wrapper:MT5 symbol_info_tick(GBPUSD) returned None (attempt 2/3)
WARNING:mt5_wrapper:MT5 symbol_info_tick(GBPUSD) returned None (attempt 3/3)
ERROR:mt5_wrapper:Failed to get tick for GBPUSD after 3 attempts
```

This means MT5 is unable to retrieve pricing data for the GBPUSD symbol after 3 retry attempts.

## Root Causes

### 1. **MT5 Terminal Not Running or Disconnected**
- The MT5 terminal crashed or lost connection
- **Fix**: Restart your MetaTrader 5 terminal and ensure it connects to your broker

### 2. **Symbol Not in Market Watch**
- GBPUSD exists but hasn't been added to your MT5 "Market Watch" list
- MT5 won't provide tick data for symbols not in market watch
- **Fix**: The updated `mt5_wrapper.py` now automatically tries to select symbols (see improvements below)

### 3. **Symbol Not Available on Your Broker**
- Your broker's account doesn't include GBPUSD trading
- **Fix**: Check available symbols and use alternatives (see diagnostic tool)

### 4. **Data Feed Not Active**
- MT5 is running but the data feed for that symbol isn't loading
- **Fix**: Check MT5's "Market Watch" window - do you see the bid/ask prices updating?

### 5. **Network Connectivity Issue**
- Temporary network glitch preventing data retrieval
- **Fix**: Usually resolves on next retry, but check your internet connection

## Improvements Made to `mt5_wrapper.py`

### 1. **Automatic Symbol Selection**
The `safe_symbol_info_tick()` function now automatically tries to add the symbol to market watch before fetching ticks:
```python
# First, ensure the symbol is selected in MT5 market watch
if not safe_symbol_select(symbol, enable=True, retries=1):
    logger.warning(f"Could not select symbol {symbol} in MT5 market watch")
```

### 2. **Better Diagnostic Logging**
Enhanced error messages now differentiate between:
- Symbol doesn't exist in MT5
- Symbol exists but data feed isn't loaded
```python
if symbol_info is None:
    logger.warning("symbol may not exist")
else:
    logger.warning("possible data feed issue")
```

### 3. **New Helper Functions**
- `get_available_symbols()` - List all symbols your broker offers
- `symbol_is_available(symbol)` - Check if a symbol exists
- `safe_symbol_select(symbol, enable)` - Add/remove symbols from market watch

## How to Use the Diagnostic Tool

Run the diagnostic script to identify the exact problem:

```bash
python diagnose_mt5.py
```

This will:
1. ✓ Check if MT5 initializes
2. ✓ Verify MT5 connection health
3. ✓ Display account information
4. ✓ Show open positions
5. ✓ Diagnose GBPUSD specifically
6. ✓ List available symbols
7. ✓ Test common trading pairs
8. ✓ Provide actionable recommendations

## Quick Fixes by Symptom

### "GBPUSD is not available"
1. Open MT5 terminal
2. Right-click in "Market Watch" window
3. Select "Symbols"
4. Search for and add "GBPUSD"
5. Click OK
6. Restart your bot

### "Still can't get ticks after selecting"
1. Check if GBPUSD has bid/ask prices in Market Watch
2. If prices aren't updating: your data feed is offline
3. Restart MT5 completely
4. Check your internet connection
5. Verify your broker account is active

### "GBPUSD doesn't exist in available symbols"
1. Check your broker (some don't offer certain pairs)
2. Use alternative symbols:
   - GBPJPY, GBPCHF, GBPCAD instead
   - Or use currency baskets through your broker

### Symbol appears in list but can't get tick
1. Verify MT5 terminal is actively trading (check if you can place manual orders)
2. Check System settings in MT5 terminal
3. Rebuild terminal cache: Tools → Options → Data folder → Rebuild data folder
4. Restart MT5

## Implementation Details

### Before (Original Code)
```python
def safe_symbol_info_tick(symbol: str, retries: int = RETRY_LIMIT):
    # Just retried the call, no setup
    for attempt in range(retries):
        tick = mt5.symbol_info_tick(symbol)
        if tick is not None:
            return tick
    logger.error(f"Failed to get tick for {symbol}")
```

### After (Improved)
```python
def safe_symbol_info_tick(symbol: str, retries: int = RETRY_LIMIT):
    # Ensure symbol is in market watch first
    safe_symbol_select(symbol, enable=True, retries=1)
    
    for attempt in range(retries):
        tick = mt5.symbol_info_tick(symbol)
        if tick is not None:
            return tick
        
        # Provide diagnostic info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.warning("symbol may not exist")
        else:
            logger.warning("possible data feed issue")
```

## Preventing Future Occurrences

1. **Pre-initialize symbols** at bot startup:
   ```python
   from mt5_wrapper import safe_symbol_select
   
   symbols_needed = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
   for sym in symbols_needed:
       safe_symbol_select(sym, enable=True)
   ```

2. **Run health checks** periodically:
   ```python
   from mt5_wrapper import mt5_health_check
   
   health = mt5_health_check()
   if not health['is_connected']:
       logger.error("MT5 disconnected!")
   ```

3. **Log data feed status** in error handling:
   ```python
   tick = safe_symbol_info_tick("GBPUSD")
   if tick is None:
       logger.error("Data feed may be offline")
       # Take corrective action
   ```

## Files Modified/Created

- **Modified**: `mt5_wrapper.py` - Enhanced with symbol selection and better diagnostics
- **Created**: `diagnose_mt5.py` - Comprehensive diagnostic tool

## Next Steps

1. Run `python diagnose_mt5.py` to identify the specific issue
2. Apply the fix based on the diagnostic results
3. Monitor logs for the pattern to prevent recurrence
4. Consider adding symbol pre-initialization to bot startup routine

## Support

If the diagnostic tool shows all systems operational but you still get failures:
- Check MT5 terminal logs (Tools → Journal)
- Verify broker data feed status
- Contact your broker's support
