# 🚀 MULTI-MODEL INTEGRATION GUIDE

## Quick Start

### Step 1: Call Model Selector in Entry Logic
```python
# In compute_unified_decision() or main entry loop:

model_result = select_best_entry_model(context)

if not model_result['should_enter']:
    context.should_trade = False
    print(f"[MODEL SELECTOR] No suitable entry model")
    return

best_model = model_result['best_model']
model_confidence = model_result['confidence']

print(f"[ENTRY MODEL] {best_model} selected ({model_confidence:.0%})")
print(f"[RECOMMENDATION] {model_result['recommendation']}")

# Store for trade logging
context.entry_model = best_model
context.model_confidence = model_confidence
```

### Step 2: Model-Specific Entry Logic
```python
# Route to model-specific logic based on selection

if best_model == 'hydra':
    # Require high confidence (3+ heads)
    if model_confidence < 0.65:
        BLOCK_ENTRY()
    else:
        ALLOW_ENTRY()

elif best_model == 'smc_classic':
    # Allow entry if 3+ stages confirmed
    if model_confidence >= 0.6:
        ALLOW_ENTRY()
    else:
        WAIT_FOR_NEXT_STAGE()

elif best_model == 'hydra_lite':
    # Entry if 3+ conditions met
    if model_confidence >= 0.5:
        ALLOW_ENTRY()
    else:
        BLOCK_ENTRY()

elif best_model == 'displacement':
    # Trend filter mandatory
    if context.htf_bias != context.signal:
        BLOCK_ENTRY()
    else:
        ALLOW_ENTRY()

elif best_model == 'range_fade':
    # Range must be confirmed
    if model_confidence >= 0.6:
        ALLOW_ENTRY()
    else:
        BLOCK_ENTRY()
```

### Step 3: Execute with Model Confidence
```python
# Adjust position sizing based on model confidence

base_lot = 0.01
model_multiplier = model_confidence  # 0.5-1.0

adjusted_lot = base_lot * model_multiplier

print(f"[POSITION SIZE] {adjusted_lot:.4f} lot ({model_confidence:.0%} of base)")

# Place trade
place_trade(
    symbol=context.symbol,
    direction=context.signal,
    lot_size=adjusted_lot,
    entry_price=context.limit_price if hasattr(context, 'limit_price') else context.price,
    entry_model=best_model,
    model_confidence=model_confidence
)
```

---

## Complete Entry Flow

```
┌─────────────────────────────────────────────┐
│ Main Trading Loop                           │
│ - Get current data                          │
│ - Analyze HTF/M15/M5 structure              │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ select_best_entry_model(context)            │
│ - Evaluate all 5 models                     │
│ - Score each based on conditions            │
│ - Return best match + confidence            │
└──────────────┬──────────────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
    MODEL 1      MODEL 2
   (Hydra)    (SMC Classic)
        │             │
        │   MODEL 3   │
        │  (Hydra-    │
        │   Lite)     │
        │             │
        │   MODEL 4   │
        │(Displacement)
        │             │
        │   MODEL 5   │
        │(Range Fade) │
        │             │
        └──────┬──────┘
               │
        ▼ (Best Model Selected)
┌─────────────────────────────────────────────┐
│ Model-Specific Validation                   │
│ - Check model confidence threshold          │
│ - Verify model-specific requirements        │
│ - Apply model gates                         │
└──────────────┬──────────────────────────────┘
               │
         ┌─────┴─────┐
         ▼           ▼
      ENTRY      WAIT/BLOCK
     Allowed     Entry Rejected
         │           │
         ▼           ▼
    Calculate    Continue Loop
    Position Size
         │
         ▼
    Place Trade
    (with model metadata)
         │
         ▼
    Trade Executed
    (logged with entry model)
```

---

## Function Reference

### select_best_entry_model(context)
**Location:** `botfriday90000th.py` line 7395

```python
result = select_best_entry_model(context)

# Returns:
{
    'best_model': 'hydra' | 'smc_classic' | 'hydra_lite' | 'displacement' | 'range_fade',
    'confidence': 0.0-1.0,  # How confident is this model?
    'all_models': {         # All model results
        'hydra': {...},
        'smc_classic': {...},
        ...
    },
    'recommendation': str,  # Explanation of choice
    'should_enter': bool    # Final entry decision
}
```

### evaluate_hydra_model(context)
**Location:** `botfriday90000th.py` line 7005

```python
result = evaluate_hydra_model(context)

# Returns:
{
    'applicable': bool,      # 3+ heads aligned?
    'heads_aligned': 0-5,    # How many heads?
    'heads_details': [...],  # List of head statuses
    'confidence': 0.0-1.0,   # Confidence
    'reasoning': str         # Why applicable/not
}
```

### evaluate_smc_classic_model(context)
**Location:** `botfriday90000th.py` line 7080

```python
result = evaluate_smc_classic_model(context)

# Returns:
{
    'applicable': bool,           # Can enter?
    'flow_stage': 'sweep_detected' | 'bos_confirmed' | 'in_retrace' | 'entry_ready',
    'confidence': 0.0-1.0,        # How far through flow?
    'reasoning': str              # Current stage
}
```

### evaluate_hydra_lite_model(context)
**Location:** `botfriday90000th.py` line 7152

```python
result = evaluate_hydra_lite_model(context)

# Returns:
{
    'applicable': bool,           # 3+ conditions met?
    'score': 0-6,                 # How many conditions?
    'conditions_met': [...],      # List of conditions
    'confidence': 0.0-1.0,        # Confidence
    'reasoning': str              # Score explanation
}
```

### evaluate_displacement_pullback_model(context)
**Location:** `botfriday90000th.py` line 7231

```python
result = evaluate_displacement_pullback_model(context)

# Returns:
{
    'applicable': bool,                                    # Can enter?
    'stage': 'no_trend' | 'no_displacement' | 'in_pullback',
    'confidence': 0.0-1.0,                                 # Stage progress
    'reasoning': str                                       # Why this stage
}
```

### evaluate_range_liquidity_fade_model(context)
**Location:** `botfriday90000th.py` line 7302

```python
result = evaluate_range_liquidity_fade_model(context)

# Returns:
{
    'applicable': bool,                                    # Can enter?
    'setup_type': 'equal_highs' | 'equal_lows' | 'session_extreme',
    'fade_direction': 'buy' | 'sell' | 'none',             # Which direction to fade
    'confidence': 0.0-1.0,                                 # Setup strength
    'reasoning': str                                       # Setup details
}
```

---

## Context Requirements

For all models to work, `context` should have:

```python
context = {
    # Basic
    'symbol': 'EURUSD',
    'signal': 'buy' | 'sell',
    'price': 1.19300,
    
    # Dataframes
    'df': df_m15,           # Main data (M15)
    'df_m5': df_m5,         # M5 data for candle confirmation
    
    # HTF Analysis
    'htf_bias': 'bullish' | 'bearish' | None,
    'htf_score': -10.0 to 10.0,
    
    # Structure
    'bos_confirmed_m15': bool,
    'bos_strength': 0.0-1.0,
    'choch_confirmed': bool,
    'liquidity_swept': bool,
    
    # FVG/POI
    'fvg_detected': bool,
    'fvg_analysis': {'low': float, 'high': float, ...},
    'price_in_discount': bool,
    'price_in_premium': bool,
    'price_in_fvg': bool,
    
    # Candle
    'candle_check': {'confirmed': bool, 'confirmation_type': str, ...},
    
    # Volatility/Volume (for Hydra-Lite)
    'current_atr': float,
    'avg_atr': float,
    'current_volume': float,
    'avg_volume': float,
    
    # Session info (for Range Fade)
    'session_high': float,
    'session_low': float,
}
```

---

## Debugging

### Check All Model Outputs
```python
result = select_best_entry_model(context)

print("[ALL MODELS]")
for model_name, model_result in result['all_models'].items():
    applicable = model_result.get('applicable', False)
    confidence = model_result.get('confidence', 0)
    print(f"  {model_name}: {'✓' if applicable else '✗'} ({confidence:.0%})")

print(f"\n[WINNER] {result['best_model']} ({result['confidence']:.0%})")
print(f"[DECISION] {'ENTER' if result['should_enter'] else 'BLOCK'}")
```

### Model-Specific Debugging
```python
# Debug Hydra
hydra = evaluate_hydra_model(context)
for head in hydra['heads_details']:
    print(head)

# Debug SMC
smc = evaluate_smc_classic_model(context)
print(f"Flow stage: {smc['flow_stage']}")

# Debug Hydra-Lite
hydra_lite = evaluate_hydra_lite_model(context)
for cond in hydra_lite['conditions_met']:
    print(cond)

# Debug Displacement
disp = evaluate_displacement_pullback_model(context)
print(f"Stage: {disp['stage']}")

# Debug Range Fade
fade = evaluate_range_liquidity_fade_model(context)
print(f"Setup: {fade['setup_type']}, Fade: {fade['fade_direction']}")
```

---

## Position Sizing by Model

### Conservative (Lower Confidence)
```python
if model_confidence < 0.6:
    lot_size = base_lot * 0.5  # 50% of base
    
elif model_confidence < 0.7:
    lot_size = base_lot * 0.75  # 75% of base
```

### Standard (Medium Confidence)
```python
elif model_confidence >= 0.7 and model_confidence < 0.85:
    lot_size = base_lot * 1.0   # 100% of base
```

### Aggressive (High Confidence)
```python
elif model_confidence >= 0.85:
    lot_size = base_lot * 1.25  # 125% of base
```

---

## Trade Logging

After execution, log the entry model:

```python
trade_data = {
    'symbol': context.symbol,
    'direction': context.signal,
    'entry_price': entry_price,
    'entry_time': datetime.now(),
    
    # Model info
    'entry_model': context.entry_model,
    'model_confidence': context.model_confidence,
    
    # Model-specific details
    'hydra_heads': hydra_result.get('heads_aligned'),
    'smc_stage': smc_result.get('flow_stage'),
    'hydra_lite_score': hydra_lite_result.get('score'),
    'displacement_stage': disp_result.get('stage'),
    'range_setup': fade_result.get('setup_type'),
}

log_trade(trade_data)
```

---

## Performance Targets

Over 100 trades:

| Model | Count | Win% | RR | Avg Profit |
|-------|-------|------|-----|-----------|
| Hydra | 25 | 65% | 1:1.8 | $1,170 |
| SMC | 30 | 58% | 1:3.5 | $1,680 |
| Hydra-Lite | 20 | 58% | 1:2.0 | $930 |
| Displacement | 15 | 68% | 1:2.5 | $765 |
| Range Fade | 10 | 62% | 1:3.0 | $465 |

**Total:** 100 trades, 60.4% win rate, 1:2.6 RR, **$5,010 profit**

---

## Summary

1. ✅ **Call `select_best_entry_model(context)`** to choose model
2. ✅ **Check `should_enter`** and `confidence`
3. ✅ **Apply model-specific validation** (HTF trend, BOS stage, etc.)
4. ✅ **Size position** based on `model_confidence`
5. ✅ **Log trade** with entry model metadata
6. ✅ **Monitor results** by model (Hydra should have 65%+ win rate)

**Integration status:** Ready for copy/paste into main entry logic
