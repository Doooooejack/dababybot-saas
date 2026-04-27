# ✓ ONE-TIME CONFIRMATION FRAMEWORK
## Robust Confirmation Logic for DababybotV8

---

## 📋 Overview

This framework implements a **one-time confirmation** approach to prevent multiple, conflicting entry signals on the same setup. Once a confirmation signal is detected, the bot **stops checking for new confirmations** until the trade is executed and the state is reset.

**Key principle:**
> "I've seen enough. Now I act." — Once confirmed, no more signal checking.

---

## 🎯 The 4-Step Flow

### STEP 1️⃣: DETECT THE SETUP
**When:** Liquidity sweep happens OR price touches HTF level
**What:** `setup_active = true`
**Function:** `set_setup_active(symbol, direction, price, reason="")`

```python
# Example: Setup detected at EURUSD when liquidity sweep happens
set_setup_active("EURUSD.m", "long", 1.0850, reason="Liquidity sweep at swing low")
```

**Characteristics of a valid setup:**
- Liquidity sweep (HTF highs/lows being swept)
- Price touch of recent HTF level (within 10 pips)
- Order block at support/resistance level
- Clear structural point with volume confirmation

---

### STEP 2️⃣: WAIT FOR CONFIRMATION (ONLY ONCE)

**When:** Price action confirms the setup direction
**What:** `confirmation_seen = true` (and NEVER check for confirmation again)
**Function:** `set_confirmation_locked(symbol, price, reason="", candle_index=None)`

**Valid confirmation signals (OBJECTIVE & BINARY):**

#### ✓ Bullish/Bearish Engulfing CLOSE
- **Bullish:** Current candle closes ABOVE previous candle's high
- **Bearish:** Current candle closes BELOW previous candle's low
- Binary: Either it happens or it doesn't
- No ambiguity

```python
# Bullish Engulfing Requirements:
# - curr_close > prev_high         (closes above previous high)
# - curr_open < prev_open          (opens below previous open)
# - curr_low < prev_low            (engulfs to downside)
```

#### ✓ Close Beyond Fixed Structure Level
- **For LONG:** Close ABOVE the structure level (resistance break)
- **For SHORT:** Close BELOW the structure level (support break)
- Objective: Clear price level, no interpretation

```python
# Example: Structure level at 1.0830
if direction == "long":
    if close > 1.0830:  # CONFIRMED
        confirmation_seen = true
```

#### ✓ Close Above/Below Pre-Marked Level
- **For LONG:** Close above a recent swing high (pre-marked resistance)
- **For SHORT:** Close below a recent swing low (pre-marked support)
- Uses recent order blocks or structure highs/lows

---

### STEP 3️⃣: LOCK & STORE
**When:** Confirmation signal occurs
**What:** `confirmation_candle_index = current_candle`
**State saved:**
```python
confirmation_state = {
    'setup_active': True,
    'confirmation_seen': True,              # ✓ LOCKED
    'confirmation_candle_index': 245,       # Candle where confirmation occurred
    'confirmation_price': 1.0855,
    'confirmation_reason': "Bullish engulfing CLOSE",
    'setup_direction': "long"
}
```

**⚠️ CRITICAL:** After this point, the framework **STOPS checking for new confirmations** on this symbol. The state is frozen until the trade is executed.

---

### STEP 4️⃣: ENTRY EXECUTION (RESET)
**When:** Trade is successfully placed
**What:** Reset the state for the next setup
**Function:** `reset_confirmation_state(symbol, reason="")`

```python
# After place_trade() succeeds:
reset_confirmation_state("EURUSD.m", reason="Trade executed: LONG @ 1.0855")

# Now the bot can detect a NEW setup on this symbol
```

---

## 🔧 Integration into Trading Loop

### Quick Start: Use `check_and_process_confirmation_for_symbol()`

```python
# In your main trading loop:
for symbol in SYMBOLS:
    df = get_price_data(symbol, bars=500)
    if df is None or len(df) < 20:
        continue
    
    # Check setup and confirmation status
    should_enter, direction, entry_price, reason = check_and_process_confirmation_for_symbol(symbol, df)
    
    if should_enter:
        print(f"[ENTRY READY] {symbol} {direction.upper()} @ {entry_price:.5f}")
        print(f"[REASON] {reason}")
        
        # Calculate SL/TP based on setup
        sl, tp = calculate_sl_tp(symbol, direction, entry_price, df)
        
        # Place the trade
        place_trade(symbol, direction, lot, sl, tp)
        # ✓ place_trade() automatically resets the confirmation state
```

---

## 📊 Confirmation State Tracking

### Check Current Status

```python
# Get state for a symbol
state = get_confirmation_state("EURUSD.m")

print(f"Setup active: {state['setup_active']}")
print(f"Confirmation locked: {state['confirmation_seen']}")
print(f"Setup direction: {state['setup_direction']}")
print(f"Setup price: {state['setup_price']:.5f}")
print(f"Confirmation price: {state['confirmation_price']:.5f}")
print(f"Reason: {state['confirmation_reason']}")
```

### Check if Ready to Enter

```python
# Simple yes/no check
if has_locked_confirmation("EURUSD.m"):
    print("ENTRY IS READY - Trade is confirmed and locked!")
```

### Print All Symbols Status

```python
# Debug: See all symbols at a glance
print_confirmation_status_all_symbols(symbols=["EURUSD.m", "GBPUSD.m", "XAUUSD.m"])

# Output:
# [CONFIRMATION STATUS] Current state for all symbols
# ════════════════════════════════════════════════════════════════════════════════════════════════════
#   EURUSD.m        ✓ CONFIRMED           Setup: LONG @ 1.0850     Confirm: 1.0855
#   GBPUSD.m        ⚠ SETUP ACTIVE        Setup: SHORT @ 1.2710    Confirm: N/A
#   XAUUSD.m        ○ IDLE                Setup: N/A               Confirm: N/A
```

---

## 🎨 Configuration Examples

### Example 1: Manual Setup Activation with Structure Level

```python
# When you detect a liquidity sweep manually:
set_setup_active(
    symbol="EURUSD.m",
    direction="long",
    price=1.0840,
    reason="Liquidity sweep at swing low (HTF confirmed)",
    structure_level=1.0830  # Support level to watch
)

# Now the framework waits for:
# - Engulfing close, OR
# - Close above 1.0830, OR
# - Close above a pre-marked resistance
```

### Example 2: Check Setup Invalidation

```python
# Call periodically to invalidate broken setups
current_price = 1.0810  # Price moved against setup

invalidated = check_setup_invalidation(
    "EURUSD.m",
    current_price,
    invalidation_distance_pips=50  # Break setup if 50+ pips away
)

if invalidated:
    print("Setup broken! Reset and ready for new setup")
```

### Example 3: Manual Confirmation Lock

```python
# If you detect a confirmation manually (e.g., engulfing candle):
set_confirmation_locked(
    symbol="EURUSD.m",
    price=1.0855,
    reason="Bullish engulfing CLOSE confirmed",
    candle_index=245
)

# Now ready for entry!
state = get_confirmation_state("EURUSD.m")
print(f"ENTRY READY at {state['confirmation_price']:.5f}")
```

---

## ⚠️ Important Behaviors

### 1. One-Time Trigger
```python
# ✓ CORRECT: Confirmation locked, stops checking
set_confirmation_locked("EURUSD.m", 1.0855, reason="...")
set_confirmation_locked("EURUSD.m", 1.0856, reason="...")  # IGNORED!
# → Second call is ignored, state already locked

# ✗ WRONG: Calling without setup active
# set_confirmation_locked("EURUSD.m", 1.0855)  # No effect if no setup
```

### 2. Setup Can Only Be Active Once
```python
set_setup_active("EURUSD.m", "long", 1.0840, ...)   # ✓ Activated
set_setup_active("EURUSD.m", "short", 1.0860, ...)  # ✗ Ignored - setup already active
```

### 3. Reset Clears Everything
```python
# Before reset:
state['setup_active'] = True
state['confirmation_seen'] = True
state['setup_price'] = 1.0840
state['confirmation_price'] = 1.0855

reset_confirmation_state("EURUSD.m", reason="Trade executed")

# After reset:
state['setup_active'] = False          # ✓ Cleared
state['confirmation_seen'] = False     # ✓ Cleared
state['setup_price'] = None            # ✓ Cleared
state['confirmation_price'] = None     # ✓ Cleared
# → Ready to detect NEW setup
```

---

## 📈 Usage Flow in Main Loop

```python
def main_trading_loop():
    while True:
        for symbol in SYMBOLS:
            # Load latest data
            df = get_price_data(symbol, bars=500)
            if df is None or len(df) < 20:
                continue
            
            # === CONFIRMATION FRAMEWORK CHECK ===
            should_enter, direction, entry_price, reason = check_and_process_confirmation_for_symbol(symbol, df)
            
            if should_enter:
                print(f"[ENTRY] {symbol} {direction.upper()} @ {entry_price:.5f}")
                print(f"[REASON] {reason}")
                
                # Calculate trade parameters
                atr = calculate_atr(df)
                sl = entry_price - atr if direction == "long" else entry_price + atr
                tp = entry_price + atr * 2 if direction == "long" else entry_price - atr * 2
                
                # Place trade
                place_trade(symbol, direction, lot=0.01, sl=sl, tp=tp)
                # ✓ place_trade() auto-resets confirmation state
            
            # Check if setup needs to be invalidated
            check_setup_invalidation(symbol, df['close'].iloc[-1], invalidation_distance_pips=50)
            
            # Debug: Print status every N candles
            if len(df) % 50 == 0:
                print_confirmation_status_all_symbols(symbols=[symbol])
        
        time.sleep(60)  # Check every minute
```

---

## 🐛 Debugging Tips

### Check State Without Printing
```python
state = get_confirmation_state("EURUSD.m")
print(f"State dict: {state}")
```

### Manual Status Check
```python
# Quick one-liner checks
if get_confirmation_state("EURUSD.m")['setup_active']:
    print("Setup is active")

if has_locked_confirmation("EURUSD.m"):
    print("Ready to enter!")
```

### Reset a Stuck Symbol
```python
# If a symbol gets stuck in setup/confirmation, force reset:
reset_confirmation_state("EURUSD.m", reason="Manual reset - stuck state")
```

---

## ✅ Checklist Before Using

- [ ] Load historical data (minimum 20 candles)
- [ ] Set up `get_price_data()` function
- [ ] Integrate `check_and_process_confirmation_for_symbol()` into main loop
- [ ] Call `reset_confirmation_state()` after `place_trade()` succeeds
- [ ] Test on 1-2 symbols first before running on all symbols
- [ ] Monitor logs for "SETUP ACTIVE" and "CONFIRMATION LOCKED" messages

---

## 🎓 Why This Framework Works

1. **No Multiple Entries:** Once confirmed, the state is locked. No more signal checking.
2. **Objective Rules:** Confirmation checks are binary (true/false), not subjective.
3. **Memory:** The framework remembers each step (setup → confirmation → entry)
4. **Scalable:** Works for any number of symbols independently
5. **Flexible:** You can add custom confirmation rules by modifying `detect_and_lock_confirmation()`

---

## 📚 API Reference

### State Management Functions

| Function | Purpose |
|----------|---------|
| `set_setup_active()` | Activate a setup (STEP 1) |
| `set_confirmation_locked()` | Lock a confirmation (STEP 2-3) |
| `reset_confirmation_state()` | Reset for new setup (STEP 4) |
| `get_confirmation_state()` | Query current state |
| `has_locked_confirmation()` | Check if ready to enter |
| `check_setup_invalidation()` | Invalidate broken setups |
| `check_and_process_confirmation_for_symbol()` | Main integration function |

### Detection Functions

| Function | Purpose |
|----------|---------|
| `detect_and_activate_setup()` | Auto-detect setup conditions |
| `detect_and_lock_confirmation()` | Auto-detect confirmation signals |
| `print_confirmation_status_all_symbols()` | Debug status display |

---

## 📝 Log Output Examples

### Setup Detected
```
[SETUP ACTIVE] EURUSD.m | Direction: LONG | Price: 1.0850 | Structure Level: 1.0830 | Reason: Liquidity sweep detected on HTF
```

### Confirmation Locked
```
[CONFIRMATION LOCKED ✓] EURUSD.m | Direction: LONG | Entry: 1.0855 | Time since setup: 15.3s | Candle: 245 | Reason: ✓ Bullish engulfing CLOSE @ 1.0855
                         ⚠️  STOP checking for new confirmations - this setup is locked!
```

### Trade Reset
```
[CONFIRMATION RESET] EURUSD.m | Previous setup: LONG @ 1.0850 | Reason: Trade executed: LONG @ 1.0855
```

---

**Version:** 1.0  
**Last Updated:** January 8, 2026  
**Framework Status:** ✅ PRODUCTION READY
