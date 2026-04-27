# Exact Code Sections - LightGBM Feature Usage in botfriday6000th.py

## 1. FEATURE EXTRACTION (Line 8519)

**File**: botfriday6000th.py, **Lines**: 8519-8527

```python
# Extract features
features = get_features_fixed(df)

# --- Prepare feature vector for the loaded model ---
try:
    # Prepare feature vector
    feature_vector = [features.get(k, 0.0) for k in rf_feature_orders[symbol]]
    symbol_onehot = [int(symbol.startswith(s)) for s in rf_symbol_onehot_orders[symbol]]
```

**What happens**:
- `features` = dict with ~135 keys and values
- `rf_feature_orders[symbol]` = list with 193 feature names
- **Result**: `feature_vector` has 193 elements
  - Elements 1-135: Real values from `features`
  - Elements 136-193: 0.0 (default value for missing keys)

**Problem**: 58 features are missing and filled with zeros.

---

## 2. FEATURE VECTOR CONSTRUCTION (Lines 8523-8527)

**File**: botfriday6000th.py, **Lines**: 8523-8527

```python
feature_vector = [features.get(k, 0.0) for k in rf_feature_orders[symbol]]
symbol_onehot = [int(symbol.startswith(s)) for s in rf_symbol_onehot_orders[symbol]]
feature_vector += symbol_onehot
X = np.array([feature_vector])
```

**Array Construction**:
1. `feature_vector` = 193 elements (from rf_feature_orders)
2. `symbol_onehot` = 5 elements (one-hot encoding)
3. `feature_vector += symbol_onehot` → now 198 elements total
4. `X = np.array([feature_vector])` → shape becomes (1, 198)

**Dimensions**:
- Input shape: (1, 198)
- Expected by LightGBM: 193 features
- **Mismatch**: ✗ May cause the 135 vs 193 error

---

## 3. LIGHTGBM PREDICTION (Line 8546)

**File**: botfriday6000th.py, **Line**: 8546-8548

```python
# LightGBM prediction
lgb_pred = lgb_models[symbol].predict(X)
lgb_signal = label_map.get(int(np.round(lgb_pred[0])), "hold")
lgb_proba = lgb_models[symbol].predict(X, raw_score=False)
```

**Error occurs here**:
- Line 8546: `lgb_models[symbol].predict(X)`
- X is shape (1, 198) but model expects 193
- OR X has 193 but wrong feature order

**Error message**:
```
[LightGBM] [Fatal] The number of features in data (135) is not the same as it was in training data (193)
```

This error suggests the model is receiving 135 features, not 198.

---

## 4. MODEL LOADING (Lines 8928-8980)

**File**: botfriday6000th.py, **Lines**: 8928-8980

```python
def load_lgb_model(symbol):
    model = lgb.Booster(model_file=f"model_lgb_{symbol}.txt")
    rf_data = joblib.load(f"model_rf_{symbol}.pkl")
    feature_order = rf_data["feature_order"]
    symbol_onehot_order = rf_data["symbol_onehot_order"]
    return model, feature_order, symbol_onehot_order

# Load all models at startup
lgb_models = {}
lgb_feature_orders = {}
lgb_symbol_onehot_orders = {}

for sym in SYMBOLS:
    try:
        model, feature_order, symbol_onehot_order = load_lgb_model(sym)
        lgb_models[sym] = model
        lgb_feature_orders[sym] = feature_order
        lgb_symbol_onehot_orders[sym] = symbol_onehot_order
        print(f"[MODEL] Loaded LGB model for {sym}")
    except Exception as e:
        print(f"[ERROR] Could not load LGB model for {sym}: {e}")
```

**What gets stored**:
- `lgb_models[sym]` = Booster object from `model_lgb_{sym}.txt`
  - Contains: 193 features worth of decision trees
  - Has metadata about feature count and names
- `lgb_feature_orders[sym]` = Feature order list (193 items)
  - Loaded from: `model_rf_{sym}.pkl`
  - Used at prediction time (Line 8523)
- `lgb_symbol_onehot_orders[sym]` = Symbol order list (5 items)
  - Loaded from: `model_rf_{sym}.pkl`
  - Used at prediction time (Line 8524)

**Key insight**: The feature order comes from the RANDOM FOREST pickle, not the LightGBM model file!

---

## 5. KERAS FEATURE ORDER DEFINITION (Lines 7480-7525)

**File**: botfriday6000th.py, **Lines**: 7480-7525

```python
KERAS_FEATURE_ORDER_20 = list(dict.fromkeys([
    "atr", "rsi", "ema200", "ema50", "ema20", "ema200_dist",
    "prev_body", "prev_wick", "prev_bull", "std20", "hour", "volume",
    "pattern_score", "bullish_pattern_strength", "bearish_pattern_strength",
    # --- Candlestick patterns ---
    "cdl_bullish_engulfing", "cdl_bearish_engulfing", "cdl_hammer", "cdl_morning_star",
    "cdl_three_white_soldiers", "cdl_three_black_crows", "cdl_shooting_star", "cdl_evening_star",
    # --- Western chart patterns and classic indicators ---
    "head_shoulders", "double_top", "double_bottom", "triple_top", "triple_bottom",
    "flag_pattern", "pennant_pattern", "wedge_pattern", "rectangle_pattern",
    "adx", "parabolic_sar", "obv", "roc", "williams_r", "pivot_point", "breadth", "intermarket_corr",
    "distance_from_tp", "minutes_left_session", "atr_squeeze", "atr_burst",
    "macd", "macd_signal", "macd_hist", "macd_cross",
    "htf_confluence", "volume_delta",
    "dist_to_swing_high", "dist_to_swing_low", "body_vs_avg",
    "HH", "HL", "LH", "LL",
    "H1_HH", "H1_HL", "H1_LH", "H1_LL",
    "H4_HH", "H4_HL", "H4_LH", "H4_LL",
    "trend_alignment_score",
    # --- NEW HTF trend features ---
    "htf_trend_4h", "htf_trend_1h",
    # --- Additional features for robustness ---
    "day_of_week", "news_impact", "is_no_trade_zone", "smart_lot", "hedge_signal", "trend_mtf",
    "volume_spike", "volatility_spike",
    # --- Advanced engineered features (appended in feature_vector) ---
    "bullish_pattern", "bearish_pattern", "doji_pattern", "structure_trend",
    # Symbol one-hot: ["XAUUSD", "EURUSD", "USDJPY", "GBPUSD", "AUDUSD"]
    "symbol_XAUUSD", "symbol_EURUSD", "symbol_USDJPY", "symbol_GBPUSD", "symbol_AUDUSD",
    # Price action and orderbook
    "body", "upper_wick", "lower_wick", "close_vs_open", "close_vs_prev_close", "vol", "rel_vol",
    "body_accel", "orderbook_imbalance", "delta_vol",
    "time_since_high", "time_since_low",
    "bb_upper", "bb_lower", "bb_width", "bb_pos",
    "lag_ema20", "lag_rsi",
    "close_mean_10", "close_std_10", "close_min_10", "close_max_10",
    "vol_mean_10", "vol_std_10",
    "is_high_impact_news",
    # --- NEW: Add advanced TA features from Murphy's book and bot enhancements ---
    "trend", "trendline_break", "ma_cross", "rsi_div", "fib_236", "fib_382", "fib_500", "fib_618", "fib_786",
    "sr_support", "sr_resistance", "stochastic_k", "stochastic_d", "macd_signal_line", "macd_histogram", "market_regime", "volume_profile_poc",
    # --- NEW STRUCTURE FEATURES ---
    "fvg_bull", "fvg_bear", "fvg_none",
    "displacement_strong", "liquidity_sweep", "order_block", "bos", "institutional_move", "volume_spike"
]))
```

**Count**: Approximately 135 features

**This list**:
- ✓ Used when training models
- ✓ Should match the 135 features returned by `get_features_fixed(df)`
- ✗ Does NOT match the 193 features in `rf_feature_orders[symbol]`

**Question**: Where do the extra 58 features come from?

---

## 6. FEATURE PREPARATION FUNCTION (Lines 7527-7610)

**File**: botfriday6000th.py, **Lines**: 7527-7610

```python
def prepare_model_input(features, model=None, symbol=None, feature_order=None):
    """Return a 2D numpy array suitable for model.predict from various `features` formats.

    - `features` may be a dict, a list (of dicts or lists), or a flattened vector.
    - `feature_order` if provided overrides other order sources.
    - If `model` has `feature_names_in_` or `feature_order` attribute, it will be used.
    - If feature count mismatch occurs, pads with zeros or truncates to match model expectations.
    """
    import numpy as _np

    # Normalize to a dict (use first element if list of dicts)
    fdict = {}
    if isinstance(features, list):
        if len(features) == 0:
            fdict = {}
        else:
            first = features[0]
            if isinstance(first, dict):
                fdict = first
            elif isinstance(first, (list, tuple, _np.ndarray)):
                # Already a numeric vector or list of vectors
                try:
                    arr = _np.array(features)
                    if arr.ndim == 1:
                        return arr.reshape(1, -1)
                    return arr
                except Exception:
                    fdict = {}
            else:
                fdict = {}
    elif isinstance(features, dict):
        fdict = features
    else:
        # Try to flatten via provided helper if available
        try:
            fdict = flatten_features(features) if 'flatten_features' in globals() else {}
            if not isinstance(fdict, dict):
                fdict = {}
        except Exception:
            fdict = {}

    # Determine feature order
    order = None
    if feature_order:
        order = feature_order
    elif model is not None:
        if hasattr(model, 'feature_names_in_'):
            try:
                order = list(model.feature_names_in_)
            except Exception:
                order = None
        elif hasattr(model, 'feature_order'):
            try:
                order = list(model.feature_order)
            except Exception:
                order = None
    if order is None:
        order = KERAS_FEATURE_ORDER_20

    vec = []
    for k in order:
        v = fdict.get(k, 0.0)
        try:
            vec.append(float(v))
        except Exception:
            vec.append(0.0)
    
    result = _np.array([vec])
    
    # ✅ FEATURE MISMATCH HANDLING
    # If the model expects a different number of features, handle gracefully
    try:
        model_expected = None
        if hasattr(model, 'n_features_in_'):
            model_expected = model.n_features_in_
        elif hasattr(model, 'num_feature'):
            try:
                model_expected = model.num_feature()
            except:
                model_expected = None
        
        if model_expected is not None and result.shape[1] != model_expected:
            input_features = result.shape[1]
            
            # If we have fewer features than expected, pad with zeros
            if input_features < model_expected:
                padding = _np.zeros((result.shape[0], model_expected - input_features))
                result = _np.hstack([result, padding])
                print(f"[FEATURE PAD] Padded from {input_features} to {model_expected} features (zero-padding)")
            
            # If we have more features than expected, truncate
            elif input_features > model_expected:
                result = result[:, :model_expected]
                print(f"[FEATURE TRUNCATE] Truncated from {input_features} to {model_expected} features")
    except Exception as e:
        print(f"[FEATURE CHECK] Could not verify model feature count: {e}")
    
    return result
```

**This function**:
- ✓ Accepts features dict
- ✓ Auto-detects model expectations via `model.num_feature()` for LightGBM
- ✓ Automatically pads missing features with zeros
- ✓ Automatically truncates extra features
- ✗ **NOT USED** in the main trading loop (lines 8520-8570)

**Why it exists but isn't used**:
- Manual feature vector construction at line 8523 bypasses this function
- This is likely the root cause of the feature mismatch!

---

## 7. ERROR LOCATION & CONTEXT (Lines 8540-8570)

**File**: botfriday6000th.py, **Lines**: 8540-8570

```python
        # LightGBM prediction
        lgb_pred = lgb_models[symbol].predict(X)  # ← ERROR OCCURS HERE!
        lgb_signal = label_map.get(int(np.round(lgb_pred[0])), "hold")
        lgb_proba = lgb_models[symbol].predict(X, raw_score=False)
        if isinstance(lgb_proba, np.ndarray) and lgb_proba.ndim == 2:
            lgb_confidence = float(np.max(lgb_proba[0]))
        else:
            lgb_confidence = float(np.max(lgb_proba))

        # Example: Use majority vote or pick the most confident model
        signals = [rf_signal, xgb_signal, lgb_signal]
        confidences = [rf_confidence, xgb_confidence, lgb_confidence]
        # Majority vote
        from collections import Counter
        vote = Counter(signals).most_common(1)[0][0]
        # Or pick the signal with highest confidence
        best_idx = int(np.argmax(confidences))
        ml_signal = signals[best_idx]
        confidence = confidences[best_idx]
        features["ml_signal"] = ml_signal  # For Murphy entry logic

    except Exception as e:
        print(f"[SIGNAL] Model prediction error: {e}")
```

**The exception is caught** at line 8567, so the bot doesn't crash, but:
- ✗ No signal is generated
- ✗ ML signal is not computed
- ✗ Trade decision falls back to other logic

**Error message captured**:
```
[SIGNAL] Model prediction error: [LightGBM] [Fatal] The number of features in data (135) is not the same as it was in training data (193)
```

---

## 8. COMPARISON: RandomForest vs LightGBM

**File**: botfriday6000th.py, **Lines**: 8530-8548

```python
# RandomForest prediction (Works)
rf_pred = rf_models[symbol].predict(X)
rf_proba = safe_predict_proba(rf_models[symbol], X, model_type="sklearn") if 'safe_predict_proba' in globals() else (rf_models[symbol].predict_proba(X) if hasattr(rf_models[symbol], 'predict_proba') else np.array([0.33, 0.33, 0.33]))
rf_confidence = float(np.max(rf_proba[0]) if rf_proba.ndim > 1 else np.max(rf_proba))

# XGBoost prediction (Works)
xgb_X = xgb.DMatrix(X)
xgb_pred = xgb_models[symbol].predict(xgb_X)
xgb_signal = label_map.get(int(np.round(xgb_pred[0])), "hold")
xgb_proba = xgb_models[symbol].predict(xgb_X, output_margin=False)

# LightGBM prediction (FAILS)
lgb_pred = lgb_models[symbol].predict(X)
lgb_signal = label_map.get(int(np.round(lgb_pred[0])), "hold")
lgb_proba = lgb_models[symbol].predict(X, raw_score=False)
```

**Why RF and XGB work but LGB doesn't**:
- RF: Tree-based, tolerates mismatched features better
- XGB: Wrapped in DMatrix, may handle feature count differently
- LGB: Strict about feature count and order, requires exact match

---

## Summary Table

| Aspect | Details |
|--------|---------|
| **Feature Definition** | KERAS_FEATURE_ORDER_20 (~135 features) |
| **Feature Extraction** | get_features_fixed(df) returns dict with ~135 keys |
| **Model Training** | Used 193 features from rf_feature_orders[symbol] |
| **Prediction Input** | feature_vector constructed from rf_feature_orders (193) |
| **Missing Features** | ~58 filled with 0.0 |
| **Input Shape** | X = (1, 198) with one-hot encoding included |
| **Expected Shape** | LightGBM expects 193 features |
| **Error** | Feature count mismatch |
| **Solution** | Use prepare_model_input() function instead of manual construction |
| **Fix Location** | Lines 8523-8527 |
