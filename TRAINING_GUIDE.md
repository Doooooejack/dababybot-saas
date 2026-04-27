# ML Model Training Guide - Aligned with BotFriday90000th.py

## ✅ What Was Fixed

### Before:
- ❌ Training code imported from **botfriday6000th.py** (outdated)
- ❌ Feature mismatch between training and bot
- ❌ Manual path to wrong directory
- ❌ No MT5 integration for live data
- ❌ Missing SMC/FVG/Fibonacci features

### After:
- ✅ Training code imports from **botfriday90000th.py** (current bot)
- ✅ Feature extraction matches bot exactly (120+ features)
- ✅ Uses MT5 for live data collection (CSV fallback)
- ✅ Includes all advanced features: FVG, BOS, liquidity, Fibonacci
- ✅ Ensemble stacking (RF + XGB + LGB)
- ✅ Drift detection for auto-retrain alerts

---

## 🚀 How to Train Models

### Prerequisites:
1. **MetaTrader5 running** and logged into your broker
2. **Python environment** with required packages:
   ```bash
   pip install MetaTrader5 xgboost lightgbm scikit-learn shap joblib pandas numpy
   ```

### Training Steps:

1. **Run the training script:**
   ```bash
   python train_modelv8.py
   ```

2. **Training process:**
   - Loads 3000+ bars from MT5 for each symbol
   - Extracts 120+ features per candle
   - Labels data as BUY/SELL/HOLD based on future price movement
   - Balances dataset (oversamples minority classes)
   - Trains 4 models: RandomForest, XGBoost, LightGBM, Ensemble
   - Validates with TimeSeriesSplit cross-validation
   - Saves models to `./models/` directory

3. **Expected output:**
   ```
   [MT5] Loaded 3000 bars for XAUUSD.m from MT5
   [AUTO] XAUUSD: Using confluence threshold 5.0 (samples: 1247)
   [TUNE] Best RF params for XAUUSD: {'max_depth': 20, 'n_estimators': 200}
   [PERF] RandomForest accuracy for XAUUSD: 0.687
   [PERF] XGBoost accuracy for XAUUSD: 0.712
   [PERF] LightGBM accuracy for XAUUSD: 0.701
   [PERF] Stacking ensemble accuracy for XAUUSD: 0.724
   [SUCCESS] All models trained and saved for XAUUSD!
   ```

---

## 📊 Feature Alignment

### Bot (botfriday90000th.py) Features:
```python
KERAS_FEATURE_ORDER_20 = [
    # Core indicators (14)
    "atr", "rsi", "ema200", "ema50", "ema20", "ema200_dist",
    "prev_body", "prev_wick", "prev_bull", "std20", "hour", "volume",
    "pattern_score", "bullish_pattern_strength", "bearish_pattern_strength",
    
    # Candlestick patterns (8)
    "cdl_bullish_engulfing", "cdl_bearish_engulfing", "cdl_hammer", 
    "cdl_morning_star", "cdl_three_white_soldiers", "cdl_three_black_crows",
    "cdl_shooting_star", "cdl_evening_star",
    
    # Chart patterns (9)
    "head_shoulders", "double_top", "double_bottom", "triple_top", 
    "triple_bottom", "flag_pattern", "pennant_pattern", "wedge_pattern",
    "rectangle_pattern",
    
    # Advanced indicators (13)
    "adx", "parabolic_sar", "obv", "roc", "williams_r", "pivot_point",
    "breadth", "intermarket_corr", "distance_from_tp", "minutes_left_session",
    "atr_squeeze", "atr_burst", "macd", "macd_signal", "macd_hist", "macd_cross",
    
    # Multi-timeframe structure (17)
    "htf_confluence", "volume_delta", "dist_to_swing_high", "dist_to_swing_low",
    "body_vs_avg", "HH", "HL", "LH", "LL",
    "H1_HH", "H1_HL", "H1_LH", "H1_LL",
    "H4_HH", "H4_HL", "H4_LH", "H4_LL",
    "trend_alignment_score", "htf_trend_4h", "htf_trend_1h",
    
    # Session & risk (8)
    "day_of_week", "news_impact", "is_no_trade_zone", "smart_lot",
    "hedge_signal", "trend_mtf", "volume_spike", "volatility_spike",
    
    # Engineered patterns (9)
    "bullish_pattern", "bearish_pattern", "doji_pattern", "structure_trend",
    "symbol_XAUUSD", "symbol_EURUSD", "symbol_USDJPY", "symbol_GBPUSD",
    "symbol_AUDUSD",
    
    # Price action (18)
    "body", "upper_wick", "lower_wick", "close_vs_open", "close_vs_prev_close",
    "vol", "rel_vol", "body_accel", "orderbook_imbalance", "delta_vol",
    "time_since_high", "time_since_low", "bb_upper", "bb_lower", "bb_width",
    "bb_pos", "lag_ema20", "lag_rsi",
    
    # Rolling statistics (7)
    "close_mean_10", "close_std_10", "close_min_10", "close_max_10",
    "vol_mean_10", "vol_std_10", "is_high_impact_news",
    
    # Murphy's TA (14)
    "trend", "trendline_break", "ma_cross", "rsi_div", "fib_236", "fib_382",
    "fib_500", "fib_618", "fib_786", "sr_support", "sr_resistance",
    "stochastic_k", "stochastic_d", "macd_signal_line", "macd_histogram",
    "market_regime", "volume_profile_poc",
    
    # SMC Structure (9)
    "fvg_bull", "fvg_bear", "fvg_none", "displacement_strong",
    "liquidity_sweep", "order_block", "bos", "institutional_move",
    "volume_spike"
]
# Total: 120+ features
```

### Training Script Matches 100%
The training script (`train_modelv8.py`) uses the **exact same** `KERAS_FEATURE_ORDER_20` list, ensuring perfect alignment.

---

## 🎯 Model Performance Targets

### Acceptable Accuracy:
- **RandomForest:** 60-70%
- **XGBoost:** 65-75%
- **LightGBM:** 65-75%
- **Ensemble:** 70-80%

### Why Not Higher?
Trading is **probabilistic**, not deterministic. 70-80% accuracy combined with:
- **1:2 RR ratio** = profitable
- **9-filter confluence system** = high-quality entries only
- **Position sizing** = risk management

---

## 🔄 Retraining Schedule

### When to Retrain:
1. **Weekly:** Standard schedule for active trading
2. **Drift alert:** When `feature_drift_{SYMBOL}.json` shows `"drift_detected": true`
3. **Market regime change:** Major news events, volatility spikes
4. **Poor performance:** If live win rate drops below 50%

### Quick Retrain:
```bash
# Just run the script again
python train_modelv8.py
```

Models are automatically versioned with timestamps in metadata.

---

## 📁 Model Files Explained

```
models/
├── model_rf_XAUUSD.pkl          # RandomForest (scikit-learn)
├── model_xgb_XAUUSD.pkl         # XGBoost (pickled)
├── model_lgb_XAUUSD.txt         # LightGBM (booster format)
├── model_stack_XAUUSD.pkl       # Ensemble (stacking)
├── model_metrics_rf_XAUUSD.json # Performance stats
├── model_metrics_xgb_XAUUSD.json
├── model_metrics_lgb_XAUUSD.json
├── feature_drift_XAUUSD.json    # Drift monitoring
└── rf_feature_orders.json       # Feature order metadata
```

### Compatibility:
All models saved with **multiple suffix variants**:
- `XAUUSD` (base)
- `XAUUSD.m` (MT5 market watch)
- `XAUUSD.ecn` (ECN brokers)
- `XAUUSD.pro` (Pro accounts)

Bot auto-detects and loads correct variant.

---

## 🛠️ Troubleshooting

### Issue: "Not enough data"
**Solution:** Lower `TRAIN_BARS` in script or collect more history in MT5

### Issue: "MT5 initialize failed"
**Solution:** 
1. Check MT5 is running
2. Verify you're logged into your broker
3. Use CSV fallback: place CSV files in `./data/SYMBOL.csv`

### Issue: "Low accuracy (<60%)"
**Solution:**
1. Check feature quality (are indicators calculating correctly?)
2. Verify label logic (is `get_multibar_label` sensible?)
3. Increase `TRAIN_BARS` for more data
4. Check class balance (should have similar buy/sell/hold counts)

### Issue: "Import error from botfriday90000th"
**Solution:**
1. Ensure `botfriday90000th.py` is in same directory
2. Check Python path in script matches your setup
3. Verify all required functions exist in bot file

---

## 📈 Next Steps After Training

1. **Verify models loaded:**
   - Start `botfriday90000th.py`
   - Check console for: `[MODEL LOADED] XAUUSD: RandomForest (120 features)`

2. **Backtest:**
   - Use historical data to validate model performance
   - Check win rate, drawdown, RR ratio

3. **Paper trade:**
   - Run bot on demo account for 1-2 weeks
   - Monitor prediction accuracy vs actual outcomes

4. **Go live:**
   - Start with minimum lot sizes
   - Scale up gradually as confidence builds

---

## 🎓 Understanding Model Predictions

### Bot Prediction Flow:
```python
# 1. Extract features from current market data
features = extract_features(df, symbol)

# 2. Load appropriate model
model = load_model(f"models/model_rf_{symbol}.pkl")

# 3. Prepare input (normalize, align feature order)
X = prepare_model_input(features, model)

# 4. Get prediction + confidence
prediction = model.predict(X)[0]  # 'buy', 'sell', or 'hold'
confidence = model.predict_proba(X)[0].max()  # 0.0-1.0

# 5. Filter through 9-filter system
if prediction == 'buy' and confidence > 0.7 and all_9_filters_pass:
    place_trade(symbol, 'buy')
```

### Confidence Thresholds:
- **< 0.5:** Ignore (coin flip)
- **0.5-0.7:** Low confidence, reduce size
- **0.7-0.85:** Good confidence, normal size
- **> 0.85:** High confidence, consider scaling up

---

## 🎉 Success Indicators

Your training is successful when you see:
- ✅ All 5 symbols trained without errors
- ✅ Accuracy > 60% for all models
- ✅ Balanced confusion matrices (not biased to one class)
- ✅ Bot successfully loads models on startup
- ✅ Predictions align with filter system (not contradicting)

**You're ready to trade!** 🚀
