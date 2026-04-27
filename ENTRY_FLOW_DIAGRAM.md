# Entry Decision Flow - Visual Guide

## Complete Entry Flow (BUY Example)

```
START: New candle formed on M15
│
├─ M15 CANDLE HIGH broken?
│  ├─ NO → WAIT FOR BOS
│  └─ YES → BOS DETECTED ✅
│
├─ [FILTER 1] PULLBACK RULE
│  ├─ Price pulling back 50-70% of impulse body?
│  ├─ OR tapping FVG zone?
│  ├─ NO → BLOCK ENTRY ❌
│  └─ YES → +12% CONFIDENCE ✅
│
├─ [FILTER 2] HTF DEMAND/SUPPLY
│  ├─ H4 BULLISH? (EMA21 > 50 > 200)
│  ├─ OR bouncing from swing low?
│  ├─ NO → BLOCK ENTRY ❌
│  └─ YES → +10% CONFIDENCE ✅
│
├─ [FILTER 3] ENTRY TF CONFIRMATION
│  ├─ M5 broke above recent high?
│  ├─ Rejection candle formed?
│  ├─ NO → BLOCK ENTRY ❌
│  └─ YES → +8 to +20% CONFIDENCE ✅
│
├─ FINAL CONFIDENCE CHECK
│  ├─ Confidence ≥ 70%?
│  ├─ Risk/Reward ≥ 1.5:1?
│  ├─ Volume confirmed?
│  ├─ NO → WAIT FOR MORE CONFIRMATION
│  └─ YES → SEND ENTRY SIGNAL ✅
│
└─ ENTRY EXECUTED
   Stop Loss: Below recent M5 low (or impulse low)
   Take Profit: Previous structure high or FVG target
```

---

## Confidence Buildup

```
Starting Confidence: 60%
│
├─ Pullback Rule: +12%
│  └─ → 72%
│
├─ HTF Filter: +10%
│  └─ → 82%
│
├─ Entry TF Confirmation:
│  ├─ Pin Bar: +20%    → 102% (capped)
│  ├─ Engulfing: +15%  → 97%
│  └─ BOS Only: +8%    → 90%
│
└─ FINAL CONFIDENCE: 85-100% ✅
```

---

## Decision Matrix

### BUY Entry Decision Table

| Pullback | HTF | Entry TF | Volume | Result |
|----------|-----|----------|--------|--------|
| ✅ | ✅ | ✅ | ✅ | **BUY** 🟢 |
| ✅ | ✅ | ❌ | ✅ | **WAIT** 🟡 |
| ✅ | ❌ | ✅ | ✅ | **WAIT** 🟡 |
| ✅ | ✅ | ✅ | ❌ | **CAUTIOUS** 🟡 |
| ❌ | ✅ | ✅ | ✅ | **SKIP** 🔴 |
| ✅ | ❌ | ❌ | ✅ | **SKIP** 🔴 |
| ❌ | ❌ | ✅ | ✅ | **SKIP** 🔴 |

🟢 = Execute entry  
🟡 = Wait for more confirmation  
🔴 = Skip setup entirely

---

## Multi-Timeframe Sync

### Data Flow
```
Live Price Feed
│
├─ M15 (Entry Timeframe)
│  ├─ BOS Detection
│  └─ Impulse Body Measurement
│
├─ M5 (Confirmation Timeframe)
│  ├─ BOS Detection
│  ├─ Rejection Candle Pattern
│  └─ Entry Trigger
│
├─ H4 (Trend Filter)
│  ├─ EMA Ribbon Analysis
│  ├─ Swing High/Low Detection
│  └─ Demand/Supply Zone
│
└─ D1 (Bias)
   └─ General Trend Direction
```

---

## Pattern Recognition Examples

### BUY Pullback Pattern
```
M15 Impulse:
   │
   ├─ H: 1.2050 (High)
   ├─ O: 1.2020
   ├─ C: 1.2045
   └─ L: 1.2010

Body: 25 pips
Pullback Zone: 1.2037-1.2045 (50-70% of 25)

✅ If price = 1.2040 → In zone, valid for BUY
❌ If price = 1.2050 → Not pulled back, SKIP
```

### M5 Rejection Candle (Pin Bar)
```
M5 Last 10 candles high: 1.2040

Rejection Candle:
   │
   ├─ H: 1.2050
   ├─ O: 1.2005
   ├─ C: 1.2008
   └─ L: 1.2000

Body: 3 pips
Upper Wick: 42 pips
Wick Ratio: 42/3 = 14 (> 2.5 required) ✅

✅ Strong rejection candle, BUY confirmed!
```

### H4 Bullish Confirmation
```
H4 EMA Values:
├─ EMA21: 1.2030
├─ EMA50: 1.2015
├─ EMA200: 1.2000
└─ Price: 1.2025

Check: 1.2030 > 1.2015 > 1.2000 ✅

✅ H4 is BULLISH, allow BUY
```

---

## Timing Diagram

```
M15 Timeframe (Main Entry TF):
═══════════════════════════════════
│ 12:00 │ 12:15 │ 12:30 │ 12:45 │
│   A   │   B   │   C   │   D   │
└───────┴───────┴───────┴───────┘
        ↑       ↑       ↑       ↑
        │       │       │       │
        │       │       Pullback│
        │       BOS     forming │
        │       (high)          │
        └─────────────────────────
              Impulse phase

M5 Timeframe (Confirmation TF):
═══════════════════════════════════════════════════════════════════════════════
│12:00│12:05│12:10│12:15│12:20│12:25│12:30│12:35│12:40│12:45│12:50│12:55│13:00│
│ a  │ b  │ c  │ d  │ e  │ f  │ g  │ h  │ i  │ j  │ k  │ l  │ m  │
└────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
                       ↑                           ↑
                       │                           │
                  M15 BOS candle            Pullback forms
                  (m=1-1)                   on M5 with pin

                                                  ↑
                                                  │
                                            M5 BOS + Pin
                                            → ENTRY SIGNAL
```

---

## Critical Rules Summary

### RULE 1: No Entry Without Pullback
```
BUY Price Action:
   High → (no pullback) → BUY ❌ BLOCKED
   High → (pullback 55%) → BUY ✅ ALLOWED
```

### RULE 2: No Counter-Trend Entry
```
H4 Bearish + BUY Signal = ❌ BLOCKED
(Unless price bouncing from demand support)

H4 Bullish + BUY Signal = ✅ ALLOWED
```

### RULE 3: No Entry Without M5 Confirmation
```
Pullback Valid + HTF OK + M5 No BOS = ❌ BLOCKED WAIT
Pullback Valid + HTF OK + M5 BOS = ✅ ENTRY READY

M5 BOS + No Pin Bar = ✅ OK (weaker)
M5 BOS + Pin Bar = ✅ OK (stronger +20%)
```

---

## Block Reasons (Why Entry Gets Rejected)

```
NO_PULLBACK_RULE
├─ Price outside 50-70% retracement zone
├─ No FVG tap detected
└─ Action: Wait for pullback completion

HTF_FILTER
├─ BUY: H4 not bullish and not at demand
├─ SELL: H4 not bearish and not at supply
└─ Action: Wait for H4 to confirm or price react from level

ENTRY_TF (NO_BUY_M5_BOS)
├─ M5 price hasn't broken above recent high
├─ OR M5 price at recent low (no BOS yet)
└─ Action: Wait for M5 breakout + confirmation

INSUFFICIENT_VOLUME
├─ Volume < 1.1x average
└─ Action: Wait for volume spike

RISK_REWARD_FAIL
├─ Risk/Reward ratio < 1.5:1
└─ Action: Recalculate TP or adjust SL
```

---

## Expected Trade Distribution

Out of 100 setups:

```
15 rejected: Fail pullback rule
10 rejected: Fail HTF filter
10 rejected: Fail entry TF confirmation
5 rejected: Fail volume check
5 rejected: Poor risk/reward
─────────────────────────────
55 accepted as valid entries
  ├─ 35 win (63% win rate)
  └─ 20 loss (37% loss rate)

Profit factor: (35 × 2R) / (20 × 1R) = 3.5
```

---

## Implementation Checklist

- [x] Pullback rule function created
- [x] HTF demand/supply function created
- [x] Entry TF confirmation function created
- [x] All three integrated into compute_unified_decision()
- [x] Confidence boosts implemented
- [x] Blocking logic implemented
- [x] Applied to both BUY and SELL
- [x] Documentation complete

Ready to test! 🚀
