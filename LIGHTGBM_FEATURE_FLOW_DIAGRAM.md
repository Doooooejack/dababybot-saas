# LightGBM Feature Mismatch - Visual Flow Diagram

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     LIVE TRADING LOOP (Line 8519+)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  features = get_features_fixed(df)            │
        │  Returns: dict with ~135 features             │
        │  Keys: "atr", "rsi", "ema20", ... etc         │
        │  Missing: 58 features not computed            │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  feature_vector = [features.get(k, 0.0)       │
        │     for k in rf_feature_orders[symbol]]       │
        │  ─────────────────────────────────────────    │
        │  rf_feature_orders[symbol] contains:          │
        │  - 193 features (from training)               │
        │  - All 135 features from get_features_fixed() │
        │  - 58 additional features (get 0.0)           │
        │  ─────────────────────────────────────────    │
        │  Missing features filled with: 0.0            │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  symbol_onehot = [int(symbol.startswith(s))   │
        │     for s in rf_symbol_onehot_orders[symbol]] │
        │  Returns: 5 one-hot encoded features          │
        │  [XAUUSD, EURUSD, USDJPY, GBPUSD, AUDUSD]    │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  feature_vector += symbol_onehot              │
        │  Total length: 193 + 5 = 198                  │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  X = np.array([feature_vector])               │
        │  Shape: (1, 198)                              │
        │  - First 193 columns from rf_feature_orders   │
        │  - Last 5 columns are one-hot encoding        │
        │  ─────────────────────────────────────────    │
        │  ⚠️  PROBLEM: Only ~140 of 198 are non-zero  │
        │      ~58 features are 0.0 (missing)           │
        │      Order may not match training data!       │
        └───────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
        ┌──────────────┐  ┌──────────────┐  ┌────────────────┐
        │ RF Predict   │  │ XGB Predict  │  │ LGB Predict    │
        │ WORKS OK ✓   │  │ WORKS OK ✓   │  │ FAILS ✗        │
        │              │  │              │  │                │
        │ Shape: 198   │  │ Shape: 198   │  │ Expected: 193  │
        │              │  │              │  │ Got: 135-198?  │
        └──────────────┘  └──────────────┘  └────────────────┘
                                                    │
                                                    ▼
                        ┌───────────────────────────────────────┐
                        │ [LightGBM] [Fatal]                    │
                        │ The number of features in data        │
                        │ (135) is not the same as it was       │
                        │ in training data (193)                │
                        └───────────────────────────────────────┘
```

---

## Feature Order Source Mismatch

```
┌──────────────────────────────────────────────────────────────┐
│              WHAT THE CODE IS TRYING TO DO                   │
└──────────────────────────────────────────────────────────────┘

KERAS_FEATURE_ORDER_20          rf_feature_orders[symbol]
(Line 7480+)                     (Loaded from .pkl, Line 8931)
───────────────────             ──────────────────────────────
~135 features                    193 features
                                 
atr                              atr
rsi                              rsi
ema200                           ema200
... (130 more)                   ... (190 more)
                                 
These ~135 are                   These 193 MUST be used for
DEFINED but not all              LightGBM because the model
are computed by                  was trained on this exact
get_features_fixed()!            order!


┌──────────────────────────────────────────────────────────────┐
│                    THE FLOW BREAKDOWN                         │
└──────────────────────────────────────────────────────────────┘

At Line 8523:
────────────
feature_vector = [features.get(k, 0.0) for k in rf_feature_orders[symbol]]
                  └─ features dict       └─────────────────────────────────
                     (has ~135 keys)          THIS LIST HAS 193 KEYS!

When iterating through 193 keys:
- Keys 1-135: Found in features dict → use actual value
- Keys 136-193: NOT in features dict → use 0.0 (zero-fill)

Result:
- Vector has 193 elements
- ~135 have real data
- ~58 are zeros
- ORDER might be mismatched!


┌──────────────────────────────────────────────────────────────┐
│              WHY RANDOM FOREST WORKS BUT LIGHTGBM FAILS      │
└──────────────────────────────────────────────────────────────┘

Random Forest:
├─ Training: Learned feature importance from 193 features
├─ But RF doesn't REQUIRE exact feature order or count
├─ It just uses whatever features it's given
└─ Works with zero-padding! ✓

LightGBM Booster:
├─ Training: Built decision trees expecting EXACTLY 193 features
├─ REQUIRES exact feature order and count
├─ Each tree node references feature by INDEX
├─ Feature #42 MUST be the right feature!
├─ If order is wrong → predictions are garbage
└─ Fails with zero-padding at wrong indices! ✗

XGBoost:
├─ Similar to LightGBM
├─ Should work if features are in right order
├─ May silently give wrong predictions if order is wrong
└─ (Unclear why it "works" here - may also be broken!)
```

---

## The Exact Error Location

```
Line 8546: lgb_pred = lgb_models[symbol].predict(X)
           
Error occurs because:
├─ X shape is correct (1, 198) or (1, 193) 
├─ BUT feature order might not match training
└─ LightGBM internally gets confused about which 
   feature goes where

Timeline:
─────────
1. Model loaded with 193 feature count stored
2. At prediction time, array comes in
3. LightGBM checks: "Is this 193 features?"
4. If input is 135 → ERROR (mismatch)
5. If input is 193 but wrong order → SILENT ERROR
   (predictions are wrong, but no exception)
```

---

## Fix Strategy Comparison

```
FIX OPTION A: Use the padding function
────────────────────────────────────────
Before (BROKEN):
    feature_vector = [features.get(k, 0.0) for k in rf_feature_orders[symbol]]
    X = np.array([feature_vector])
    lgb_pred = lgb_models[symbol].predict(X)  # FAILS

After (FIXED):
    X = prepare_model_input(
        features, 
        model=lgb_models[symbol],
        feature_order=lgb_feature_orders[symbol]
    )
    lgb_pred = lgb_models[symbol].predict(X)  # WORKS

Benefits:
✓ Auto-detects model expectations
✓ Pads/truncates as needed
✓ Handles feature order correctly
✓ Minimal code change

Location to change: Lines 8523-8525


FIX OPTION B: Ensure all 193 features are computed
────────────────────────────────────────────────────
Check get_features_fixed() function:
- Does it compute all 193 features?
- Or only the 135 in KERAS_FEATURE_ORDER_20?

If it computes only 135:
→ Extend get_features_fixed() to compute missing 58

Benefits:
✓ No zero-padding needed
✓ All real data used
✓ Better model predictions
✗ Major refactor
✗ Must identify which 58 are missing

Location to investigate: get_features_fixed() function


FIX OPTION C: Retrain models on correct features
──────────────────────────────────────────────────
Train LightGBM with ONLY the 135 features in:
- KERAS_FEATURE_ORDER_20
- As computed by get_features_fixed()

Benefits:
✓ Simpler model
✓ No zero-padding
✓ Faster inference
✗ Need training data
✗ Potential accuracy loss

Approach:
1. Identify exactly which 193 features used in training
2. Determine which are missing from current codebase
3. Either:
   a) Remove unused features from model training
   b) OR add missing feature computations

Location: Retraining pipeline (not in this file)
```

---

## Key Variables and Their Meanings

```python
features  = dict, keys = feature names, values = feature values
            Only ~135 keys present
            Example: {"atr": 12.5, "rsi": 65.0, ...}

rf_feature_orders[symbol]  = list of 193 feature names (from model training)
                             Used as the ORDER to build the feature vector
                             Example: ["atr", "rsi", ..., "unknown_feature_193"]

rf_symbol_onehot_orders[symbol]  = list of 5 symbol names
                                   Example: ["XAUUSD", "EURUSD", "USDJPY", "GBPUSD", "AUDUSD"]

feature_vector = list built by iterating through rf_feature_orders[symbol]
                 Length: 193
                 Values: features.get(key, 0.0)  ← 0.0 fills missing features

X = numpy array of shape (1, 193) or (1, 198)
    Used as input to all three models

lgb_models[symbol] = lgb.Booster object
                     Trained on 193 features
                     Expects exactly 193 features in predict() call
```

---

## Debug Checklist

```
☐ Check model was loaded correctly:
  lgb_models[symbol]
  
☐ Check model's feature count:
  lgb_models[symbol].num_feature() == 193?
  
☐ Check feature_vector length:
  len(feature_vector) == 193?
  
☐ Check feature names match:
  Do rf_feature_orders[symbol] match model.feature_names?
  
☐ Check which features are missing:
  for k in rf_feature_orders[symbol]:
      if k not in features:
          print(f"Missing: {k}")
  
☐ Check feature value distribution:
  How many zeros in feature_vector?
  This reveals how many features are missing
  
☐ Check order consistency:
  Does feature #42 in rf_feature_orders match
  what the model thinks feature #42 is?
```
