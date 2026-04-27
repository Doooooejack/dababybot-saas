# Real-World Integration Examples

This document shows practical examples of how to use and customize the three new trading features.

## Example 1: Using Displacement Candle Block Standalone

```python
import pandas as pd
from botfriday20000th import detect_displacement_candle_block

# Load your market data
df = pd.read_csv('XAUUSD_M15.csv')

# Check for displacement on BUY entries
direction = "buy"
result = detect_displacement_candle_block(
    df, 
    direction,
    atr_multiplier=2.0,    # Default: blocks candles > 2x ATR
    volume_threshold=1.2   # Default: requires volume > 120% of average
)

print(f"Is displacement candle? {result['is_displacement']}")
print(f"Displacement strength: {result['displacement_strength']:.2f}")
print(f"Block entry? {result['block_entry']}")
print(f"Reason: {result['reason']}")

# Example Output:
# Is displacement candle? True
# Displacement strength: 0.82
# Block entry? True
# Reason: Strong displacement move detected (strength: 0.82). Price has run too hard — wait for pullback.
```

## Example 2: Using Break-Reclaim Confirmation

```python
from botfriday20000th import detect_break_reclaim_confirmation

# Check for break-reclaim pattern
direction = "buy"
br_result = detect_break_reclaim_confirmation(
    df,
    direction,
    lookback=20  # Look back 20 bars for the pattern
)

if br_result['break_reclaim_detected']:
    print(f"✅ Break-reclaim detected!")
    print(f"   Break Price: {br_result['break_price']:.4f}")
    print(f"   Reclaim Zone: {br_result['reclaim_zone_low']:.4f} - {br_result['reclaim_zone_high']:.4f}")
    print(f"   Confirmation Strength: {br_result['confirmation_strength']:.2f}")
    
    if br_result['is_confirmed']:
        print(f"   Status: ✅ CONFIRMED (price is above break level)")
        # This is ideal - price has broken through and reclaimed
        confidence_boost = 1.0 + (br_result['confirmation_strength'] * 0.2)
    else:
        print(f"   Status: ⏳ PENDING (waiting for confirmation)")
        confidence_boost = 1.0

# Example Output:
# ✅ Break-reclaim detected!
#    Break Price: 2050.3500
#    Reclaim Zone: 2050.3495 - 2050.3505
#    Confirmation Strength: 0.68
#    Status: ✅ CONFIRMED (price is above break level)
```

## Example 3: Using ATR/Volatility Filter

```python
from botfriday20000th import validate_atr_volatility_filter

# Validate volatility conditions before trading
vol_result = validate_atr_volatility_filter(
    df,
    direction="buy",
    min_atr_threshold=0.3,      # Minimum ATR for entry
    max_atr_threshold=50.0,     # Maximum ATR before blocking
    volatility_regime='auto'    # Auto-detect regime
)

print(f"ATR Value: {vol_result['atr_value']:.4f}")
print(f"Valid for Trading? {vol_result['is_valid']}")
print(f"Volatility Regime: {vol_result['volatility_regime']}")
print(f"ATR Ratio: {vol_result['atr_ratio']:.2f}x (vs historical average)")
print(f"Confidence Boost: {vol_result['confidence_boost']:.2f}x")

if not vol_result['is_valid']:
    print(f"❌ Reason for Block: {vol_result['block_reason']}")

# Example Output 1 (Normal conditions):
# ATR Value: 0.4523
# Valid for Trading? True
# Volatility Regime: normal
# ATR Ratio: 0.95x (vs historical average)
# Confidence Boost: 1.00x

# Example Output 2 (Dead market):
# ATR Value: 0.1235
# Valid for Trading? False
# Volatility Regime: low
# ATR Ratio: 0.65x (vs historical average)
# Confidence Boost: 0.70x
# ❌ Reason for Block: Market too quiet (ATR: 0.1235 < threshold: 0.21). Avoid low volatility entries.

# Example Output 3 (Volatility spike):
# ATR Value: 45.3200
# Valid for Trading? False
# Volatility Regime: high
# ATR Ratio: 1.85x (vs historical average)
# Confidence Boost: 1.10x
# ❌ Reason for Block: Volatility too extreme (ATR: 45.3200 > threshold: 30.0000). Risk of spike moves.
```

## Example 4: Complete Integration - Custom Entry Function

```python
from botfriday20000th import (
    detect_displacement_candle_block,
    detect_break_reclaim_confirmation,
    validate_atr_volatility_filter
)

def validate_and_enter(df, symbol, direction, base_confidence=0.80):
    """
    Complete validation pipeline for entries using all three filters.
    
    Returns: (should_enter, final_confidence, validation_details)
    """
    
    validation_details = {}
    
    # STEP 1: Volatility Filter (pre-check)
    vol_check = validate_atr_volatility_filter(df, direction)
    validation_details['volatility'] = vol_check
    
    if not vol_check['is_valid']:
        print(f"[BLOCKED] {symbol}: {vol_check['block_reason']}")
        return False, 0.0, validation_details
    
    # STEP 2: Displacement Check
    displacement = detect_displacement_candle_block(df, direction)
    validation_details['displacement'] = displacement
    
    if displacement['block_entry']:
        print(f"[BLOCKED] {symbol}: {displacement['reason']}")
        return False, 0.0, validation_details
    
    # STEP 3: Break-Reclaim Confirmation
    br = detect_break_reclaim_confirmation(df, direction)
    validation_details['break_reclaim'] = br
    
    # STEP 4: Calculate Final Confidence
    final_confidence = base_confidence
    
    # Apply volatility multiplier
    final_confidence *= vol_check['confidence_boost']
    
    # Apply break-reclaim boost if confirmed
    if br['is_confirmed']:
        final_confidence *= (1.0 + br['confirmation_strength'] * 0.2)
    
    # Apply displacement penalty if detected (not blocking but cautionary)
    if displacement['is_displacement']:
        final_confidence *= 0.9
    
    final_confidence = min(final_confidence, 1.0)  # Cap at 1.0
    
    print(f"✅ {symbol} {direction.upper()} | Confidence: {final_confidence:.2f}")
    print(f"   Base: {base_confidence:.2f} → Vol×{vol_check['confidence_boost']:.2f} → BR×{1.0 + (br['confirmation_strength']*0.2 if br['is_confirmed'] else 0):.2f} → Result: {final_confidence:.2f}")
    
    return True, final_confidence, validation_details

# Usage:
should_enter, confidence, details = validate_and_enter(
    df,
    symbol="XAUUSD",
    direction="buy",
    base_confidence=0.85
)

if should_enter:
    print(f"Execute BUY with confidence {confidence:.2f}")
    # Execute trade here
```

## Example 5: Customizing Parameters for Different Market Conditions

```python
# AGGRESSIVE TRADING (Accept more entries)
# - Lower displacement threshold (allow stronger runs)
# - Shorter lookback for patterns
# - Allow more volatile conditions

def aggressive_entry_validation(df, direction):
    vol = validate_atr_volatility_filter(
        df, direction,
        min_atr_threshold=0.2,     # Lower minimum (accept quieter markets)
        max_atr_threshold=75.0,    # Higher maximum (accept spikes)
        volatility_regime='auto'
    )
    
    displacement = detect_displacement_candle_block(
        df, direction,
        atr_multiplier=2.5,        # Higher multiplier = less blocking
        volume_threshold=1.0       # Lower volume requirement
    )
    
    br = detect_break_reclaim_confirmation(
        df, direction,
        lookback=15                # Shorter lookback
    )
    
    return vol, displacement, br


# CONSERVATIVE TRADING (Accept fewer but higher quality entries)
# - Higher displacement threshold (only very clean entries)
# - Longer lookback for confirmed patterns
# - Avoid volatile conditions

def conservative_entry_validation(df, direction):
    vol = validate_atr_volatility_filter(
        df, direction,
        min_atr_threshold=0.5,     # Higher minimum (avoid quiet markets)
        max_atr_threshold=25.0,    # Lower maximum (avoid spikes)
        volatility_regime='normal' # Force normal regime
    )
    
    displacement = detect_displacement_candle_block(
        df, direction,
        atr_multiplier=1.5,        # Lower multiplier = more blocking
        volume_threshold=1.5       # Higher volume requirement
    )
    
    br = detect_break_reclaim_confirmation(
        df, direction,
        lookback=30                # Longer lookback for stronger confirmation
    )
    
    return vol, displacement, br
```

## Example 6: Logging and Monitoring

```python
import logging

logger = logging.getLogger(__name__)

def log_validation_results(symbol, direction, vol, displacement, br, final_confidence):
    """
    Comprehensive logging of all validation results.
    """
    
    logger.info(f"{'='*60}")
    logger.info(f"ENTRY VALIDATION: {symbol} {direction.upper()}")
    logger.info(f"{'='*60}")
    
    # Volatility
    logger.info(f"VOLATILITY CHECK:")
    logger.info(f"  ATR: {vol['atr_value']:.4f}")
    logger.info(f"  Regime: {vol['volatility_regime']}")
    logger.info(f"  Ratio: {vol['atr_ratio']:.2f}x")
    logger.info(f"  Valid: {vol['is_valid']} {f'({vol[\"block_reason\"]})' if not vol['is_valid'] else ''}")
    logger.info(f"  Boost: {vol['confidence_boost']:.2f}x")
    
    # Displacement
    logger.info(f"DISPLACEMENT CHECK:")
    logger.info(f"  Is Displacement: {displacement['is_displacement']}")
    logger.info(f"  Strength: {displacement['displacement_strength']:.2f}")
    logger.info(f"  Block: {displacement['block_entry']}")
    logger.info(f"  Reason: {displacement['reason']}")
    
    # Break-Reclaim
    logger.info(f"BREAK-RECLAIM CHECK:")
    logger.info(f"  Detected: {br['break_reclaim_detected']}")
    if br['break_reclaim_detected']:
        logger.info(f"  Break Price: {br['break_price']:.4f}")
        logger.info(f"  Confirmed: {br['is_confirmed']}")
        logger.info(f"  Strength: {br['confirmation_strength']:.2f}")
    
    # Final Decision
    logger.info(f"FINAL DECISION:")
    logger.info(f"  Confidence: {final_confidence:.2f}")
    logger.info(f"{'='*60}")
    
    # Also print to console for real-time monitoring
    print(f"[{symbol}] {direction.upper()} → Confidence: {final_confidence:.2f}")

# Usage:
log_validation_results(symbol, direction, vol, displacement, br, final_confidence)
```

## Example 7: Backtesting Filter Effectiveness

```python
def backtest_filter_impact(trades_df):
    """
    Analyze the impact of the new filters on historical trades.
    """
    
    total_trades = len(trades_df)
    blocked_trades = len(trades_df[trades_df['displacement_blocked'] == True])
    displacement_cautions = len(trades_df[trades_df['displacement_detected'] == True])
    br_confirmed = len(trades_df[trades_df['break_reclaim_confirmed'] == True])
    
    print(f"Trade Analysis:")
    print(f"  Total Trades: {total_trades}")
    print(f"  Blocked by Displacement: {blocked_trades} ({100*blocked_trades/total_trades:.1f}%)")
    print(f"  Displacement Detected: {displacement_cautions} ({100*displacement_cautions/total_trades:.1f}%)")
    print(f"  Break-Reclaim Confirmed: {br_confirmed} ({100*br_confirmed/total_trades:.1f}%)")
    
    # Win rate analysis
    blocked_wr = trades_df[trades_df['displacement_blocked'] == True]['win_loss'].mean()
    caution_wr = trades_df[trades_df['displacement_detected'] == True]['win_loss'].mean()
    clean_wr = trades_df[trades_df['displacement_detected'] == False]['win_loss'].mean()
    br_confirmed_wr = trades_df[trades_df['break_reclaim_confirmed'] == True]['win_loss'].mean()
    
    print(f"\nWin Rate Analysis:")
    print(f"  Clean Entries (no displacement): {clean_wr:.1%}")
    print(f"  Displacement Caution Trades: {caution_wr:.1%}")
    print(f"  Break-Reclaim Confirmed: {br_confirmed_wr:.1%}")
    
    print(f"\nRecommendation:")
    if clean_wr > caution_wr:
        print(f"  ✅ Block displacement trades (saves {(caution_wr-clean_wr)*100:.1f}% losses)")
    if br_confirmed_wr > clean_wr:
        print(f"  ✅ Prioritize break-reclaim confirmed trades (gains {(br_confirmed_wr-clean_wr)*100:.1f}%)")
```

## Quick Reference: Parameter Tuning

### Conservative Settings (Lower Risk, Fewer Entries)
```python
displacement = detect_displacement_candle_block(
    df, direction,
    atr_multiplier=1.5,    # ⬇️ Lower = more blocking
    volume_threshold=1.5   # ⬆️ Higher = stricter
)

vol = validate_atr_volatility_filter(
    df, direction,
    min_atr_threshold=0.5, # ⬆️ Higher = avoid dead markets
    max_atr_threshold=25.0 # ⬇️ Lower = avoid spikes
)

br = detect_break_reclaim_confirmation(
    df, direction,
    lookback=30            # ⬆️ Longer = stronger confirmation needed
)
```

### Aggressive Settings (Higher Risk, More Entries)
```python
displacement = detect_displacement_candle_block(
    df, direction,
    atr_multiplier=2.5,    # ⬆️ Higher = less blocking
    volume_threshold=1.0   # ⬇️ Lower = less strict
)

vol = validate_atr_volatility_filter(
    df, direction,
    min_atr_threshold=0.2, # ⬇️ Lower = accept quiet
    max_atr_threshold=75.0 # ⬆️ Higher = accept spikes
)

br = detect_break_reclaim_confirmation(
    df, direction,
    lookback=15            # ⬇️ Shorter = faster confirmation
)
```

### Balanced Settings (Default)
```python
displacement = detect_displacement_candle_block(
    df, direction,
    atr_multiplier=2.0,    # Standard
    volume_threshold=1.2   # Standard
)

vol = validate_atr_volatility_filter(
    df, direction,
    min_atr_threshold=0.3,
    max_atr_threshold=50.0
)

br = detect_break_reclaim_confirmation(
    df, direction,
    lookback=20            # Balanced
)
```

---

## Summary

These real-world examples show how to:
1. ✅ Use each filter independently
2. ✅ Combine all three in a complete validation pipeline
3. ✅ Customize parameters for different trading styles
4. ✅ Monitor and log validation results
5. ✅ Backtest filter effectiveness
6. ✅ Adjust settings based on market conditions

Start with the default/balanced settings and adjust based on your backtesting results.
