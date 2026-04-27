# QUICK REFERENCE: One-Time Confirmation Framework

## The 4 Steps (Simplified)

```
STEP 1: Setup Detected
  └─ set_setup_active(symbol, "long/short", price, reason)
  
STEP 2: Wait for Confirmation
  └─ detect_and_lock_confirmation() automatically checks for:
     • Engulfing candle CLOSE
     • Close beyond structure level
     • Close above/below pre-marked level
  
STEP 3: Confirmation Locked
  └─ set_confirmation_locked(symbol, price, reason)
  └─ ⚠️  STOPS checking for new confirmations
  
STEP 4: Entry & Reset
  └─ place_trade() succeeds
  └─ reset_confirmation_state(symbol, reason)
  └─ Ready for next setup
```

---

## Main Integration Function

```python
# Call this in your main loop for each symbol
should_enter, direction, entry_price, reason = check_and_process_confirmation_for_symbol(symbol, df)

if should_enter:
    print(f"ENTER: {symbol} {direction.upper()} @ {entry_price}")
    place_trade(symbol, direction, lot, sl, tp)
```

---

## State Checks

```python
# Is ready to enter?
if has_locked_confirmation("EURUSD.m"):
    print("READY TO ENTER!")

# Get full state
state = get_confirmation_state("EURUSD.m")
print(state['setup_active'])
print(state['confirmation_seen'])
print(state['setup_direction'])
print(state['confirmation_price'])

# Reset if stuck
reset_confirmation_state("EURUSD.m", reason="Manual reset")

# View all symbols
print_confirmation_status_all_symbols()
```

---

## Objective Confirmations

✓ **Bullish Engulfing:** Current candle closes ABOVE previous high  
✓ **Bearish Engulfing:** Current candle closes BELOW previous low  
✓ **Structure Break:** Close beyond fixed support/resistance level  
✓ **Pre-marked Level:** Close above/below recent swing high/low  

---

## Log Markers

```
[SETUP ACTIVE]           → Setup detected, waiting for confirmation
[CONFIRMATION LOCKED ✓]  → Confirmation found, STOP checking
[CONFIRMATION RESET]     → Trade executed, ready for new setup
[SETUP EXISTS]          → Duplicate setup ignored
[SETUP INVALIDATED]     → Setup broken by price movement
```

---

## Embedded in place_trade()

✅ **Automatically called:**
```python
# Inside place_trade() after successful order:
reset_confirmation_state(resolved_symbol, reason=f"Trade executed: {direction.upper()}")
```

No manual reset needed if using `place_trade()`!

---

## Example Loop

```python
def main_loop():
    while True:
        for symbol in SYMBOLS:
            df = get_price_data(symbol, bars=500)
            if df is None: continue
            
            # Framework checks everything
            should_enter, dir, price, reason = check_and_process_confirmation_for_symbol(symbol, df)
            
            if should_enter:
                sl = price - 0.001
                tp = price + 0.002
                place_trade(symbol, dir, 0.01, sl, tp)
                # Auto reset happens here!
        
        time.sleep(60)
```

---

**Status:** ✅ READY TO USE
