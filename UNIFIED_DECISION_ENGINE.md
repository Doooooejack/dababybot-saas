# Unified Trade Decision Engine

## Problem Solved

Your bot had **20+ independent filters** running in isolation. Each system (HTF Trend, ML Model, FVG Detection, Volume, Risk-Reward, etc.) was producing its own results but **not communicating with each other before placing trades**. This meant:

- ❌ FVG detection ran but didn't coordinate with HTF trend
- ❌ ML confidence existed but HTF could still block silently
- ❌ Volume confirmations were logged but didn't affect the actual decision
- ❌ Multiple signals saying "NO" could still result in a trade being placed
- ❌ Trade quality was unpredictable because no consensus was enforced

---

## Solution: Unified Decision Engine

A new **TradeDecisionContext** orchestrates ALL analyses into a single, coordinated decision:

### Architecture

```
SIGNAL GENERATION
    ↓
UNIFIED DECISION ENGINE (TradeDecisionContext)
    ├─→ analyze_htf_trend()            [HTF alignment check]
    ├─→ analyze_fvg_zone()             [Entry zone confirmation]
    ├─→ analyze_momentum_confluence()  [RSI/MACD validation]
    ├─→ analyze_volume_confirmation()  [Volume spike check]
    ├─→ analyze_risk_reward()          [RR ratio validation]
    ├─→ analyze_market_regime()        [Session/news/regime check]
    └─→ compute_unified_decision()     [Synthesize all inputs]
        ├─ Check BLOCKING filters
        ├─ Verify minimum ML confidence (70%)
        ├─ Require 2+ supporting factors
        └─ Return: TRADE or NO-TRADE decision
```

---

## How It Works

### 1. TradeDecisionContext (Container)
A class that holds all analysis results from each subsystem:

```python
context = TradeDecisionContext(symbol, signal, ml_confidence, features, df)
context.htf_analysis = {...}
context.fvg_analysis = {...}
context.momentum_analysis = {...}
# etc.
```

### 2. Six Parallel Analyses

Each function analyzes one aspect and **populates the same context object**:

#### **analyze_htf_trend()**
- Checks if HTF bias aligns with signal direction
- **Aligned (+bullish buy, -bearish sell)** → Supporting factor ✓
- **Neutral** → No block, but lower confidence
- **Conflict** → BLOCKING factor ✗

#### **analyze_fvg_zone()**
- Confirms FVG is detected and high-quality
- Checks if current price is within FVG entry zone
- **In zone** → Supporting factor ✓
- **Detected but out of zone** → BLOCKING factor ✗
- **Not detected** → Lower confidence only

#### **analyze_momentum_confluence()**
- Validates RSI and MACD support the direction
- **Supports** (RSI > 50 for buy, etc.) → Supporting factor ✓
- **Conflicts** (Overbought/oversold extremes) → BLOCKING factor ✗

#### **analyze_volume_confirmation()**
- Checks for volume spike on the move
- **Volume spike detected** → Supporting factor ✓
- **Volume normal/low** → Reduces confidence slightly

#### **analyze_risk_reward()**
- Validates risk-reward ratio >= 1.0
- Validates ATR is sufficient for the symbol
- **Good RR + sufficient ATR** → Supporting factor ✓
- **Poor RR** → BLOCKING factor ✗ (hard stop)

#### **analyze_market_regime()**
- Session-specific checks (XAU: 6-16 UTC only)
- News impact level
- Market regime compatibility
- **All OK** → Supporting factor ✓
- **Outside session or high news impact** → BLOCKING factor ✗

### 3. compute_unified_decision()

Synthesizes all inputs using a confidence algorithm:

**Base:** ML confidence (0-1)

**Adjustments:**
- HTF aligned: +15% boost
- HTF conflict: -35% penalty (harsh)
- FVG in zone: +10% boost
- FVG out of zone: -20% penalty
- Momentum supports: +10% boost
- Momentum conflicts: -20% penalty
- Volume spike: +5% boost
- Poor RR: -40% penalty (hard stop)

**Final Trade Logic:**
```
TRADE ALLOWED IF AND ONLY IF:
  1. NO blocking filters active
  2. Final confidence >= 70%
  3. >= 2 supporting factors
  4. HTF doesn't strongly conflict
```

---

## Example Decision Flow

### Scenario 1: GBPUSD BUY (REJECTED)
```
ML Signal: BUY, Confidence: 75% ✓
  HTF Trend: bearish → CONFLICT ✗
    → -35% penalty → 40% final confidence
  FVG Detected: YES, but out of zone
    → BLOCKING FILTER: FVG_OUT_OF_ZONE
  
DECISION: ✗ REJECTED
Reason: "BLOCKED: FVG_OUT_OF_ZONE"
```

### Scenario 2: XAUUSD BUY (APPROVED)
```
ML Signal: BUY, Confidence: 82% ✓
  HTF Trend: bullish → ALIGNED ✓
    → +15% boost → 97% confidence
  FVG Detected: YES, in zone → SUPPORTING ✓
  Momentum: RSI=55, MACD bullish → SUPPORTING ✓
  Volume: spike detected → SUPPORTING ✓
  Risk-Reward: 2.5:1 → SUPPORTING ✓
  Regime: London session, no news → SUPPORTING ✓

Supporting Factors: 6 ✓✓✓✓✓✓
Blocking Factors: 0 ✓

DECISION: ✓ APPROVED
Reason: "APPROVED: 6 confirming factors, confidence=97%"
Quality Score: 0.97
```

---

## Integration Point

The unified decision is called **RIGHT BEFORE ANY TRADE PLACEMENT**:

```python
# In botfriday6000th.py, line ~25600:

should_trade, quality_score, decision_reason, context = unified_trade_decision(
    symbol=symbol,
    signal=signal,
    ml_confidence=confidence,
    features=features,
    df=df,
    entry=entry,
    sl=sl,
    tp=tp
)

if not should_trade:
    print(f"[UNIFIED] {symbol}: {decision_reason}")
    continue  # ← SKIP THIS TRADE
    
# Only if unified decision approved, proceed:
place_sniper_entry(symbol, direction, LOT_SIZE, features, confidence, atr)
```

---

## Key Benefits

| Issue Before | Solution After |
|---|---|
| HTF blocks silently, ML still trades | HTF conflict → -35% penalty, subject to minimum confidence |
| FVG detected but not enforced | FVG out of zone → explicit BLOCKING factor |
| 20 filters, unclear precedence | 6 coordinated analyses with clear decision logic |
| No consensus requirement | Requires 2+ supporting factors + clean blocking filters |
| Confidence opaque | Final confidence displayed with full reasoning |
| Multiple "NO"s still trade | ONE blocking filter halts trade immediately |

---

## Output Example

When a trade is evaluated, you'll now see:

```
[UNIFIED DECISION] GBPUSD BUY
  HTF: HTF trend CONFLICTS: bearish vs signal buy
  FVG: FVG DETECTED (High Quality) + Liquidity Swept + PRICE IN ZONE
  Momentum: RSI(58) > 50 & MACD bullish
  Volume: VOLUME SPIKE detected
  Risk-Reward: Good RR (2.5:1) & ATR (0.00052)
  Regime: Regime: trend, Session: London & New York
  
  Blocking Filters: ['HTF_CONFLICT: HTF trend CONFLICTS: bearish vs signal buy']
  Supporting Factors: ['FVG: ...', 'MOMENTUM: ...', 'VOLUME: ...', 'RISK: ...', 'REGIME: ...']
  
  ➜ DECISION: BLOCKED: HTF_CONFLICT: HTF trend CONFLICTS: bearish vs signal buy
  Quality Score: 0.15
```

---

## Customization

To adjust decision thresholds, edit these functions:

1. **Minimum ML confidence:** Line in `compute_unified_decision()`: `if final_confidence < 0.70:`
   - Lower to 0.65 for more aggressive trading
   - Raise to 0.80 for strict mode

2. **Confidence adjustments:** Modify boost/penalty percentages in `compute_unified_decision()`
   - Currently: HTF aligned +15%, conflict -35%
   - Adjust to prioritize/deprioritize HTF

3. **Supporting factors required:** Line `if len(context.supporting_filters) < 2:`
   - Change `2` to `3` for stricter consensus
   - Change to `1` for more lenient

4. **Blocking filter definitions:** Each `analyze_*()` function has its own logic
   - Edit thresholds (e.g., FVG zone buffer, ATR minimums)

---

## Next Steps

1. **Monitor output** – Watch for `[UNIFIED DECISION]` messages in logs
2. **Verify blocks** – Check that "bad" setups are properly rejected
3. **Tune thresholds** – Adjust minimum confidence and factor requirements based on your edge
4. **Backtest** – Run strategy with new unified decision to measure improvement

All previous filters (`passes_trade_filters()`, `meta_filter()`, etc.) still run and provide defense-in-depth, but the unified decision is the PRIMARY gatekeeper before any trade execution.
