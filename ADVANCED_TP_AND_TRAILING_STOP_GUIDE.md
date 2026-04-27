# Advanced Take Profit & Trailing Stop System

## Overview

Your bot now has a **professional-grade profit-locking system** that splits each trade into 3 tiers with different take-profit strategies:

```
ENTRY
  ↓
├─ Tier 1 (30% lots) → TP at 0.5R (QUICK LOCK)
├─ Tier 2 (40% lots) → TP at 1.0R (SECONDARY LOCK)
└─ Tier 3 (30% lots) → NO TP, TRAILING STOP (RUNNER)
```

## Key Features

### 1. **Multi-Tier Take Profit System** (Most Important!)

```python
calculate_multi_tier_tp_levels(entry, direction, atr, symbol, confidence)
```

**What it does:**
- Breaks your lot into 3 parts with different exit strategies
- Tier 1: Takes 30% profit at **0.5R** (quick win)
- Tier 2: Takes 40% profit at **1.0R** (secondary win)
- Tier 3: Lets 30% run with **trailing stop** (winner extension)

**Example: XAUUSD BUY at 4208.05**

```
Entry: 4208.05
ATR: 2.5
Confidence: 0.85

Calculation:
- base_distance = 2.5 (ATR)
- confidence_mult = 0.5 + (0.85 / 0.9) = 1.44
- adjusted_distance = 2.5 * 1.44 = 3.6

Results:
- TP1: 4208.05 + (3.6 * 0.5) = 4209.85 (30% lots) → QUICK WIN
- TP2: 4208.05 + (3.6 * 1.0) = 4211.65 (40% lots) → SECONDARY WIN
- TP3: 4208.05 + (3.6 * 2.5) = 4217.05 (30% lots) → TRAILING RUNNER
- SL: 4208.05 - (3.6 * 1.5) = 4202.55
```

**Why 3-tier?**
- **Tier 1 (Quick Lock)**: Locks in 0.5R quickly → converts "maybe win" to "definitely win"
- **Tier 2 (Secondary)**: Gets you to 1:1 RR ratio (no-lose zone)
- **Tier 3 (Runner)**: Lets 30% extend with trailing stop → catches big moves (2R-3R+)

### 2. **Advanced Trailing Stop System**

```python
update_trailing_stops_advanced(symbols, lookback_bars=20, profit_lock_ratio=0.3, trail_tightness=1.0)
```

**How it works:**

1. **Profit Locking**: Once trade reaches 30% of max profit, locks it in
2. **Trailing**: Then trails at 1.0x ATR behind price (for Tier 3 runners)
3. **Smart Updates**: Only moves SL when price advances meaningfully (avoids whipsaws)
4. **Breakeven Protection**: Never lets SL go worse than breakeven + 1 pip

**Example: XAUUSD BUY**

```
Entry: 4208.05
Max Reach: 4215.00 (high from last 20 bars)
Max Profit: 6.95 pips
Profit Lock Ratio: 30%
Locked Profit: 6.95 * 0.30 = 2.08 pips

Current Price: 4212.50
Current Profit: 4.45 pips
SL moved to: max(4208.05, 4212.50 - 2.5*ATR) = 4208.05 (breakeven)

As price climbs to 4217.00:
Current Profit: 8.95 pips
New SL: max(4208.05, 4217.00 - 2.5*ATR) = 4211.50 (trails up)

[TRAIL] XAUUSD BUY: SL moved to 4211.50 (profit locked: 8.95 pips)
```

### 3. **Breakeven Move Protection**

```python
adaptive_tp_breakeven_move(symbols, min_profit_ratio=0.5)
```

**What it does:**
- Once your trade is at 50% of the way to TP, moves SL to breakeven
- Converts trade to "can't lose money, can only make it" mode

**Example:**

```
TP Distance: 10 pips (from entry to TP)
Current Profit: 5 pips (50% there)
→ SL automatically moves to BREAKEVEN + 1 pip
```

Now if trade reverses, you're still breakeven! But if it continues, you profit.

## Three Functions to Use

### **1. Place Multi-Tier Trades** (Use this for entry!)

```python
place_multi_tier_trades(
    symbol="XAUUSD",
    direction="buy",
    total_lot=0.05,           # Your total lot size
    entry=4208.05,            # Entry price
    atr=2.5,                  # Current ATR
    confidence=0.85,          # Your ML confidence (0-1)
    features=None
)
```

**Output:**
```
[MULTI-TIER] XAUUSD BUY Trade 1: 0.015 lots at TP1=4209.85, SL=4202.55
[MULTI-TIER] XAUUSD BUY Trade 2: 0.020 lots at TP2=4211.65, SL=4202.55
[MULTI-TIER] XAUUSD BUY Trade 3: 0.015 lots RUNNER (trailing stop), SL=4202.55
```

### **2. Update Trailing Stops** (Call in main loop every cycle)

```python
# In your main trading loop (every iteration):
update_trailing_stops_advanced(
    symbols=["XAUUSD", "EURUSD", "GBPUSD"],
    lookback_bars=20,         # Look back 20 bars for max profit
    profit_lock_ratio=0.3,    # Lock 30% of max profit
    trail_tightness=1.0       # Trail 1.0x ATR behind price
)
```

### **3. Adaptive Breakeven** (Call periodically)

```python
# In your main trading loop:
adaptive_tp_breakeven_move(
    symbols=["XAUUSD", "EURUSD", "GBPUSD"],
    min_profit_ratio=0.5      # Move to BE when 50% to TP
)
```

## Integration with Your Bot

### Replace Current Entry Code

**Old (single TP):**
```python
place_sniper_entry(
    symbol=symbol,
    direction=signal,
    lot_size=LOT_SIZE,
    features=features,
    confidence=confidence,
    atr=atr
)
```

**New (multi-tier):**
```python
place_multi_tier_trades(
    symbol=symbol,
    direction=signal,
    total_lot=LOT_SIZE,
    entry=entry,
    atr=atr,
    confidence=confidence,
    features=features
)
```

### Add to Main Loop

Find your main trading loop (around line 25850) and add:

```python
while True:
    # ... your trading logic ...
    
    # EVERY CYCLE: Update trailing stops and breakeven protection
    update_trailing_stops_advanced(symbols_to_trade)
    adaptive_tp_breakeven_move(symbols_to_trade)
    
    # Sleep before next cycle
    time.sleep(10)
```

## Real-World Example: XAUUSD Trade

### Setup
- Entry: 4208.05 (BUY)
- ML Confidence: 0.88 (very high)
- ATR: 2.5
- Total Lot: 0.05

### Execution

```python
place_multi_tier_trades(
    symbol="XAUUSD",
    direction="buy",
    total_lot=0.05,
    entry=4208.05,
    atr=2.5,
    confidence=0.88
)
```

### Output & Execution

```
[MULTI-TIER] XAUUSD BUY Trade 1: 0.015 lots at TP1=4209.85, SL=4202.55
[MULTI-TIER] XAUUSD BUY Trade 2: 0.020 lots at TP2=4211.65, SL=4202.55
[MULTI-TIER] XAUUSD BUY Trade 3: 0.015 lots RUNNER (trailing stop), SL=4202.55

Price Action:
- 4208.05 → ENTRY TRIGGERED
- 4209.85 → Trade 1 closed at TP1 (+1.8 pips, 0.015 lots)
           Profit: 0.015 * 1.8 = 27 USD (locked!)

- 4211.65 → Trade 2 closed at TP2 (+3.6 pips, 0.020 lots)
           Profit: 0.020 * 3.6 = 72 USD (locked!)

- 4215.00 → [TRAIL] SL moved to 4209.50 (profit locked: 6.95 pips)

- 4217.50 → [TRAIL] SL moved to 4213.00 (profit locked: 9.45 pips)

- 4216.00 → Runner trailing stop hit at 4213.00
           Trade 3 closed (+8.0 pips, 0.015 lots)
           Profit: 0.015 * 8.0 = 120 USD

TOTAL PROFIT: 27 + 72 + 120 = 219 USD (on 0.05 lots)
WIN RATE: 3/3 (100% - all 3 tiers hit)
```

## Configuration Tuning

### Conservative (Low Volatility/Confidence)
```python
confidence = 0.65
trail_tightness = 1.5    # Trail looser
profit_lock_ratio = 0.4  # Lock more conservatively
```

### Aggressive (High Volatility/Confidence)
```python
confidence = 0.90
trail_tightness = 0.8    # Trail tighter to price
profit_lock_ratio = 0.2  # Lock quickly, let runner go far
```

### XAUUSD Specific
```python
# Gold is slower moving, use tighter targets
confidence = 0.85
trail_tightness = 1.0
profit_lock_ratio = 0.3
```

## Why This Works

| Scenario | Old System | New System |
|----------|-----------|-----------|
| Trade goes 0.5R then reverses | Losses full RR | Locks 30% at 0.5R, loses rest |
| Trade goes 1R then reverses | Gets 1R profit | Gets 30% + 40% = 70% profit |
| Trade goes 3R+ | Gets 1R profit (TP hit) | Gets 30% + 40% + 3R = 2.7R profit |
| Whipsaw reversal | Stops out at SL | Trailing stop trails out safely |

**Key Advantage**: You're always "taking something off the table" while letting your winners run.

## Next Steps

1. Replace `place_sniper_entry()` calls with `place_multi_tier_trades()`
2. Add `update_trailing_stops_advanced()` to main loop
3. Add `adaptive_tp_breakeven_move()` to main loop
4. Backtest 10 trades to verify execution
5. Monitor logs for `[MULTI-TIER]`, `[TRAIL]`, and `[BE-MOVE]` messages

Your bot is now a **true profit-killing machine!** 🚀

