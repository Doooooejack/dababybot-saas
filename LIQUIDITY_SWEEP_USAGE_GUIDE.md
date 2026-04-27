"""
LIQUIDITY SWEEP ENGINE - USAGE GUIDE
======================================

Now integrated into botfriday6000th.py - all functions are available for use.

QUICK START EXAMPLES
====================

1️⃣ DETECT LIQUIDITY SWEEP & CONFIRM RE-ENTRY
----------------------------------------------

from liquidity_sweep_engine import liquidity_sweep_high, sweep_reentry_confirmed

# Candles: list or pandas DataFrame with 'high', 'low', 'close'
prev_high = 1.2000
current_candle = candles[-1]  # Last candle

# Check if sweep occurred
if liquidity_sweep_high(prev_high, current_candle):
    print("Sweep detected! Checking for re-entry...")
    
    # Confirm re-entry within next 5 candles
    if sweep_reentry_confirmed(prev_high, candles[-5:], sweep_type='high', lookback=5):
        print("✅ Sweep CONFIRMED - re-entry detected")
    else:
        print("❌ No re-entry yet - wait or reject")


2️⃣ IDENTIFY SWING POINTS FOR MARKET BIAS
-------------------------------------------

from liquidity_sweep_engine import find_last_swing_high, find_last_swing_low

# Find last swing high (lookback 20 candles)
last_swing_high = find_last_swing_high(candles, lookback=20)
if last_swing_high:
    print(f"Last Swing High: {last_swing_high['price']} at index {last_swing_high['index']}")

# Find last swing low
last_swing_low = find_last_swing_low(candles, lookback=20)
if last_swing_low:
    print(f"Last Swing Low: {last_swing_low['price']} at index {last_swing_low['index']}")


3️⃣ DETECT BOS vs CHoCH
-----------------------

from liquidity_sweep_engine import (
    detect_bullish_bos, detect_bullish_choch,
    detect_bearish_bos, detect_bearish_choch
)

current_close = candles[-1].close

# BULLISH signals
if detect_bullish_bos(current_close, last_swing_high['price']):
    print("📈 Bullish BOS detected - trend continuation")

choch = detect_bullish_choch(current_close, candles, lookback=30)
if choch and choch['signal']:
    print(f"🔄 Bullish CHoCH detected at level {choch['trigger_level']}")

# BEARISH signals
if detect_bearish_bos(current_close, last_swing_low['price']):
    print("📉 Bearish BOS detected - trend continuation")

choch = detect_bearish_choch(current_close, candles, lookback=30)
if choch and choch['signal']:
    print(f"🔄 Bearish CHoCH detected at level {choch['trigger_level']}")


4️⃣ DETECT FVG ONLY AFTER STRUCTURE BREAK
------------------------------------------

from liquidity_sweep_engine import (
    detect_fvg_after_structure, calculate_entry_zone
)

# Assume structure_index is where BOS/CHoCH occurred
structure_index = last_swing_high['index']

# Get FVG created AFTER the structure break
fvg_result = detect_fvg_after_structure(
    candles,
    structure_index,
    fvg_type='bullish',  # 'bullish' or 'bearish'
    lookback=5
)

if fvg_result and fvg_result['exists']:
    fvg_low = fvg_result['low']
    fvg_high = fvg_result['high']
    print(f"✅ FVG found: [{fvg_low}, {fvg_high}]")


5️⃣ CALCULATE HIGH-PROBABILITY ENTRY ZONE (50%-75% of FVG)
----------------------------------------------------------

from liquidity_sweep_engine import calculate_entry_zone, price_in_entry_zone

# Calculate the entry zone (NOT the whole FVG)
entry_zone = calculate_entry_zone(
    fvg_low=1.1950,
    fvg_high=1.2000,
    fvg_type='bullish'
)

print(f"Entry Zone: {entry_zone['entry_zone_low']} - {entry_zone['entry_zone_high']}")
print(f"Mid-point: {entry_zone['mid_point']}")

# Check if current price is in entry zone
current_price = candles[-1].close
if price_in_entry_zone(current_price, 
                       entry_zone['entry_zone_low'], 
                       entry_zone['entry_zone_high'], 
                       fvg_type='bullish'):
    print("✅ Price in entry zone!")


6️⃣ CONFIRM ENTRY (ENGULFING + OPTIONAL FILTERS)
-------------------------------------------------

from liquidity_sweep_engine import (
    bullish_engulfing, validate_entry_confirmation
)

prev_candle = candles[-2]
curr_candle = candles[-1]

# Simple engulfing check
if bullish_engulfing(prev_candle, curr_candle):
    print("✅ Bullish engulfing detected")

# Complete validation (engulfing + displacement + volume)
confirmation = validate_entry_confirmation(
    prev_candle,
    curr_candle,
    entry_type='bullish',
    check_displacement=True,  # Optional: large body
    check_volume=False         # Optional: volume expansion
)

if confirmation['entry_confirmed']:
    print("✅✅ ENTRY CONFIRMED - All filters passed!")
    print(f"  - Engulfing: {confirmation['engulfing']}")
    print(f"  - Displacement: {confirmation['displacement']}")
    print(f"  - Volume: {confirmation['volume_expansion']}")
else:
    print("❌ Entry not confirmed - waiting for setup")


7️⃣ COMPLETE WORKFLOW (ALL-IN-ONE)
-----------------------------------

from liquidity_sweep_engine import execute_sweep_to_entry_workflow

# Execute the complete pipeline in one call
result = execute_sweep_to_entry_workflow(
    candles,
    lookback=30,
    entry_type='bullish',  # 'bullish' or 'bearish'
    require_displacement=True
)

print(f"Sweep detected: {result['sweep_detected']}")
print(f"Sweep confirmed: {result['sweep_confirmed']}")
print(f"Structure: {result['structure_detected']}")  # 'BOS', 'CHoCH', None
print(f"FVG detected: {result['fvg_detected']}")
print(f"Entry zone: {result['entry_zone']}")
print(f"ENTRY READY: {result['entry_ready']}")  # ✅ Go signal

if result['entry_ready']:
    print("🚀 READY TO TRADE - Execute entry!")
    print(f"Details: {result['details']}")


KEY RULES TO REMEMBER
=====================

✅ Liquidity Sweep Rule:
   "A sweep is NOT confirmed until price re-enters the range."
   No re-entry → no sweep → no trade.

✅ BOS vs CHoCH:
   BOS = Continuation in same direction
   CHoCH = Reversal (what you want after a sweep)
   After a sweep, prefer CHoCH over BOS

✅ FVG Rule:
   "Only accept FVGs created AFTER BOS/CHoCH"
   Old FVGs = ignore
   Random gaps = ignore
   FVGs before structure = ignore

✅ Entry Zone Rule:
   "Do not enter at the whole FVG"
   Bullish: 50%-75% from bottom (mid to top)
   Bearish: 25%-50% from top (mid to bottom)

✅ Entry Confirmation:
   Must have bullish/bearish engulfing pattern
   + Optional displacement candle (large body)
   + Optional volume expansion

DATA STRUCTURE COMPATIBILITY
=============================

All functions accept either:
- pandas DataFrame rows (df.iloc[i] or df.loc[idx])
- Dictionaries with OHLC keys: {'open': x, 'high': y, 'low': z, 'close': w, ...}

Required columns/keys:
  - 'open'
  - 'high'
  - 'low'
  - 'close'

Optional columns/keys:
  - 'volume' (for volume expansion checks)

Example with pandas:
  candles = pd.read_csv('data.csv')
  result = execute_sweep_to_entry_workflow(candles)

Example with dict list:
  candles = [
      {'open': 1.2000, 'high': 1.2010, 'low': 1.1990, 'close': 1.2005},
      {'open': 1.2005, 'high': 1.2015, 'low': 1.2000, 'close': 1.2008},
      ...
  ]
  result = execute_sweep_to_entry_workflow(candles)


TESTING & DEBUGGING
===================

Test your logic step-by-step:

# Step 1: Load candles
candles = get_price_data('EURUSD', timeframe='M5', bars=100)

# Step 2: Check swing points
swing = find_last_swing_high(candles)
print(f"Swing High: {swing}")

# Step 3: Check structure break
is_bos = detect_bullish_bos(candles[-1].close, swing['price'])
print(f"BOS detected: {is_bos}")

# Step 4: Check FVG
fvg = detect_fvg_after_structure(candles, swing['index'])
print(f"FVG: {fvg}")

# Step 5: Check entry zone
if fvg:
    zone = calculate_entry_zone(fvg['low'], fvg['high'])
    print(f"Entry zone: {zone}")

# Step 6: Check confirmation
confirmation = validate_entry_confirmation(candles[-2], candles[-1])
print(f"Entry ready: {confirmation['entry_confirmed']}")


For questions or issues, refer to liquidity_sweep_engine.py for full documentation.
"""
