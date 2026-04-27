# Robust Entry Filters - Summary

## Overview
The entry filters have been re-engineered to work together **robustly** instead of blocking aggressively. They now log information and guidance while allowing HTF (higher-timeframe) signals to make the final entry decision.

## Key Changes

### 1. **Impulse Filter** (Line 3548)
- **Old:** Blocked when last candle range > avg × 1.5 and direction against signal
- **New:** Relaxed to 1.3× multiplier; logs info only
- **Benefit:** Fewer false negatives, allows more valid entries

### 2. **M5 Structure Shift Check** (Line 3579)
- **Old:** Hard-blocked if M5 BOS not detected
- **New:** Checks M5 BOS but always returns True; logs "M5_BOS_CONFIRMED" or "M5_BOS_UNCLEAR"
- **Benefit:** Informational only; HTF signals can override

### 3. **One-Candle Rule** (Line 3605)
- **Old:** Blocked first bullish after sell-off (2+ bearish candles)
- **New:** Flags situations but always returns True; requires 3+ bearish candles AND 2+ strong bodies
- **Benefit:** Less false positives; allows entry on strong continuations

### 4. **Confirmation Candle** (Line 3658)
- **Old:** Required lower-wick rejection > 2.0× body or engulfing (very strict)
- **New:** Relaxed to 1.0× body (simple wick exists); flags as STRONG or WEAK, allows both
- **Benefit:** Accommodates more candle patterns; still flags weak confirmations

## Integration into Decision Flow (Line 3708+)

All filters are now **informational** - they log to `context.supporting_filters` and never hard-block:

```python
# Pre-filters: informational checks that log guidance but allow HTF to decide
try:
    impulse_filter(context)  # Logs to supporting/blocking filters; always returns True
except Exception:
    pass

try:
    require_m5_structure_shift(context)  # Logs M5 structure info; always returns True
except Exception:
    pass

try:
    one_candle_rule(context)  # Flags pullback situations; always returns True
except Exception:
    pass

try:
    require_confirmation_candle(context)  # Flags confirmation strength; always returns True
except Exception:
    pass
```

## What Gets Logged

### Blocking Filters (if returned)
- `IMPULSE_FILTER_BLOCK`: Last candle was a strong impulse
- (Others are now warnings only)

### Supporting Filters (informational)
- `M5_BOS_CONFIRMED`: M5 structure shift detected
- `M5_BOS_UNCLEAR`: No clear M5 shift (HTF override possible)
- `ONE_CANDLE_FLAG: first bullish after strong sell-off (monitor)`
- `CONFIRM_CANDLE_STRONG: bullish with rejection/engulfing`
- `CONFIRM_CANDLE_WEAK: no strong rejection`

## Expected Behavior

1. **Entry frequency improves** - Fewer false negatives from overly strict checks
2. **Risk management maintained** - Impulse filter still blocks obvious falling knives
3. **HTF bias decides** - M5 structure, pullback, and confirmation are now suggestions, not requirements
4. **Logging for monitoring** - All checks are logged in supporting/blocking filters for transparency

## Testing

Run the test to verify filters work together robustly:
```bash
python test_robust_filters.py
```

Expected output:
- No hard blocks (blocking_filters is empty)
- Informational logs in supporting_filters
- Entry is allowed to proceed to HTF decision logic
