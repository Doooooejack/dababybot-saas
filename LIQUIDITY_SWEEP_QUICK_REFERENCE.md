"""
LIQUIDITY SWEEP ENGINE - QUICK REFERENCE CARD
==============================================

Keep this handy for fast function lookup and common patterns.


🔍 FUNCTION QUICK REFERENCE
===========================

LIQUIDITY SWEEP
───────────────
liquidity_sweep_high(prev_high, candle)
  → Returns: bool
  → True if price >high then <close in same candle

liquidity_sweep_low(prev_low, candle)
  → Returns: bool
  → True if price <low then >close in same candle

sweep_reentry_confirmed(sweep_level, candles, sweep_type, lookback=5)
  → Returns: bool
  → True if re-entry detected within lookback


SWING POINTS
────────────
swing_high(candles, i)
  → Returns: bool
  → True if candles[i].high > [i-1].high AND > [i+1].high

swing_low(candles, i)
  → Returns: bool
  → True if candles[i].low < [i-1].low AND < [i+1].low

find_last_swing_high(candles, lookback=20)
  → Returns: {'index': int, 'price': float} or None

find_last_swing_low(candles, lookback=20)
  → Returns: {'index': int, 'price': float} or None


BOS DETECTION
─────────────
detect_bullish_bos(current_close, last_swing_high)
  → Returns: bool
  → True if close > last_swing_high

detect_bearish_bos(current_close, last_swing_low)
  → Returns: bool
  → True if close < last_swing_low


CHOCH DETECTION
───────────────
detect_bullish_choch(current_close, candles, lookback=30)
  → Returns: {'signal': bool, 'trigger_level': float, ...} or None
  → Looks for lower high break (reversal signal)

detect_bearish_choch(current_close, candles, lookback=30)
  → Returns: {'signal': bool, 'trigger_level': float, ...} or None
  → Looks for higher low break (reversal signal)


FVG DETECTION
─────────────
bullish_fvg(c1, c2, c3)
  → Returns: bool
  → True if c1.high < c3.low (gap exists)

bearish_fvg(c1, c2, c3)
  → Returns: bool
  → True if c1.low > c3.high (gap exists)

get_fvg_bounds(c1, c2, c3, fvg_type='bullish')
  → Returns: (low, high) or None

detect_fvg_after_structure(candles, structure_index, fvg_type='bullish', lookback=5)
  → Returns: {'exists': bool, 'low': float, 'high': float, ...} or None


ENTRY ZONE
──────────
calculate_entry_zone(fvg_low, fvg_high, fvg_type='bullish')
  → Returns: {
      'entry_zone_low': float,
      'entry_zone_high': float,
      'zone_size': float,
      'mid_point': float
    }
  → Bullish: 50%-75% from bottom
  → Bearish: 25%-50% from top

price_in_entry_zone(price, entry_zone_low, entry_zone_high, fvg_type='bullish')
  → Returns: bool
  → True if price is within optimal entry zone


ENTRY CONFIRMATION
───────────────────
bullish_engulfing(prev_candle, curr_candle)
  → Returns: bool
  → True if open < prev.close AND close > prev.open

bearish_engulfing(prev_candle, curr_candle)
  → Returns: bool
  → True if open > prev.close AND close < prev.open

is_displacement_candle(candle, prev_candle=None, body_ratio_threshold=0.7)
  → Returns: bool
  → True if body > 70% of total range

has_volume_expansion(curr_candle, prev_candle, volume_ratio_threshold=1.5)
  → Returns: bool
  → True if current volume > 1.5x previous

validate_entry_confirmation(prev_candle, curr_candle, entry_type='bullish',
                           check_displacement=True, check_volume=False)
  → Returns: {
      'entry_confirmed': bool,
      'engulfing': bool,
      'displacement': bool or None,
      'volume_expansion': bool or None
    }


COMPLETE WORKFLOW
──────────────────
execute_sweep_to_entry_workflow(candles, lookback=30, entry_type='bullish',
                                require_displacement=False)
  → Returns: {
      'sweep_detected': bool,
      'sweep_confirmed': bool,
      'structure_detected': 'BOS' | 'CHoCH' | None,
      'fvg_detected': bool,
      'entry_zone': dict or None,
      'entry_ready': bool,
      'details': dict
    }


⚡ COMMON PATTERNS
==================

PATTERN 1: Check for any liquidity sweep
──────────────────────────────────────────
if liquidity_sweep_high(1.2000, candles[-1]):
    if sweep_reentry_confirmed(1.2000, candles[-5:], 'high'):
        print("Sweep confirmed!")


PATTERN 2: Find trend direction
────────────────────────────────
swing_h = find_last_swing_high(candles, lookback=20)
swing_l = find_last_swing_low(candles, lookback=20)

if swing_h and swing_l:
    if swing_h['index'] > swing_l['index']:
        print("Bullish bias - higher high is more recent")
    else:
        print("Bearish bias - lower low is more recent")


PATTERN 3: Detect structure break
──────────────────────────────────
close = candles[-1].close

if detect_bullish_bos(close, swing_h['price']):
    print("BOS: Bullish continuation")

choch = detect_bullish_choch(close, candles)
if choch and choch['signal']:
    print(f"CHoCH: Bullish reversal at {choch['trigger_level']}")


PATTERN 4: Find and analyze FVG
────────────────────────────────
fvg = detect_fvg_after_structure(candles, swing_h['index'], fvg_type='bullish')

if fvg and fvg['exists']:
    zone = calculate_entry_zone(fvg['low'], fvg['high'], 'bullish')
    
    curr_price = candles[-1].close
    if price_in_entry_zone(curr_price, zone['entry_zone_low'], 
                          zone['entry_zone_high'], 'bullish'):
        print(f"Price in entry zone! Mid-point: {zone['mid_point']}")


PATTERN 5: Complete signal validation
──────────────────────────────────────
# One-liner check
result = execute_sweep_to_entry_workflow(candles, lookback=30, 
                                        entry_type='bullish',
                                        require_displacement=True)

if result['entry_ready']:
    print("✅ GO LONG!")
    entry_price = result['entry_zone']['mid_point']
    print(f"Enter at: {entry_price}")


📊 DATA FORMAT EXAMPLES
=======================

PANDAS DATAFRAME
────────────────
import pandas as pd

df = pd.DataFrame({
    'time': [...],
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})

# Use directly
result = execute_sweep_to_entry_workflow(df)


DICTIONARY LIST
────────────────
candles = [
    {
        'time': '2025-01-01 10:00',
        'open': 1.2000,
        'high': 1.2010,
        'low': 1.1990,
        'close': 1.2005,
        'volume': 1500
    },
    ...
]

# Use directly
result = execute_sweep_to_entry_workflow(candles)


NAMEDTUPLE/OBJECT
──────────────────
from collections import namedtuple

Candle = namedtuple('Candle', ['open', 'high', 'low', 'close', 'volume'])

candles = [
    Candle(1.2000, 1.2010, 1.1990, 1.2005, 1500),
    ...
]

# Use directly
result = execute_sweep_to_entry_workflow(candles)


🎯 TRADING LOGIC TEMPLATE
=========================

def execute_trade(symbol, timeframe='M5'):
    # 1. Get candles
    candles = get_price_data(symbol, timeframe=timeframe, bars=100)
    
    if len(candles) < 10:
        return None
    
    # 2. Run complete analysis
    result = execute_sweep_to_entry_workflow(
        candles,
        lookback=30,
        entry_type='bullish',
        require_displacement=True
    )
    
    # 3. Check if trade is ready
    if not result['entry_ready']:
        return None
    
    # 4. Extract trade parameters
    entry_price = result['entry_zone']['mid_point']
    
    # 5. Calculate SL/TP
    swing_low = find_last_swing_low(candles, lookback=50)
    stop_loss = swing_low['price'] - 0.0005  # Small buffer
    
    fvg = result['details'].get('fvg_bounds')
    take_profit = fvg['high'] + 0.001  # Target above FVG
    
    # 6. Place trade
    trade = {
        'symbol': symbol,
        'direction': result['structure_detected'],
        'entry': entry_price,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'risk_reward': (take_profit - entry_price) / (entry_price - stop_loss),
        'setup_quality': 'CHoCH' if result['structure_detected'] == 'CHoCH' else 'BOS'
    }
    
    return trade


✓ ERROR HANDLING
================

All functions are safe:
- Check for None returns before using results
- DataFrame/dict handling is automatic
- Import failures don't crash bot (fallback functions)
- No divisions by zero
- All edge cases handled


VALIDATION CHECKLIST
====================

Before placing a trade:
☐ swing_ref is not None
☐ structure_detected is 'CHoCH' (preferred) or 'BOS'
☐ fvg_detected is True
☐ entry_ready is True
☐ entry_zone exists and has bounds
☐ current_price is within entry_zone
☐ engulfing pattern confirmed
☐ displacement candle present (if required)
☐ risk/reward ratio > 1.5:1


COMMON DEBUGGING
================

Issue: Functions return None/False
Fix: Check candle data has required OHLC columns

Issue: swing_ref is always None
Fix: Increase lookback period or check data quality

Issue: No FVG detected
Fix: Check structure was actually detected first
     (FVG only detected AFTER BOS/CHoCH)

Issue: entry_ready is always False
Fix: Check engulfing pattern exists
     Check if displacement is required

Issue: Import fails silently
Fix: Verify liquidity_sweep_engine.py exists
     Use test script to validate: python test_liquidity_sweep_engine.py


═══════════════════════════════════════════════════════════

This is your complete reference guide.
Bookmark it for quick function lookup during development.

═══════════════════════════════════════════════════════════
"""
