# Model Loading Fix - Symbol Suffix Issue

## Problem Identified
Your models were NOT actually missing - they exist on disk with these names:
- `model_lgb_XAUUSD.txt`
- `model_rf_XAUUSD.pkl`
- `model_xgb_XAUUSD.json`
- etc. for all symbols

But the bot was trying to look them up under the **live trading symbol names** which include the `.m` suffix:
- Live symbol: `XAUUSD.m` (what MT5 returns)
- Lookup: `lgb_models["XAUUSD.m"]` ❌ (NOT FOUND)
- Actual storage: `lgb_models["XAUUSD"]` ✓ (loaded at startup)

## Root Cause
1. **Model loading at startup** (line 9375-9400):
   - Loads models under base symbol names: `XAUUSD`, `EURUSD`, etc.
   - Stores them in dictionaries: `lgb_models["XAUUSD"]`, `rf_models["EURUSD"]`, etc.

2. **Live trading loop** (line 32127):
   - Iterates through `symbols_to_trade` which are MT5 symbol names
   - MT5 returns live symbols with suffix: `XAUUSD.m`, `EURUSD.m`, etc.
   - Bot was trying: `lgb_models["XAUUSD.m"]` → `KeyError` → `model = None`
   - Result: All models showed as unavailable → ML confidence = 0.00 → trades blocked by 0.90 threshold

3. **Why fallback didn't help enough**:
   - Previous fix: Set `effective_confidence = 0.70` when models missing
   - But the **real** models existed - they just weren't being found!
   - This fix ensures models ARE found.

## Solution Applied
**Strip the `.m`/`.ecn` suffix when looking up models** (line 32134-32136):

```python
# Before (line 32136):
if symbol in lgb_models:  # symbol = "XAUUSD.m" → KeyError

# After (line 32135-2136):
base_symbol = symbol.replace(".m", "").replace(".ecn", "")  # "XAUUSD.m" → "XAUUSD"
if base_symbol in lgb_models:  # base_symbol = "XAUUSD" ✓ Found!
```

## Files Exist on Your System
Your models are all there:
```
✓ model_lgb_XAUUSD.txt
✓ model_lgb_EURUSD.txt
✓ model_lgb_GBPUSD.txt
✓ model_lgb_USDJPY.txt
✓ model_lgb_AUDUSD.txt
✓ model_rf_XAUUSD.pkl
✓ model_rf_EURUSD.pkl
... (and corresponding .m versions + .json files for XGB)
```

## Expected Impact
1. **ML models now load correctly** → `ml_confidence > 0.00` → trades using real ML predictions
2. **Stricter threshold applies** → Min confidence = 0.90 (instead of fallback 0.60)
3. **Better trade quality** → ML ensemble voting now has actual model consensus
4. **No more "model unavailable" errors** in logs

## Supporting Changes Already Applied
From previous session:
1. **RSI soft filtering** (not hard blocker): Allows trades outside RSI 45-55 zone with penalty
2. **ML fallback confidence**: Still active for edge cases where models truly fail
3. **Relaxed min_confidence thresholds**: 0.60 when no model, 0.90 when loaded

## Testing Recommendations
1. Watch bot logs for `[MODEL] Loaded LGB model for XAUUSD` messages
2. Verify `ml_confidence` values > 0.00 in trades
3. Compare trade signals with and without ML filtering
4. Monitor that no more "Model is None" errors appear

## Code Location
- **Fix location**: [botfriday6000th.py](botfriday6000th.py#L32134-L32136)
- **Lookup code**: Lines 32127-32146 (model loading in main trading loop)
- **Feature order resolver**: Lines 8050-8070 (already handles `.m` suffix correctly)
- **Startup loading**: Lines 9375-9400 (loads models under base symbol names)
