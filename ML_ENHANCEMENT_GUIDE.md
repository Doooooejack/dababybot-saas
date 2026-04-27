# ML Enhancement Strategy: From Confirmer to Decision Driver

## Current State: ML as a Passive Tweaker

```python
# Current usage in compute_unified_decision()
ml_base = context.ml_confidence        # 0.0-1.0 from model
# Apply session modifiers
ml_base = max(0.0, min(1.0, ml_base + session_conf_mod))
# Apply filter boosts
ml_base = min(1.0, ml_base + entry_tf_boost)
# Result: ML = 5-15% of final decision, 85-95% = hard filters
```

**Problem**: 
- ML score rarely breaks a tie between competing filters
- Model learns generic patterns but not current market regimes
- No feedback loop: model doesn't know which trades were actually winners

---

## Target State: ML as Primary Driver (65% of decision)

```python
# New workflow:
ml_score = run_ml_model(features)           # 0-100
feature_score = analyze_geometry(context)    # 0-100
final_score = 0.65 * ml_score + 0.35 * feature_score

# Final decision REQUIRES minimum score, not filter passing
if final_score < 60:
    SKIP (even if all heuristics say yes)
elif final_score < 75:
    SMALL position
elif final_score < 85:
    STANDARD position
else:
    AGGRESSIVE position
```

---

## Implementation Guide

### Part 1: Extract ML Scoring into Standalone Module

**File**: `ml_decision_engine.py` (NEW)

```python
import joblib
import numpy as np
from typing import Tuple, Dict

class MLDecisionEngine:
    """
    ML-centric trade quality assessment.
    Trained on: BOS patterns, FVG quality, volume profiles, historical outcomes.
    """
    
    def __init__(self, model_path: str):
        """Load pre-trained model (autoencoder or classifier)."""
        try:
            self.model = joblib.load(model_path)
            self.is_available = True
        except Exception as e:
            print(f"[WARNING] ML model failed to load: {e}")
            self.model = None
            self.is_available = False
    
    def extract_features(self, context) -> np.ndarray:
        """
        Convert TradeDecisionContext into ML feature vector.
        
        Features (35 dimensions):
        - Pattern features (10): BOS type, FVG quality, impulse body ratio, etc.
        - Volume features (5): vol spike, profile shape, displacement, etc.
        - Regime features (5): trend strength, volatility, session, etc.
        - Price action (10): recent candle shapes, pullback %, structure proximity
        - Confluence (5): # of overlapping signals, strength of overlap
        """
        features = []
        
        # === PATTERN FEATURES (10) ===
        fvg = context.fvg_analysis.get('entry_zone', {})
        bos = context.fvg_analysis.get('bos')
        
        features.extend([
            1.0 if bos == context.signal else 0.0,  # BOS confirmed
            fvg.get('quality_score', 0) / 100,      # FVG quality (0-100) → 0-1
            self._impulse_body_ratio(context),      # Last candle body %
            self._recent_high_proximity(context),   # Distance to recent high (%)
            self._recent_low_proximity(context),    # Distance to recent low (%)
            1.0 if context.fvg_analysis.get('in_zone') else 0.0,  # In FVG zone
            len(context.supporting_filters) / 7,    # # supporting filters
            self._pullback_depth(context),          # Pullback % of impulse
            1.0 if context.features.get('mean_reversion_disabled') else 0.0,
            context.ml_confidence,                  # Raw ML score input
        ])
        
        # === VOLUME FEATURES (5) ===
        volume_analysis = context.volume_analysis
        features.extend([
            volume_analysis.get('strong', 0.0),     # Strong volume (0-1)
            context.features.get('volume', 0) / (context.features.get('volume_avg_20', 1) + 1e-6),
            context.features.get('volume_sma_ratio', 1.0),
            1.0 if volume_analysis.get('spike_detected') else 0.0,
            1.0 if context.features.get('displacement_detected') else 0.0,
        ])
        
        # === REGIME FEATURES (5) ===
        regime = context.regime_analysis
        features.extend([
            regime.get('trend_strength', 0.5),     # 0-1
            regime.get('volatility', 0.5),         # 0-1
            1.0 if regime.get('is_trending') else 0.0,
            1.0 if context.features.get('session') == 'london_open' else 0.0,
            1.0 if context.features.get('session') == 'ny_open' else 0.0,
        ])
        
        # === PRICE ACTION (10) ===
        df = context.df
        last = df.iloc[-1] if len(df) > 0 else None
        prev = df.iloc[-2] if len(df) > 1 else None
        
        features.extend([
            self._recent_candle_body_ratio(last),
            self._recent_candle_wick_ratio(last),
            self._candle_direction(last),           # 1 = bullish, -1 = bearish
            self._candle_to_prev_ratio(last, prev),
            context.risk_analysis.get('ratio', 2.0) / 3.0,  # R:R (capped at 3:1)
            self._entry_distance_from_extreme(context),
            self._pullback_phase_detection(context),
            1.0 if self._is_impulse_confirmed(context) else 0.0,
            self._recent_low_proximity(context),
            self._recent_high_proximity(context),
        ])
        
        # === CONFLUENCE (5) ===
        n_supporting = len(context.supporting_filters)
        features.extend([
            n_supporting / 7,                       # % of possible supporting factors
            1.0 if n_supporting >= 5 else 0.0,     # High confluence binary
            1.0 if context.htf_analysis.get('aligned') else 0.0,
            1.0 if context.momentum_analysis.get('strong') else 0.0,
            context.trade_quality_score / 100 if hasattr(context, 'trade_quality_score') else 0.5,
        ])
        
        return np.array(features, dtype=np.float32).reshape(1, -1)
    
    def score_setup(self, context) -> Tuple[float, Dict]:
        """
        Score this trade setup using ML model.
        
        Returns:
            (score: 0-100, info: dict with model insights)
        """
        if not self.is_available:
            return 50.0, {'reason': 'Model unavailable, default score'}
        
        try:
            features = self.extract_features(context)
            
            # If autoencoder: reconstruction error is inverse quality score
            if hasattr(self.model, 'predict'):
                reconstruction = self.model.predict(features, verbose=0)
                reconstruction_error = np.mean((features - reconstruction) ** 2)
                # Error 0.001 → 99/100, Error 0.05 → 0/100
                ml_score = max(0, 100 - reconstruction_error * 2000)
            
            # If classifier: use confidence/probability
            elif hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(features)
                ml_score = max(proba[0]) * 100
            
            # Fallback: average prediction
            else:
                prediction = self.model.predict(features)
                ml_score = float(prediction[0]) * 100 if isinstance(prediction[0], (int, float)) else 50
            
            ml_score = max(0, min(100, ml_score))
            
            info = {
                'model_type': 'autoencoder' if hasattr(self.model, 'predict') else 'classifier',
                'score': ml_score,
                'feature_dim': features.shape[1],
                'confidence_level': 'high' if ml_score > 75 else ('medium' if ml_score > 50 else 'low'),
            }
            
            return ml_score, info
        
        except Exception as e:
            print(f"[ERROR] ML scoring failed: {e}")
            return 50.0, {'reason': f'Scoring error: {e}', 'error': True}
    
    # === HELPER METHODS ===
    
    def _impulse_body_ratio(self, context) -> float:
        """Last candle body as % of range."""
        df = context.df
        if len(df) < 1:
            return 0.5
        last = df.iloc[-1]
        body = abs(last['close'] - last['open'])
        range_ = last['high'] - last['low']
        return (body / range_) if range_ > 0 else 0.5
    
    def _recent_high_proximity(self, context) -> float:
        """How close is current price to recent high (0-1, where 1 = at high)."""
        df = context.df
        if len(df) < 20:
            return 0.5
        recent_high = df['high'].iloc[-20:].max()
        if recent_high == 0:
            return 0.5
        distance = (recent_high - context.price) / recent_high
        return max(0, min(1, 1 - distance))  # 1 = at high, 0 = far from high
    
    def _recent_low_proximity(self, context) -> float:
        """How close is current price to recent low (0-1, where 1 = at low)."""
        df = context.df
        if len(df) < 20:
            return 0.5
        recent_low = df['low'].iloc[-20:].min()
        if recent_low == 0:
            return 0.5
        distance = (context.price - recent_low) / recent_low
        return max(0, min(1, 1 - distance))  # 1 = at low, 0 = far from low
    
    def _pullback_depth(self, context) -> float:
        """Pullback as % of impulse body (normalized 0-1)."""
        impulse = context.features.get('last_impulse', {})
        if not impulse or 'body' not in impulse:
            return 0.5
        body = float(impulse.get('body', 1))
        retrace = context.features.get('pullback_depth', 0.5 * body)
        return min(1.0, retrace / body if body > 0 else 0.5)
    
    def _recent_candle_body_ratio(self, candle) -> float:
        """Body as % of range (0-1)."""
        if candle is None:
            return 0.5
        body = abs(candle['close'] - candle['open'])
        range_ = candle['high'] - candle['low']
        return (body / range_) if range_ > 0 else 0.5
    
    def _recent_candle_wick_ratio(self, candle) -> float:
        """Upper + lower wicks as % of range (0-1)."""
        if candle is None:
            return 0.5
        upper_wick = candle['high'] - max(candle['close'], candle['open'])
        lower_wick = min(candle['close'], candle['open']) - candle['low']
        wicks = upper_wick + lower_wick
        range_ = candle['high'] - candle['low']
        return (wicks / range_) if range_ > 0 else 0.5
    
    def _candle_direction(self, candle) -> float:
        """1 = bullish, -1 = bearish, 0 = doji."""
        if candle is None:
            return 0.0
        if candle['close'] > candle['open']:
            return 1.0
        elif candle['close'] < candle['open']:
            return -1.0
        else:
            return 0.0
    
    def _candle_to_prev_ratio(self, candle, prev) -> float:
        """Current candle body vs. previous body ratio (0-2)."""
        if candle is None or prev is None:
            return 1.0
        body = abs(candle['close'] - candle['open'])
        prev_body = abs(prev['close'] - prev['open'])
        return (body / prev_body) if prev_body > 0 else 1.0
    
    def _entry_distance_from_extreme(self, context) -> float:
        """How far entry is from recent high/low (normalized 0-1)."""
        df = context.df
        if len(df) < 20:
            return 0.5
        recent_high = df['high'].iloc[-20:].max()
        recent_low = df['low'].iloc[-20:].min()
        range_ = recent_high - recent_low
        if range_ == 0:
            return 0.5
        # Distance from middle of range (0 = middle, 1 = extreme)
        mid = (recent_high + recent_low) / 2
        distance_from_mid = abs(context.price - mid)
        return min(1.0, distance_from_mid / (range_ / 2))
    
    def _pullback_phase_detection(self, context) -> float:
        """0-1: Are we in pullback phase (vs. impulse phase)?"""
        # If price near impulse extreme: 0 (impulse phase)
        # If price near FVG: 1 (pullback/accumulation phase)
        try:
            fvg = context.fvg_analysis.get('entry_zone', {})
            fvg_low = fvg.get('low')
            impulse = context.features.get('last_impulse', {})
            impulse_high = impulse.get('high')
            if fvg_low is None or impulse_high is None:
                return 0.5
            range_ = impulse_high - fvg_low
            distance_from_fvg = abs(context.price - fvg_low)
            return min(1.0, distance_from_fvg / range_) if range_ > 0 else 0.5
        except:
            return 0.5
    
    def _is_impulse_confirmed(self, context) -> bool:
        """Is there a confirmed impulse candle (body >70% range, >1.5x prev)."""
        df = context.df
        if len(df) < 2:
            return False
        last = df.iloc[-1]
        prev = df.iloc[-2]
        body = abs(last['close'] - last['open'])
        range_ = last['high'] - last['low']
        prev_body = abs(prev['close'] - prev['open'])
        if range_ == 0:
            return False
        body_ratio = body / range_
        return body_ratio > 0.7 and body > 1.5 * prev_body


# ============================================================================
# INTEGRATION INTO UNIFIED_TRADE_DECISION
# ============================================================================

def unified_trade_decision_v2(symbol, ml_confidence, features, df, entry, sl, tp):
    """
    NEW VERSION: ML-centric decision making.
    """
    # Initialize ML engine
    ml_engine = MLDecisionEngine('path/to/autoencoder_or_model.h5')
    
    # Analyze both directions
    buy_context = analyze_direction("buy")
    sell_context = analyze_direction("sell")
    
    # === ML SCORING (65% of decision) ===
    buy_ml_score, buy_ml_info = ml_engine.score_setup(buy_context)
    sell_ml_score, sell_ml_info = ml_engine.score_setup(sell_context)
    
    # === FEATURE SCORING (35% of decision) ===
    buy_feature_score = analyze_geometry(buy_context, entry, sl, tp)
    sell_feature_score = analyze_geometry(sell_context, entry, sl, tp)
    
    # === COMBINED DECISION ===
    buy_score = 0.65 * buy_ml_score + 0.35 * buy_feature_score
    sell_score = 0.65 * sell_ml_score + 0.35 * sell_feature_score
    
    # Choose direction
    if buy_score > sell_score and buy_score >= 60:
        chosen = buy_context
        chosen_direction = "buy"
        final_score = buy_score
        ml_score = buy_ml_score
        ml_info = buy_ml_info
    elif sell_score > buy_score and sell_score >= 60:
        chosen = sell_context
        chosen_direction = "sell"
        final_score = sell_score
        ml_score = sell_ml_score
        ml_info = sell_ml_info
    else:
        return False, None, 0.0, f"No valid trade (Buy: {buy_score:.0f}, Sell: {sell_score:.0f})", None
    
    # Position sizing based on ML confidence
    if final_score < 50:
        return False, chosen_direction, final_score, "ML score too low", None
    elif final_score < 60:
        size_mult = 0.3
    elif final_score < 75:
        size_mult = 0.7
    elif final_score < 85:
        size_mult = 1.0
    else:
        size_mult = 1.2
    
    log_trace = f"""
    === ML-CENTRIC DECISION ===
    ML Model Score: {ml_score:.0f}/100 ({ml_info.get('confidence_level', 'unknown')})
    Feature Score: {buy_feature_score if chosen_direction == 'buy' else sell_feature_score:.0f}/100
    
    COMBINED SCORE: {final_score:.0f}/100
    SIZE MULTIPLIER: {size_mult:.1f}x
    
    Supporting Factors: {chosen.supporting_filters}
    ML Insights: {ml_info}
    """
    
    return True, chosen_direction, final_score, "ML-driven trade approved", log_trace

def analyze_geometry(context, entry, sl, tp) -> float:
    """
    Score geometry/risk-reward independently of ML.
    Returns: 0-100 feature score
    """
    # R:R ratio
    pip_value = 0.0001 if 'JPY' not in context.symbol else 0.01
    sl_pips = abs(entry - sl) / pip_value
    tp_pips = abs(tp - entry) / pip_value
    rr_ratio = tp_pips / sl_pips if sl_pips > 0 else 0
    rr_score = min(100, rr_ratio * 30)  # 1:3 = 100/100
    
    # Risk/Reward placement (not at first resistance)
    tp_quality = 50  # TODO: Check TP not at first resistance
    
    # Entry zone quality
    zone_score = 50  # TODO: Score entry zone proximity
    
    feature_score = (rr_score * 0.4 + tp_quality * 0.3 + zone_score * 0.3)
    return min(100, feature_score)

```

---

### Part 2: Retrain ML Model on Best Trades

**File**: `ml_retraining_logic.py` (NEW)

```python
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

def retrain_on_best_trades(
    historical_trades_df,
    winning_trades_df,
    model_path: str,
    retrain_frequency_days: int = 7
):
    """
    Periodically retrain model on actual winning trades from this market/pair.
    
    Args:
        historical_trades_df: All trades (columns: entry, sl, tp, outcome, features...)
        winning_trades_df: Only trades with profit > 1R (subset of historical)
        model_path: Path to save updated model
        retrain_frequency_days: Only retrain if >7 days since last training
    
    Process:
        1. Extract features from winning trades
        2. Create synthetic "losing" samples (valid setups but wrong direction)
        3. Train autoencoder to encode winning setups
        4. Save retrained model
    """
    
    # Filter to winning trades (profit > 1R)
    winners = winning_trades_df[winning_trades_df['pnl_in_r'] > 1.0]
    
    if len(winners) < 20:
        print(f"[WARNING] Only {len(winners)} winning trades; skipping retrain")
        return False
    
    # Extract feature vectors from winners
    X_winners = extract_features_from_trades(winners)
    
    # Create synthetic losers (same setups, opposite direction)
    X_losers = create_synthetic_losers(historical_trades_df)
    
    # Combine
    X = np.vstack([X_winners, X_losers])
    y = np.hstack([np.ones(len(X_winners)), np.zeros(len(X_losers))])
    
    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Retrain autoencoder (minimize reconstruction error on winners)
    from tensorflow import keras
    
    model = keras.Sequential([
        keras.layers.Dense(32, activation='relu', input_dim=X.shape[1]),
        keras.layers.Dense(16, activation='relu'),
        keras.layers.Dense(8, activation='relu'),
        keras.layers.Dense(16, activation='relu'),
        keras.layers.Dense(32, activation='relu'),
        keras.layers.Dense(X.shape[1])
    ])
    
    model.compile(optimizer='adam', loss='mse')
    
    # Train mostly on winners (70% winners, 30% losers)
    sample_weights = np.where(y == 1, 1.0, 0.3)
    
    model.fit(
        X_scaled, X_scaled,
        epochs=100,
        batch_size=32,
        sample_weight=sample_weights,
        validation_split=0.2,
        verbose=1
    )
    
    # Save
    model.save(model_path)
    joblib.dump(scaler, model_path.replace('.h5', '_scaler.pkl'))
    
    print(f"[SUCCESS] Retrained model on {len(winners)} winning trades")
    return True

def extract_features_from_trades(trades_df) -> np.ndarray:
    """
    Convert trade records into feature vectors (same as MLDecisionEngine.extract_features).
    """
    features = []
    for _, trade in trades_df.iterrows():
        feature_vector = [
            # BOS confirmed
            1.0 if trade.get('bos_confirmed') else 0.0,
            # FVG quality
            trade.get('fvg_quality', 50) / 100,
            # Impulse body ratio
            trade.get('impulse_body_ratio', 0.5),
            # ... (20+ more features)
        ]
        features.append(feature_vector)
    
    return np.array(features)

def create_synthetic_losers(trades_df) -> np.ndarray:
    """
    Create synthetic negative examples by flipping trade direction.
    """
    # TODO: Implement feature flipping logic
    pass

```

---

### Part 3: Update `compute_unified_decision()` to Use ML-Centric Scoring

**In botfriday6000th.py**, replace lines ~1939-2370 with:

```python
def unified_trade_decision_ML_v2(symbol, ml_confidence, features, df, entry, sl, tp):
    """
    ML-CENTRIC DECISION ENGINE (65% ML, 35% heuristics)
    
    Replaces the cascading blocker model with transparent scoring.
    """
    from ml_decision_engine import MLDecisionEngine
    
    # Initialize ML engine
    ml_engine = MLDecisionEngine(f'autoencoder_{symbol}.h5')
    
    # Analyze both directions
    buy_context = analyze_direction("buy")
    sell_context = analyze_direction("sell")
    
    # Score using ML (65%) + geometry (35%)
    buy_ml, buy_ml_info = ml_engine.score_setup(buy_context)
    sell_ml, sell_ml_info = ml_engine.score_setup(sell_context)
    
    buy_feature = analyze_geometry(buy_context, entry, sl, tp)
    sell_feature = analyze_geometry(sell_context, entry, sl, tp)
    
    buy_final = 0.65 * buy_ml + 0.35 * buy_feature
    sell_final = 0.65 * sell_ml + 0.35 * sell_feature
    
    # Choose direction
    if buy_final > sell_final and buy_final >= 60:
        chosen = buy_context
        final_score = buy_final
        direction = "buy"
    elif sell_final > buy_final and sell_final >= 60:
        chosen = sell_context
        final_score = sell_final
        direction = "sell"
    else:
        print(f"\n[ML DECISION] {symbol} - SKIP (Buy: {buy_final:.0f}, Sell: {sell_final:.0f})")
        return False, None, 0.0, "ML score insufficient", None
    
    # Derive position sizing from score
    if final_score < 60:
        return False, direction, final_score, "Below minimum threshold", None
    elif final_score < 75:
        size_mult = 0.7
    elif final_score < 85:
        size_mult = 1.0
    else:
        size_mult = 1.2
    
    # Log decision
    print(f"\n[ML DECISION] {symbol} {direction.upper()} - Score: {final_score:.0f}/100")
    print(f"  ML: {buy_ml:.0f}/100 (LVL: {buy_ml_info.get('confidence_level')})")
    print(f"  Features: {buy_feature:.0f}/100")
    print(f"  Size: {size_mult:.1f}x | Supporting: {chosen.supporting_filters}\n")
    
    chosen.features['size_multiplier'] = size_mult
    return True, direction, final_score, f"ML-approved trade", chosen
```

---

## Key Changes Summary

| Aspect | Old (Heuristic-Heavy) | New (ML-Centric) |
|--------|------|------|
| **Decision Driver** | 7 cascading filters | ML model (65%) + geometry (35%) |
| **ML Role** | Confidence tweak (±10%) | Primary driver (65% weight) |
| **Rejection Reason** | "Filter X failed" | "ML score 45/100: fuzzy pattern" |
| **Position Size** | Static or filter-based | Dynamic (based on ML confidence) |
| **Retraining** | Manual / never | Every 7 days on actual winners |
| **Adaptability** | Static rules | Learns current regime |

---

## Testing Checklist

- [ ] Extract features correctly from TradeDecisionContext
- [ ] ML model loads and scores setups (no crashes)
- [ ] Decision trace logs clearly (direction, scores, size)
- [ ] Backtest on historical data: # trades, win %, avg winner/loser
- [ ] Compare: new ML version vs. old heuristic version
- [ ] Paper trade for 1 week
- [ ] Live trade with 0.01 lot for 2 weeks
- [ ] Monitor: actual fill rates, actual win %, retraining impact

