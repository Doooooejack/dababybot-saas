# CONFIRMATION EXAMPLES
## Real-World Scenarios for One-Time Confirmation Framework

---

## Example 1: Bullish Engulfing Confirmation

### Scenario
Trading EURUSD.m after a liquidity sweep at the swing low.

```
Candle N-1 (Previous):
  Open:  1.0840
  Close: 1.0845
  High:  1.0850
  Low:   1.0835

Candle N (Current):
  Open:  1.0839    ← Opens BELOW previous open
  Close: 1.0855    ← Closes ABOVE previous high ✓
  High:  1.0860
  Low:   1.0835    ← Extends below previous low
```

### Detection
```python
# Setup is active, waiting for confirmation
state['setup_active'] = True
state['setup_direction'] = "long"
state['setup_price'] = 1.0835

# Candle N arrives - check confirmation
prev_candle = df.iloc[-2]  # Candle N-1: open=1.0840, high=1.0850, low=1.0835
curr_candle = df.iloc[-1]  # Candle N: open=1.0839, close=1.0855, low=1.0835

# Bullish engulfing check:
is_bullish_engulfing = (
    curr_candle['close'] > prev_candle['high'] and     # 1.0855 > 1.0850 ✓
    curr_candle['open'] < prev_candle['open'] and      # 1.0839 < 1.0840 ✓
    curr_candle['low'] < prev_candle['low']            # 1.0835 < 1.0835 ✓ (equal is ok)
)
# Result: TRUE - Confirmation locked!
```

### Action
```
[SETUP ACTIVE] EURUSD.m | Direction: LONG | Price: 1.0835 | Reason: Liquidity sweep at swing low

[Candle N closes]

[CONFIRMATION LOCKED ✓] EURUSD.m | Direction: LONG | Entry: 1.0855 | Candle: 245 | Reason: ✓ Bullish engulfing CLOSE @ 1.0855
                         ⚠️  STOP checking for new confirmations - this setup is locked!

[Entry placed at 1.0855 with SL=1.0835, TP=1.0875]
```

---

## Example 2: Structure Level Break Confirmation

### Scenario
Trading GBPUSD.m with a pre-marked structure level.

```
Support Level (Recent Swing Low): 1.2650
Current Setup: LONG at 1.2655 (just above support)

Waiting for confirmation:
- Option A: Engulfing candle (bullish)
- Option B: Close ABOVE a fixed structure level
- Option C: Close above a pre-marked resistance

Candle N:
  Open:  1.2660
  Close: 1.2670    ← Previous resistance level
  High:  1.2675
  Low:   1.2658
```

### Detection
```python
# Setup active with structure level
state['setup_active'] = True
state['setup_direction'] = "long"
state['structure_level'] = 1.2665  # Previous resistance

# Confirmation check: Does price break structure?
current_price = 1.2670
structure_level = 1.2665

if current_price > structure_level:  # 1.2670 > 1.2665 ✓
    confirmation_found = True
    reason = f"Close ABOVE structure level {structure_level:.5f} by {(current_price - structure_level):.5f}"
```

### Action
```
[SETUP ACTIVE] GBPUSD.m | Direction: LONG | Price: 1.2655 | Structure Level: 1.2665

[Candle N closes at 1.2670]

[CONFIRMATION LOCKED ✓] GBPUSD.m | Direction: LONG | Entry: 1.2670 | Reason: ✓ Close ABOVE structure level 1.2665 by 0.0005
                         ⚠️  STOP checking for new confirmations - this setup is locked!

[Entry ready - trade will be executed]
```

---

## Example 3: Bearish Engulfing After Short Setup

### Scenario
Trading USDJPY.m after price touches HTF high (short setup).

```
Candle N-1 (Previous):
  Open:  150.45
  Close: 150.40
  High:  150.50
  Low:   150.35

Candle N (Current):
  Open:  150.48    ← Opens ABOVE previous open
  Close: 150.30    ← Closes BELOW previous low ✓
  High:  150.55
  Low:   150.25    ← Extends above previous high
```

### Detection
```python
# Setup: SHORT at recent HTF high
state['setup_active'] = True
state['setup_direction'] = "short"
state['setup_price'] = 150.50

# Bearish engulfing check
prev_candle = df.iloc[-2]  # open=150.45, close=150.40, high=150.50, low=150.35
curr_candle = df.iloc[-1]  # open=150.48, close=150.30, high=150.55, low=150.25

is_bearish_engulfing = (
    curr_candle['close'] < prev_candle['low'] and      # 150.30 < 150.35 ✓
    curr_candle['open'] > prev_candle['open'] and      # 150.48 > 150.45 ✓
    curr_candle['high'] > prev_candle['high']          # 150.55 > 150.50 ✓
)
# Result: TRUE - Confirmation locked!
```

### Action
```
[SETUP ACTIVE] USDJPY.m | Direction: SHORT | Price: 150.50 | Reason: Price touched HTF high

[Candle N closes]

[CONFIRMATION LOCKED ✓] USDJPY.m | Direction: SHORT | Entry: 150.30 | Candle: 389 | Reason: ✓ Bearish engulfing CLOSE @ 150.30
                         ⚠️  STOP checking for new confirmations - this setup is locked!

[Entry placed at 150.30 with SL=150.50, TP=150.00]
```

---

## Example 4: Pre-Marked Support/Resistance Break

### Scenario
Trading XAUUSD.m with recent swing points marked.

```
Recent Structure:
  Swing High (resistance): 2105.50
  Swing Low (support):      2095.00
  Second Swing High:        2103.00

Setup: SHORT triggered at 2105.00 (near recent high)
Waiting for confirmation: Close BELOW 2103.00 (pre-marked resistance)

Candle N:
  Close: 2102.50  ← Below the pre-marked resistance
```

### Detection
```python
# Setup active
state['setup_active'] = True
state['setup_direction'] = "short"
state['setup_price'] = 2105.00

# Get recent swing points
recent_highs = df['high'].tail(20).nlargest(3).values
# [2105.50, 2103.00, 2100.50]

second_highest = recent_highs[1]  # 2103.00

# Confirmation: Does price break below?
current_price = 2102.50

if current_price < second_highest:  # 2102.50 < 2103.00 ✓
    confirmation_found = True
    reason = f"Close below pre-marked resistance {second_highest:.2f}"
```

### Action
```
[SETUP ACTIVE] XAUUSD.m | Direction: SHORT | Price: 2105.00

[Candle N closes at 2102.50]

[CONFIRMATION LOCKED ✓] XAUUSD.m | Direction: SHORT | Entry: 2102.50 | Reason: ✓ Close below pre-marked resistance 2103.00
                         ⚠️  STOP checking for new confirmations - this setup is locked!

[Entry ready - Short trade will be executed]
```

---

## Example 5: Setup Invalidation (Price Breaks Setup)

### Scenario
Setup was activated, but price moves too far away without confirming.

```
Setup: LONG at 1.0840 (liquidity sweep)
Invalidation distance: 50 pips (0.0050)

Waiting for confirmation...

[10 candles later, price hasn't confirmed]
Current price: 1.0789  ← 51 pips below setup (1.0840 - 0.0051)

Check: Is price too far below setup?
Distance = 1.0840 - 1.0789 = 0.0051 (51 pips)
Invalidation threshold = 0.0050 (50 pips)

Distance > Threshold → Setup invalidated!
```

### Detection
```python
# Setup check
state['setup_active'] = True
state['setup_price'] = 1.0840
state['setup_direction'] = "long"

current_price = 1.0789

# Invalidation logic
if state['setup_direction'] == 'long':
    pip_size = 0.0001
    invalidation_price = state['setup_price'] - (50 * pip_size)  # 1.0790
    
    if current_price < invalidation_price:  # 1.0789 < 1.0790 ✓
        invalidation_triggered = True
```

### Action
```
[SETUP INVALIDATED] EURUSD.m | Long setup at 1.0840 broken. Price 1.0789 < Invalidation 1.0790
[CONFIRMATION RESET] EURUSD.m | Previous setup: LONG @ 1.0840 | Reason: Price broke setup structure

[State cleared - ready to detect new setup]
```

---

## Example 6: Multiple Setup Attempts (Correct Behavior)

### Scenario
Price touches a low twice, but only first one gets processed.

```
[Candle A] Price touches low at 1.0840
→ set_setup_active() called → setup_active = TRUE

[Candle B] Price touches another low at 1.0835
→ set_setup_active() called again
→ But setup is already active!
→ Request IGNORED
```

### Detection
```python
# First setup
set_setup_active("EURUSD.m", "long", 1.0840, reason="Liquidity sweep")
# Result: setup_active = True ✓

# Second attempt (should be ignored)
set_setup_active("EURUSD.m", "long", 1.0835, reason="Another low")
# Result: Ignored because setup_active is already True
# Log: "[SETUP EXISTS] EURUSD.m | Setup already active at 1.0840, ignoring new setup signal"
```

### Behavior
```
✓ CORRECT: Only one setup active at a time
✓ CORRECT: Prevents duplicate setups
✓ CORRECT: Waits for confirmation on first setup
```

---

## Example 7: False Breakout (Confirmation Doesn't Trigger)

### Scenario
Price breaks structure but it's a fake-out. Confirmation framework waits.

```
Setup: LONG at 1.0840

Candle N:
  High:  1.0860
  Close: 1.0858  ← Closes above previous high (looks bullish)
  But: Previous candle was small (no engulfing)

Candle N+1:
  Close: 1.0850  ← Reverses back down
```

### Detection
```python
# Candle N
prev_candle = df.iloc[-2]
curr_candle = df.iloc[-1]

# Check: Is it a FULL engulfing?
is_engulfing = (
    curr_candle['close'] > prev_candle['high'] and
    curr_candle['open'] < prev_candle['open'] and    # ← May fail here (small prev candle)
    curr_candle['low'] < prev_candle['low']
)
# If not all 3 conditions met: NOT confirmed

# Candle N+1: Price reverses
# Framework still waiting for OBJECTIVE confirmation
```

### Behavior
```
✓ CORRECT: Framework doesn't trigger on fake breakouts
✓ CORRECT: Waits for OBJECTIVE confirmation signals
✓ CORRECT: Only locks on clear engulfing or structure break
```

---

## Example 8: Complete Trade Cycle

### Full Scenario: Setup → Confirmation → Entry → Reset

```
[Candle 100] Liquidity sweep detected
→ set_setup_active("EURUSD.m", "long", 1.0840)
→ Log: "[SETUP ACTIVE] EURUSD.m | Direction: LONG | Price: 1.0840"
→ state['setup_active'] = True

[Candles 101-104] Waiting for confirmation
→ Framework checks each candle: No confirmation yet
→ state['confirmation_seen'] = False

[Candle 105] Bullish engulfing closes
→ Engulfing detected: current close > previous high
→ set_confirmation_locked("EURUSD.m", 1.0855, reason="Bullish engulfing")
→ Log: "[CONFIRMATION LOCKED ✓] EURUSD.m | Entry: 1.0855"
→ state['confirmation_seen'] = True
→ ⚠️  STOPS checking for new confirmations

[Entry placed]
→ place_trade("EURUSD.m", "long", lot=0.01, sl=1.0835, tp=1.0875)
→ Log: "[...] ORDER placed @ 1.0855"
→ reset_confirmation_state("EURUSD.m", reason="Trade executed")
→ state['setup_active'] = False
→ state['confirmation_seen'] = False

[Ready for next setup on EURUSD.m]
```

---

## Summary

| Confirmation Type | Objective? | Binary? | Example |
|-------------------|-----------|--------|---------|
| Engulfing CLOSE | ✓ Yes | ✓ Yes | "Bullish engulfing detected" |
| Structure Break | ✓ Yes | ✓ Yes | "Close above 1.0850" |
| Pre-marked Level | ✓ Yes | ✓ Yes | "Close below support 1.2650" |
| Invalidation | ✓ Yes | ✓ Yes | "Price 50+ pips away" |

**Key Point:** All confirmation checks are **objective** (no opinion) and **binary** (true/false), preventing ambiguous signals.
