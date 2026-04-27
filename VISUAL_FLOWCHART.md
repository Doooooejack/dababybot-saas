# VISUAL DECISION FLOWCHART - 7 RULES VALIDATION

```
╔════════════════════════════════════════════════════════════════════════════╗
║                     UNIFIED TRADE DECISION START                          ║
║                  (Your existing bot logic runs first)                      ║
╚════════════════════════════════════════════════════════════════════════════╝
                                    ↓
╔════════════════════════════════════════════════════════════════════════════╗
║  Step 1: Run all direction analysis (HTF, FVG, Momentum, etc.)           ║
║          Get BUY score vs SELL score                                      ║
╚════════════════════════════════════════════════════════════════════════════╝
                                    ↓
        ┌───────────────────────────────────────────────────────┐
        │ Buy > Sell ?   OR   Sell > Buy ?                      │
        └───────────────────────────────────────────────────────┘
                        ↙ yes              ↘ yes
                       /                      \
                  BUY direction          SELL direction
                       ↓                       ↓
╔════════════════════════════════════════════════════════════════════════════╗
║                    *** NEW: 7 RULES VALIDATION GATE ***                  ║
║        (This is where the new checks happen - before order!)              ║
╚════════════════════════════════════════════════════════════════════════════╝
                                    ↓
        ┌─────────────────────────────────────────────────────────┐
        │ RULE 1: HTF BIAS CHECK                                  │
        │   BUY:  HH+HL? OR impulse 1.5x? OR above equilibrium? │
        │   SELL: LL+LH? OR impulse 1.5x? OR below equilibrium? │
        │   ❌ Ranging HTF = BLOCK                               │
        └─────────────────────────────────────────────────────────┘
              ✅ PASS → continue        ❌ FAIL → BLOCK TRADE
                  ↓
        ┌─────────────────────────────────────────────────────────┐
        │ RULE 2: LOCATION CHECK                                  │
        │   BUY:  In demand zone? OR 50-61.8% retrace?          │
        │   SELL: In supply zone? OR 50-61.8% retrace?          │
        │   ❌ At highs/lows or mid-range = BLOCK               │
        └─────────────────────────────────────────────────────────┘
              ✅ PASS → continue        ❌ FAIL → BLOCK TRADE
                  ↓
        ┌─────────────────────────────────────────────────────────┐
        │ RULE 3: M5 STRUCTURE SHIFT                              │
        │   BUY:  Higher Low + Break of previous high?          │
        │   SELL: Lower High + Break of previous low?           │
        │   ❌ No structure = BLOCK                              │
        └─────────────────────────────────────────────────────────┘
              ✅ PASS → continue        ❌ FAIL → BLOCK TRADE
                  ↓
        ┌─────────────────────────────────────────────────────────┐
        │ ⚡ RULE 4: EXPANSION CANDLE (CRITICAL)                │
        │   Must have ALL:                                         │
        │   • Range ≥ 1.5x last 10 avg                          │
        │   • Close near high (BUY) or low (SELL)               │
        │   • No compression/chop                                 │
        │   ❌ NO EXPANSION = IMMEDIATE BLOCK ⚡               │
        └─────────────────────────────────────────────────────────┘
              ✅ PASS → continue        ❌ FAIL → BLOCK TRADE
                  ↓
        ┌─────────────────────────────────────────────────────────┐
        │ RULE 5: HARD FILTERS                                    │
        │   ❌ Ranging 30+ min?                                   │
        │   ❌ Huge impulse against direction?                    │
        │   ❌ News in 15 min?                                    │
        │   ❌ Spread > 1.5x normal?                             │
        └─────────────────────────────────────────────────────────┘
              ✅ PASS → continue        ❌ FAIL → BLOCK TRADE
                  ↓
        ┌─────────────────────────────────────────────────────────┐
        │ RULE 6: STOP LOSS VALIDATION                            │
        │   BUY:  SL < Entry, based on structure?               │
        │   SELL: SL > Entry, based on structure?               │
        │   ❌ Invalid or too tight = BLOCK                      │
        └─────────────────────────────────────────────────────────┘
              ✅ PASS → continue        ❌ FAIL → BLOCK TRADE
                  ↓
        ┌─────────────────────────────────────────────────────────┐
        │ RULE 7: TAKE PROFIT VALIDATION                          │
        │   Reward ≥ Risk × 2.0 (2R minimum)?                    │
        │   ❌ TP too close = BLOCK                              │
        └─────────────────────────────────────────────────────────┘
              ✅ PASS → continue        ❌ FAIL → BLOCK TRADE
                  ↓
╔════════════════════════════════════════════════════════════════════════════╗
║                   ✅ ALL 7 RULES PASSED - TRADE APPROVED                 ║
║                                                                             ║
║     Execute Order:                                                         ║
║     • Entry: [calculated price]                                           ║
║     • SL: [structure-based stop]                                          ║
║     • TP: [2R+ target]                                                    ║
║     • Lot: [calculated size]                                              ║
╚════════════════════════════════════════════════════════════════════════════╝
                                    ↓
                           Order Placed to Broker

════════════════════════════════════════════════════════════════════════════════

                           ❌ FAIL SCENARIOS ❌

If ANY rule fails, you see output like:

    ❌ BLOCKED: HTF ranging | Price mid-range | No expansion

And the order is NOT placed. Simple as that.

════════════════════════════════════════════════════════════════════════════════
```

---

## RULE PRIORITY & IMPORTANCE

```
┌──────┬──────────────────────────┬──────────────┬──────────────────────┐
│ Rule │ Name                     │ Importance   │ Block Type           │
├──────┼──────────────────────────┼──────────────┼──────────────────────┤
│  1   │ HTF Bias                 │ CRITICAL ⚡  │ Direction conflict   │
│  2   │ Location                 │ CRITICAL ⚡  │ Wrong entry zone     │
│  3   │ M5 Structure             │ HIGH         │ No BOS/structure     │
│  4   │ Expansion Candle         │ CRITICAL ⚡  │ Too small/chop       │
│  5   │ Hard Filters             │ CRITICAL ⚡  │ Bad conditions       │
│  6   │ SL Validation            │ HIGH         │ SL malformed         │
│  7   │ TP Validation            │ MEDIUM       │ Risk not worth it    │
└──────┴──────────────────────────┴──────────────┴──────────────────────┘

⚡ = If fails, trade is IMMEDIATELY blocked
```

---

## EXAMPLE: TRADE JOURNEY

### ✅ SCENARIO 1: ALL RULES PASS

```
Entry: EURUSD BUY
├─ Rule 1 (HTF Bias): ✅ PASS - HH+HL + above equilibrium
├─ Rule 2 (Location): ✅ PASS - In 50-61.8% retrace zone
├─ Rule 3 (M5 Struct): ✅ PASS - Higher Low + BOS confirmed
├─ Rule 4 (Expansion): ✅ PASS - 1.82x range, strong body
├─ Rule 5 (Filters):   ✅ PASS - No news, normal spread, trending
├─ Rule 6 (SL):        ✅ PASS - 20 pips below structure
└─ Rule 7 (TP):        ✅ PASS - 2.40:1 ratio

→ TRADE PLACED ✅
Entry: 1.1500, SL: 1.1480, TP: 1.1548
```

### ❌ SCENARIO 2: EXPANSION FAILS (CRITICAL)

```
Entry: GBPUSD SELL
├─ Rule 1 (HTF Bias): ✅ PASS - LL+LH confirmed
├─ Rule 2 (Location): ✅ PASS - In supply zone
├─ Rule 3 (M5 Struct): ✅ PASS - Lower High + BOS
├─ Rule 4 (Expansion): ❌ FAIL - 1.23x < 1.5x (chop!)
├─ Rule 5 (Filters):   ✅ PASS - Conditions OK
├─ Rule 6 (SL):        ✅ PASS - 15 pips above
└─ Rule 7 (TP):        ✅ PASS - 2.50:1 ratio

⚠️  NO EXPANSION = NO TRADE
→ ORDER REJECTED ❌
Reason: Candle too small, likely choppy consolidation
```

### ❌ SCENARIO 3: HTF CONFLICTS

```
Entry: USDJPY BUY
├─ Rule 1 (HTF Bias): ❌ FAIL - LL+LH (bearish) vs BUY signal
├─ Rule 2 (Location): ✅ PASS - In demand zone
├─ Rule 3 (M5 Struct): ✅ PASS - HH+HL confirmed
├─ Rule 4 (Expansion): ✅ PASS - 1.65x expansion
├─ Rule 5 (Filters):   ✅ PASS - All filters pass
├─ Rule 6 (SL):        ✅ PASS - 18 pips below
└─ Rule 7 (TP):        ✅ PASS - 2.30:1 ratio

⚠️  HTF CONFLICTS WITH BUY SIGNAL
→ ORDER REJECTED ❌
Reason: HTF showing downtrend, waiting for trend change first
```

### ❌ SCENARIO 4: HARD FILTER BLOCKS

```
Entry: AUDUSD SELL
├─ Rule 1 (HTF Bias): ✅ PASS - LL+LH confirmed
├─ Rule 2 (Location): ✅ PASS - In supply zone
├─ Rule 3 (M5 Struct): ✅ PASS - Lower High + BOS
├─ Rule 4 (Expansion): ✅ PASS - 1.58x expansion
├─ Rule 5 (Filters):   ❌ FAIL - News (CPI) in 8 minutes
├─ Rule 6 (SL):        ✅ PASS - 12 pips above
└─ Rule 7 (TP):        ✅ PASS - 2.80:1 ratio

⚠️  NEWS WITHIN 15 MINUTES - TOO RISKY
→ ORDER REJECTED ❌
Reason: High volatility expected from economic event
```

---

## DECISION LOGIC (PSEUDOCODE)

```
function validate_7_rules(symbol, df_h4, df_m5, direction, entry, sl, tp):
    
    // Check each rule
    rule_1_pass = check_htf_bias(df_h4, direction)
    rule_2_pass = check_location(df_h4, direction)
    rule_3_pass = check_m5_structure(df_m5, direction)
    rule_4_pass = check_expansion(df_m5, direction)  // CRITICAL
    rule_5_pass = check_hard_filters(df_m5)
    rule_6_pass = check_sl(entry, sl, direction)
    rule_7_pass = check_tp(entry, sl, tp, direction)
    
    // All must pass
    if rule_1_pass AND rule_2_pass AND rule_3_pass AND 
       rule_4_pass AND rule_5_pass AND rule_6_pass AND rule_7_pass:
        return TRADE_APPROVED
    else:
        return TRADE_BLOCKED
```

---

## KEY INSIGHT

**Before these rules:** Your bot might enter anywhere, anytime
**After these rules:** Your bot only enters high-probability setups

The rules eliminate the "bad setups" that lose money. You trade less, but win more.
