# Code Changes Reference - Enhanced Entry Rules

## Where Everything Was Added

### File: `botfriday6000th.py`

---

## NEW FUNCTIONS (195 lines total)

### 1. `check_pullback_rule(context)` - Lines 950-1010

```python
def check_pullback_rule(context):
    """
    PULLBACK RULE: After BOS, require 50-70% retracement OR FVG tap.
    """
    # ... 60 lines of implementation
    # Returns: (pullback_valid, retrace_percent, pullback_reason)
```

**What it does:**
- Detects impulse high/low from last 20 candles
- Calculates 50-70% retracement zone
- Checks if current price in that zone
- Allows FVG tap as alternative
- Returns True if valid pullback found

---

### 2. `check_htf_demand_reaction(context)` - Lines 1020-1085

```python
def check_htf_demand_reaction(context):
    """
    HTF FILTER: Only allow BUY if H4 bullish OR reacting from demand.
    Only allow SELL if H4 bearish OR reacting from supply.
    """
    # ... 65 lines of implementation
    # Returns: (htf_ok, reason)
```

**What it does:**
- Gets H4 EMA alignment (21, 50, 200)
- Finds recent swing high/low
- For BUY: Allows if bullish OR near demand
- For SELL: Allows if bearish OR near supply
- Returns True if H4 confirms entry

---

### 3. `check_entry_tf_confirmation(context)` - Lines 1090-1160

```python
def check_entry_tf_confirmation(context):
    """
    ENTRY TF REFINEMENT: Use M5/M15 entry confirmation.
    Requires M5 BOS + rejection candle (pin bar/engulfing).
    """
    # ... 70 lines of implementation
    # Returns: (entry_tf_valid, confirmation_type, confidence_boost)
```

**What it does:**
- Detects M5 BOS above/below recent high/low
- Identifies rejection candles (pin bars, engulfing)
- Awards confidence boost based on pattern strength
- Returns True + boost% if M5 confirms entry

---

## INTEGRATION POINTS (40 lines added)

### Location: `compute_unified_decision(context)` - Lines 2048-2087

**Before:**
```python
    # --- BOS CONFIRMATION IS NOW MANDATORY ---
    bos = context.fvg_analysis.get("bos", None)
    bos_confirmed = bos is not None and bos == context.signal

    # --- MOMENTUM OVERRIDE LOGIC ---
    # Define what constitutes a "strong impulse candle"
    def is_strong_impulse_candle(df, signal):
```

**After:**
```python
    # --- BOS CONFIRMATION IS NOW MANDATORY ---
    bos = context.fvg_analysis.get("bos", None)
    bos_confirmed = bos is not None and bos == context.signal

    # ========== NEW ENHANCED ENTRY FILTERS ==========
    # 1. PULLBACK RULE
    pullback_valid, retrace_pct, pullback_reason = check_pullback_rule(context)
    if bos_confirmed and not pullback_valid:
        context.should_trade = False
        context.trade_quality_score = 0.0
        context.reason = f"BLOCKED: {pullback_reason}"
        context.blocking_filters.append(f"NO_PULLBACK_RULE: {pullback_reason}")
        return
    elif pullback_valid:
        context.supporting_filters.append(f"PULLBACK_RULE_OK: {pullback_reason}")
        ml_base = min(1.0, ml_base + 0.12)

    # 2. HTF DEMAND/SUPPLY REACTION
    htf_ok, htf_reason = check_htf_demand_reaction(context)
    if not htf_ok:
        context.should_trade = False
        context.trade_quality_score = 0.0
        context.reason = f"BLOCKED: {htf_reason}"
        context.blocking_filters.append(f"HTF_FILTER: {htf_reason}")
        return
    else:
        context.supporting_filters.append(f"HTF_FILTER_OK: {htf_reason}")
        ml_base = min(1.0, ml_base + 0.10)

    # 3. ENTRY TF CONFIRMATION
    entry_tf_valid, entry_tf_type, entry_tf_boost = check_entry_tf_confirmation(context)
    if not entry_tf_valid:
        context.should_trade = False
        context.trade_quality_score = 0.0
        context.reason = f"BLOCKED: {entry_tf_type}"
        context.blocking_filters.append(f"ENTRY_TF: {entry_tf_type}")
        return
    else:
        context.supporting_filters.append(f"ENTRY_TF_OK: {entry_tf_type}")
        ml_base = min(1.0, ml_base + entry_tf_boost)

    # ========== END NEW ENHANCED FILTERS ==========

    # --- MOMENTUM OVERRIDE LOGIC ---
    # Define what constitutes a "strong impulse candle"
    def is_strong_impulse_candle(df, signal):
```

---

## Summary of Changes

### Code Statistics
- **New functions**: 3 (check_pullback_rule, check_htf_demand_reaction, check_entry_tf_confirmation)
- **Lines added**: 235 total
  - Pullback rule: 60 lines
  - HTF filter: 65 lines
  - Entry TF: 70 lines
  - Integration: 40 lines

- **Functions modified**: 1 (compute_unified_decision)
- **Functions removed**: 0 (backward compatible)
- **Breaking changes**: 0 (all new code doesn't conflict)

### Logic Flow
1. Check pullback rule → BLOCK if fail, +12% if pass
2. Check HTF filter → BLOCK if fail, +10% if pass
3. Check entry TF confirmation → BLOCK if fail, +8-20% if pass
4. Continue with existing downstream logic

### Confidence Boosts Applied
- Pullback Rule: +12%
- HTF Filter: +10%
- Entry TF (pin bar): +20%
- Entry TF (engulfing): +15%
- Entry TF (BOS only): +8%

### Blocking Logic
Each filter can independently BLOCK the entry:
```python
if not pullback_valid:
    context.should_trade = False
    return  # Exit early, don't check other filters

if not htf_ok:
    context.should_trade = False
    return  # Exit early

if not entry_tf_valid:
    context.should_trade = False
    return  # Exit early
```

---

## Testing the Implementation

### Verify Installation
```bash
# Check if functions exist
grep -n "def check_pullback_rule" botfriday6000th.py
grep -n "def check_htf_demand" botfriday6000th.py
grep -n "def check_entry_tf" botfriday6000th.py
```

### Verify Integration
```bash
# Check if called in compute_unified_decision
grep -n "check_pullback_rule(context)" botfriday6000th.py
grep -n "check_htf_demand_reaction(context)" botfriday6000th.py
grep -n "check_entry_tf_confirmation(context)" botfriday6000th.py
```

### Verify Blocking Logic
```bash
# Check if properly integrated with early returns
grep -n "context.should_trade = False" botfriday6000th.py | grep -A1 "pullback"
grep -n "context.should_trade = False" botfriday6000th.py | grep -A1 "htf_filter"
grep -n "context.should_trade = False" botfriday6000th.py | grep -A1 "entry_tf"
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 22, 2025 | Initial implementation of 3-filter system |

---

## How to Modify

### Change Pullback Zone
**File**: botfriday6000th.py  
**Lines**: 975-976

From:
```python
pullback_50 = impulse_high - 0.5 * impulse_body
pullback_70 = impulse_high - 0.7 * impulse_body
```

To (more aggressive):
```python
pullback_50 = impulse_high - 0.4 * impulse_body  # 40% retrace
pullback_70 = impulse_high - 0.8 * impulse_body  # 80% retrace
```

### Change HTF Demand Zone Size
**File**: botfriday6000th.py  
**Line**: 1048

From:
```python
demand_zone_threshold = 15 * pip_size
```

To (tighter):
```python
demand_zone_threshold = 10 * pip_size  # 10 pips instead of 15
```

### Require Pin Bar Always
**File**: botfriday6000th.py  
**Lines**: 1130-1145

Change to reject M5 BOS without pin bar:
```python
# STRICT: Only accept pin bar + BOS
if is_rejection_candle(last, signal):
    return True, "BUY_M5_BOS_REJECTION", 0.20
else:
    return False, "NO_PIN_BAR_REQUIRED", 0.0  # Strict version
```

---

## Rollback Instructions

If you need to disable the new filters temporarily:

### Option 1: Comment Out Integration
**Lines 2049-2087 in compute_unified_decision()**

```python
# ========== NEW ENHANCED ENTRY FILTERS ========== (DISABLED)
# pullback_valid, retrace_pct, pullback_reason = check_pullback_rule(context)
# if bos_confirmed and not pullback_valid:
# ... rest of filter code commented
# ========== END NEW ENHANCED FILTERS ==========
```

### Option 2: Remove Functions Entirely
Delete lines 950-1010, 1020-1085, 1090-1160  
Delete lines 2049-2087

Then revert integration changes only.

### Option 3: Always Pass Filters
Change filter checks to always return True:
```python
pullback_valid = True  # Always pass
htf_ok = True  # Always pass
entry_tf_valid = True  # Always pass
```

---

## Verify It Works

After implementation, run this test:

```python
# Test pullback rule
from botfriday6000th import check_pullback_rule
context = ...  # your context object
valid, pct, reason = check_pullback_rule(context)
print(f"Pullback valid: {valid}, percent: {pct}, reason: {reason}")

# Test HTF filter
from botfriday6000th import check_htf_demand_reaction
ok, reason = check_htf_demand_reaction(context)
print(f"HTF OK: {ok}, reason: {reason}")

# Test entry TF
from botfriday6000th import check_entry_tf_confirmation
valid, type, boost = check_entry_tf_confirmation(context)
print(f"Entry TF valid: {valid}, type: {type}, boost: {boost}")
```

---

## Next: Test & Deploy

1. ✅ Implementation complete
2. ⏭️ Run backtest (4-6 hours)
3. ⏭️ Walk-forward test (2 hours)
4. ⏭️ Paper trade (1-2 weeks)
5. ⏭️ Live trade (0.1 lot size)

Good luck! 🚀
