# LightGBM Feature Usage Analysis - botfriday6000th.py

## Problem Statement
LightGBM models are failing with error:
```
[LightGBM] [Fatal] The number of features in data (135) is not the same as it was in training data (193)
```

This document traces the exact code flow for feature preparation and model prediction.

---

## 1. Feature Definition Order

### Location: [Lines 7480-7525](botfriday6000th.py#L7480-L7525)

The `KERAS_FEATURE_ORDER_20` constant defines the FULL feature order used across the codebase:

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

**Issue**: This list contains approximately 135+ features, but the LightGBM models were trained with 193 features.

---

## 2. Model Loading at Startup

### Location: [Lines 8928-8980](botfriday6000th.py#L8928-L8980)

LightGBM models are loaded from disk with stored feature order:

```python
def load_lgb_model(symbol):
    model = lgb.Booster(model_file=f"model_lgb_{symbol}.txt")
    rf_data = joblib.load(f"model_rf_{symbol}.pkl")
    feature_order = rf_data["feature_order"]
    symbol_onehot_order = rf_data["symbol_onehot_order"]
    return model, feature_order, symbol_onehot_order

# Load all models at startup
rf_models = {}
rf_feature_orders = {}
rf_symbol_onehot_orders = {}
xgb_models = {}
xgb_feature_orders = {}
xgb_symbol_onehot_orders = {}
lgb_models = {}
lgb_feature_orders = {}
lgb_symbol_onehot_orders = {}

for sym in SYMBOLS:
    # ... RF loading ...
    # ... XGB loading ...
    try:
        model, feature_order, symbol_onehot_order = load_lgb_model(sym)
        lgb_models[sym] = model
        lgb_feature_orders[sym] = feature_order
        lgb_symbol_onehot_orders[sym] = symbol_onehot_order
        print(f"[MODEL] Loaded LGB model for {sym}")
    except Exception as e:
        print(f"[ERROR] Could not load LGB model for {sym}: {e}")
```

**Key Points**:
- `lgb_models[sym]` = the Booster object loaded from `model_lgb_{symbol}.txt`
- `lgb_feature_orders[sym]` = feature order list from the RF model's pickle file (193 features)
- `lgb_symbol_onehot_orders[sym]` = one-hot encoding order from RF model's pickle file

---

## 3. Main Trading Loop: Feature Preparation

### Location: [Lines 8520-8570](botfriday6000th.py#L8520-L8570)

This is where the ACTUAL PREDICTION HAPPENS in the live trading loop:

```python
# Extract features
features = get_features_fixed(df)  # Returns a dict with ~135 features

# --- Prepare feature vector for the loaded model ---
try:
    # Prepare feature vector
    # ⚠️ CRITICAL: Using rf_feature_orders[symbol] which has 193 features
    feature_vector = [features.get(k, 0.0) for k in rf_feature_orders[symbol]]
    
    # Add symbol one-hot encoding
    symbol_onehot = [int(symbol.startswith(s)) for s in rf_symbol_onehot_orders[symbol]]
    feature_vector += symbol_onehot
    
    # Convert to 2D array (1 sample, N features)
    X = np.array([feature_vector])  # Shape: (1, 193+5) = (1, 198) approx
    
    # RandomForest prediction
    rf_pred = rf_models[symbol].predict(X)
    # ... RF confidence calculation ...
    
    # XGBoost prediction
    xgb_X = xgb.DMatrix(X)
    xgb_pred = xgb_models[symbol].predict(xgb_X)
    # ... XGB confidence calculation ...
    
    # LightGBM prediction
    lgb_pred = lgb_models[symbol].predict(X)  # ⚠️ THIS LINE FAILS
    lgb_signal = label_map.get(int(np.round(lgb_pred[0])), "hold")
    lgb_proba = lgb_models[symbol].predict(X, raw_score=False)
    # ... LGB confidence calculation ...
    
except Exception as e:
    print(f"[SIGNAL] Model prediction error: {e}")
```

**The Problem**:
1. `rf_feature_orders[symbol]` contains 193 features (from training data)
2. `get_features_fixed(df)` only returns ~135 features
3. Missing 58 features are filled with zeros via `.get(k, 0.0)`
4. **BUT**: The feature ORDER matters! The 135 features present may NOT be in the right order for the LightGBM model

**Dimensions**:
- Input `X` shape: (1, 198) approximately (193 base + ~5 symbol one-hot)
- But only ~135 of those features are actually calculated
- The remaining ~63 are zeros (missing features)

---

## 4. Feature Preparation/Reshaping Function

### Location: [Lines 7527-7610](botfriday6000th.py#L7527-L7610)

A `prepare_model_input()` function exists with padding/truncation logic:

```python
def prepare_model_input(features, model=None, symbol=None, feature_order=None):
    """Return a 2D numpy array suitable for model.predict from various `features` formats.

    - `features` may be a dict, a list (of dicts or lists), or a flattened vector.
    - `feature_order` if provided overrides other order sources.
    - If `model` has `feature_names_in_` or `feature_order` attribute, it will be used.
    - If feature count mismatch occurs, pads with zeros or truncates to match model expectations.
    """
    import numpy as _np

    # Normalize to a dict
    fdict = {}
    if isinstance(features, list):
        if len(features) == 0:
            fdict = {}
        else:
            first = features[0]
            if isinstance(first, dict):
                fdict = first
            # ... handle various list formats ...
    elif isinstance(features, dict):
        fdict = features
    else:
        try:
            fdict = flatten_features(features) if 'flatten_features' in globals() else {}
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

    # Build feature vector
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

**Important**: This function is NOT being used in the main trading loop (lines 8520-8570). Instead, manual feature vector construction is used.

---

## 5. Summary: The Feature Mismatch Chain

| Step | Code Location | Details |
|------|---------------|---------|
| **1. Feature Definition** | Line 7480+ | `KERAS_FEATURE_ORDER_20` = ~135 features |
| **2. Model Load** | Line 8928-8980 | LightGBM expects 193 features (from training) |
| **3. Feature Extraction** | Line 8519 | `get_features_fixed(df)` returns ~135 actual features |
| **4. Vector Construction** | Line 8523 | Use `rf_feature_orders[symbol]` (193 features) |
| **5. Missing Features** | Line 8524 | `.get(k, 0.0)` fills missing features with 0 |
| **6. Prediction Call** | Line 8546 | `lgb_models[symbol].predict(X)` fails |

---

## 6. Root Cause Analysis

### Why is it failing?

1. **Training Data**: LightGBM models were trained with 193 features from `rf_feature_orders[symbol]`
2. **Runtime Data**: `get_features_fixed(df)` only computes ~135 features
3. **Feature Order Mismatch**: The 193-element `rf_feature_orders` contains features NOT in `KERAS_FEATURE_ORDER_20`
4. **Zero-Padding**: Missing features are filled with zeros, but this doesn't solve the order problem

### The 135 vs 193 Gap

- `KERAS_FEATURE_ORDER_20` has ~135 features
- `rf_feature_orders[symbol]` (loaded from pickle) has 193 features
- **58 missing features** are not being computed by `get_features_fixed(df)`

---

## 7. The Solution

### Option A: Use the `prepare_model_input()` Function
Instead of manual feature vector construction, use the built-in padding function:

**Current code (BROKEN)**:
```python
feature_vector = [features.get(k, 0.0) for k in rf_feature_orders[symbol]]
X = np.array([feature_vector])
lgb_pred = lgb_models[symbol].predict(X)  # FAILS: 135 features vs 193 expected
```

**Fixed code (OPTION A)**:
```python
X = prepare_model_input(
    features, 
    model=lgb_models[symbol], 
    feature_order=lgb_feature_orders[symbol]
)
lgb_pred = lgb_models[symbol].predict(X)  # WORKS: auto-pads to 193
```

### Option B: Match Feature Extraction to Training
Ensure `get_features_fixed(df)` computes ALL 193 features that were used during training.

### Option C: Retrain Models with Correct Feature Set
Retrain LightGBM models using ONLY the 135 features in `KERAS_FEATURE_ORDER_20`.

---

## 8. Key Code Sections for Debugging

| Section | What to Check |
|---------|---------------|
| **Feature Extraction** | [Lines 8519](botfriday6000th.py#L8519) - Does `get_features_fixed()` return 193 features? |
| **Model Loading** | [Lines 8970-8976](botfriday6000th.py#L8970-L8976) - What does `lgb_feature_orders[symbol]` contain? |
| **Feature Vector Build** | [Lines 8523-8525](botfriday6000th.py#L8523-L8525) - Is order matching model expectations? |
| **Prediction Call** | [Line 8546](botfriday6000th.py#L8546) - This is where the error occurs |
| **Feature Padding Logic** | [Lines 7590-7610](botfriday6000th.py#L7590-L7610) - Use this to auto-pad/truncate |

---

## 9. Debug Commands

To check model feature requirements:
```python
# In Python terminal:
import lightgbm as lgb
model = lgb.Booster(model_file='model_lgb_EURUSD.txt')
print(f"Expected features: {model.num_feature()}")
print(f"Feature names: {model.feature_names_[:20]}")
```

To check what `get_features_fixed()` returns:
```python
features = get_features_fixed(df)
print(f"Actual features: {len(features)}")
print(f"Feature keys: {sorted(features.keys())}")
```
