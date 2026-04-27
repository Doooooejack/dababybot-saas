# Quick Reference: Signal Reconciliation Examples

## Real-World Scenarios

### Scenario A: Strong Consensus (All Green)
```
Market Condition: Clean bullish move on all timeframes

HTF Trend:     BUY  (4H: 20>50>200 EMA, HH/HL structure, score=5.2)
ML Signal:     BUY  (high confidence 0.82)
S&R Zone:      BUY  (clear demand zone detected)
5M BOS:        BUY  (higher lows, momentum confirmation)

═══════════════════════════════════════════════════════
Decision: Strong consensus: BUY (conf=0.79, active_sources=4)
Confidence: 0.79 | Risk_Adjustment: 0.7x (PROFIT SCALE)
═══════════════════════════════════════════════════════

Position: FULL TRADE SIZE × 0.7 = 0.35% risk
Rationale: All 4 sources aligned, very confident entry
```

---

### Scenario B: HTF Bullish, ML Wants to Sell
```
Market Condition: HTF uptrend but short-term overbought

HTF Trend:     BUY  (4H: solid bullish structure, score=4.8)
ML Signal:     SELL (confidence 0.72, detecting reversal)
S&R Zone:      SELL (in supply zone)
5M BOS:        SELL (detected break of structure)

Vote Summary:
- Buy votes:  0.35×0.80 + 0.20×0.30 = 0.3400
- Sell votes: 0.30×0.72 + 0.15×0.75 = 0.3270

═══════════════════════════════════════════════════════
Decision: HTF-dominant (ML conflict). Signal=BUY, 
           HTF_conf=0.80, reduced risk 0.6x
Confidence: 0.51 | Risk_Adjustment: 0.6x (CONFLICT)
═══════════════════════════════════════════════════════

Position: NORMAL TRADE SIZE × 0.6 = 0.3% risk
Rationale: HTF trend is strong, but ML disagrees
           Take smaller position, use tighter stops
Action:   - BUY with normal TP target
          - Use tighter SL (more risk-reward defined)
          - Exit if 5M BOS gets confirmed
```

---

### Scenario C: ML Reversal (High Confidence)
```
Market Condition: HTF bullish but ML predicts strong reversal

HTF Trend:     BUY    (4H: mild bullish, score=3.2)
ML Signal:     SELL   (confidence 0.78, strong reversal signal)
S&R Zone:      SELL   (approaching strong supply)
5M BOS:        NEUTRAL (no clear structure yet)

═══════════════════════════════════════════════════════
Decision: ML Reversal Trade (high ML conf=0.78). 
          Signal=SELL, reduced risk 0.7x
Confidence: 0.63 | Risk_Adjustment: 0.7x
═══════════════════════════════════════════════════════

Position: REVERSAL TRADE SIZE × 0.7 = 0.35% risk
Rationale: ML has high conviction of reversal
           HTF not confirming, but don't ignore ML
Action:   - SELL at market (against trend)
          - Very tight SL above HTF structure
          - Quick TP near S&R zone
          - Ready to exit if HTF holds support
```

---

### Scenario D: Conflicting Signals (Reject Trade)
```
Market Condition: Choppy, indecisive price action

HTF Trend:     BUY    (4H: weak, score=2.5)
ML Signal:     SELL   (low confidence 0.52)
S&R Zone:      NEUTRAL (between zones, ambiguous)
5M BOS:        NEUTRAL (no clear structure)

═══════════════════════════════════════════════════════
Decision: Insufficient consensus (conf=0.48, sources=1)
Confidence: 0.48 | Risk_Adjustment: 1.0x
═══════════════════════════════════════════════════════

❌ TRADE REJECTED - Wait for better alignment

Rationale: Only 1 source (weak HTF) supports trade
           Low ML confidence disagrees
           Not enough confluence for safe entry
Action:   - SKIP this opportunity
          - Monitor for clearer signal
          - Wait for either:
            * HTF to strengthen (stronger EMA alignment)
            * ML to increase confidence
            * S&R zone to become clear
            * 5M BOS to develop
```

---

### Scenario E: ML Confident Reversal (Weak HTF)
```
Market Condition: HTF barely bullish, but ML sees opportunity

HTF Trend:     BUY    (4H: weak, score=2.8, ema20 barely above 50)
ML Signal:     SELL   (confidence 0.76, detecting reversal)
S&R Zone:      SELL   (clear supply at current level)
5M BOS:        SELL   (detected break down)

═══════════════════════════════════════════════════════
Decision: ML Reversal Trade (high ML conf=0.76). 
          Signal=SELL, reduced risk 0.7x
Confidence: 0.60 | Risk_Adjustment: 0.7x
═══════════════════════════════════════════════════════

Position: REVERSAL SIZE × 0.7 = 0.35% risk
Rationale: ML is confident, 3/4 sources agree
           HTF is weak, so use reduced position
Action:   - SELL with very tight management
          - SL just above weak HTF structure
          - Quick TP at S&R level
          - Exit if HTF suddenly strengthens
```

---

### Scenario F: Weak Consensus (Marginal Approval)
```
Market Condition: Slight bullish lean, many mixed signals

HTF Trend:     BUY    (4H: moderate bullish, score=3.8)
ML Signal:     BUY    (moderate confidence 0.61)
S&R Zone:      NEUTRAL (weak signals)
5M BOS:        NEUTRAL (no clear structure)

Vote Summary:
- Buy votes:  0.35×0.63 + 0.30×0.61 = 0.4275
- Others:     Low confidence

═══════════════════════════════════════════════════════
Decision: Moderate Consensus: BUY (conf=0.56, sources=2)
Confidence: 0.56 | Risk_Adjustment: 0.85x
═══════════════════════════════════════════════════════

Position: NORMAL TRADE × 0.85 = 0.425% risk
Rationale: HTF and ML agree, but confidence is moderate
           S&R doesn't confirm, 5M isn't structured
Action:   - Take BUY with slightly reduced size
          - Use standard TP/SL
          - Monitor for confirmation candles
          - Don't hold if 5M starts to break structure
```

---

## Confidence Interpretation

| Confidence | Meaning | Trade Size | Management |
|---|---|---|---|
| 0.75-1.0 | **VERY HIGH** | Full 100% size | Hold positions longer, scale profits |
| 0.65-0.74 | **HIGH** | 100% size | Standard TP/SL, professional |
| 0.55-0.64 | **MODERATE** | 85-90% size | Tighter management, ready to exit |
| 0.40-0.54 | **LOW** | Skip or 50% size | Very tight stops, quick exits |
| <0.40 | **VERY LOW** | SKIP | Don't trade, wait for better setup |

---

## Risk Adjustment Interpretation

| Multiplier | Signal Divergence | Situation | Action |
|---|---|---|---|
| 0.5x | >0.4 | High conflict | Reduce size significantly, use stop loss |
| 0.6x | ~0.3 | HTF dominant | Trade with care, follow HTF |
| 0.7x | ~0.25 | Reversal mode | Reversal trades, tight management |
| 0.85x | ~0.15 | Moderate align | Standard position sizing |
| 0.7x | <0.1 | Very aligned | Increase position size for scaling |

---

## Decision Tree (Quick Logic)

```
START
  ↓
All 4 sources agree?
  ├─ YES → Confidence ≥ 0.65?
  │         ├─ YES → ✅ TRADE (100% size)
  │         └─ NO  → ❌ SKIP
  │
  └─ NO → HTF & ML agree?
          ├─ YES, Conf ≥ 0.55 → ✅ TRADE (100% size)
          │
          └─ NO → ML very confident? (≥0.75)
                  ├─ YES → ✅ TRADE (70% size, reversal)
                  │
                  └─ NO → HTF very confident? (≥0.60)
                          ├─ YES → ✅ TRADE (60% size, HTF-dom)
                          │
                          └─ NO → ❌ SKIP (low consensus)
```

---

## Monitoring Checklist

When reviewing trades, ask:

1. **Confluence**: How many sources agreed? (Ideal: 3-4)
2. **Conflict**: Did HTF and ML disagree? (Yellow flag if yes)
3. **Risk Adjustment**: Why was it reduced? (Conflict? Divergence?)
4. **Confidence**: Is it reasonable? (0.55+ for approval)
5. **Outcome**: If lost, was it a signal failure or execution issue?
   - Signal failure: Adjust weights or confidence thresholds
   - Execution issue: Check SL placement, slippage, timing

---

## Trading Rules of Thumb

✅ **GOOD SETUPS:**
- Confidence ≥ 0.65: Take full position
- Confidence 0.55-0.64: Take 85-90% position
- All sources aligned: Consider scaling up to 1.2x

❌ **AVOID:**
- Confidence < 0.50: Skip (no consensus)
- Divergence > 0.40: Reduce size to 50%
- Only 1 source + low confidence: Wait

⚠️ **BE CAREFUL:**
- HTF bullish + ML sell (watch S&R zone)
- Weak HTF + Strong ML (use tight stops)
- No S&R + No BOS (execution risk is high)

---

## Example: Following a Trade Through

### Entry Decision
```
HTF: Bullish (4H), ML: Bullish (0.70), S&R: Bullish, BOS: Developing
→ Confidence: 0.72, Risk_Adj: 0.85x
→ ✅ APPROVE - Take normal position
```

### Trade Management
```
After 10 pips profit:
- 5M BOS just broke down
- HTF still strong
- ML signal unchanged
→ Decision: Hold, HTF more reliable than short-term BOS
→ Action: Move SL to +5 pips (lock profit)
```

### Trade Close
```
After 50 pips profit:
- Price approaching target
- HTF showing fatigue (EMA 20 flattening)
- S&R resistance holding
→ Decision: Close at target, don't be greedy
→ Action: Full exit, log successful trade
```

---

**Last Updated:** 2025-12-08  
**System Version:** Advanced Signal Reconciliation v1.0
