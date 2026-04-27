"""
LIQUIDITY SWEEP ENGINE - ARCHITECTURE & WORKFLOW DIAGRAM
=========================================================


╔════════════════════════════════════════════════════════════════════════════╗
║                    COMPLETE TRADING SETUP WORKFLOW                         ║
╚════════════════════════════════════════════════════════════════════════════╝


STEP 1: ANALYZE MARKET STRUCTURE
╔═══════════════════════════════════════════════════════════════════════════╗
│                                                                             │
│  Historical Candles (OHLC Data)                                           │
│  ├─ 100 candles (or more)                                                │
│  └─ Timeframe: M1, M5, M15, H1, etc.                                     │
│                                                                             │
│          ↓↓↓                                                              │
│                                                                             │
│  [Identify Swing Points]                                                  │
│  ├─ find_last_swing_high() → Bullish reference                          │
│  ├─ find_last_swing_low()  → Bearish reference                          │
│  └─ swing_high()/swing_low() → Mechanical detection (3-candle pattern)  │
│                                                                             │
│          ↓↓↓                                                              │
│                                                                             │
│  Result: MARKET BIAS ESTABLISHED                                          │
│  • Swing High Level (SH)                                                 │
│  • Swing Low Level (SL)                                                  │
│  • Which is more recent? (determines bias)                               │
│                                                                             │
╚═══════════════════════════════════════════════════════════════════════════╝


STEP 2: DETECT STRUCTURE BREAK (BOS or CHoCH)
╔═══════════════════════════════════════════════════════════════════════════╗
│                                                                             │
│  [Check Current Close vs Swing Levels]                                    │
│                                                                             │
│  IF BULLISH BIAS:                                                         │
│  ┌─────────────────────────────────────────────────────────┐             │
│  │ detect_bullish_bos()                                    │             │
│  │ → Does current_close > last_swing_high?                │             │
│  │ → YES = BOS (Continuation signal)                       │             │
│  └─────────────────────────────────────────────────────────┘             │
│                         ↓                                                │
│  ┌─────────────────────────────────────────────────────────┐             │
│  │ detect_bullish_choch()                                  │             │
│  │ → Look back for "lower highs" pattern                   │             │
│  │ → Does current_close > last_lower_high?                │             │
│  │ → YES = CHoCH (Reversal signal)                         │             │
│  └─────────────────────────────────────────────────────────┘             │
│                                                                             │
│  IF BEARISH BIAS:                                                         │
│  ┌─────────────────────────────────────────────────────────┐             │
│  │ detect_bearish_bos()                                    │             │
│  │ → Does current_close < last_swing_low?                 │             │
│  │ → YES = BOS (Continuation signal)                       │             │
│  └─────────────────────────────────────────────────────────┘             │
│                         ↓                                                │
│  ┌─────────────────────────────────────────────────────────┐             │
│  │ detect_bearish_choch()                                  │             │
│  │ → Look back for "higher lows" pattern                   │             │
│  │ → Does current_close < last_higher_low?                │             │
│  │ → YES = CHoCH (Reversal signal)                         │             │
│  └─────────────────────────────────────────────────────────┘             │
│                                                                             │
│  Result: STRUCTURE BREAK SIGNAL                                           │
│  • BOS = Continuation (quality: moderate)                               │
│  • CHoCH = Reversal (quality: high) ← PREFERRED                         │
│                                                                             │
╚═══════════════════════════════════════════════════════════════════════════╝


STEP 3: FIND FAIR VALUE GAP (ONLY AFTER STRUCTURE BREAK)
╔═══════════════════════════════════════════════════════════════════════════╗
│                                                                             │
│  [Look at 3 consecutive candles AFTER structure break]                    │
│                                                                             │
│  Bullish FVG Pattern:                                                     │
│  ┌─────────────────────────────────────────────────────────┐             │
│  │  C1      C2      C3                                     │             │
│  │  ├──┤    ├──┤    ├──┤                                   │             │
│  │  └──┘    └──┘    └──┘                                   │             │
│  │                                                          │             │
│  │  C1.high = 1.199                                        │             │
│  │  C2 = (middle candle)                                  │             │
│  │  C3.low = 1.200                                         │             │
│  │                                                          │             │
│  │  IF C1.high < C3.low → BULLISH FVG EXISTS              │             │
│  │  FVG = [1.199, 1.200]  (the gap)                       │             │
│  └─────────────────────────────────────────────────────────┘             │
│                                                                             │
│  Bearish FVG Pattern:                                                     │
│  ┌─────────────────────────────────────────────────────────┐             │
│  │  C1      C2      C3                                     │             │
│  │  ├──┤    ├──┤    ├──┤                                   │             │
│  │  └──┘    └──┘    └──┘                                   │             │
│  │                                                          │             │
│  │  C1.low = 1.201                                         │             │
│  │  C2 = (middle candle)                                  │             │
│  │  C3.high = 1.200                                        │             │
│  │                                                          │             │
│  │  IF C1.low > C3.high → BEARISH FVG EXISTS              │             │
│  │  FVG = [1.200, 1.201]  (the gap)                       │             │
│  └─────────────────────────────────────────────────────────┘             │
│                                                                             │
│  KEY RULE: FVG must exist AFTER structure break                          │
│  • Old FVGs = ignored                                                    │
│  • FVGs before structure = ignored                                       │
│  • Only count FVGs found within 5 candles after structure                │
│                                                                             │
│  Result: FVG BOUNDARIES                                                   │
│  • FVG.low = lower bound                                                │
│  • FVG.high = upper bound                                               │
│                                                                             │
╚═══════════════════════════════════════════════════════════════════════════╝


STEP 4: CALCULATE HIGH-PROBABILITY ENTRY ZONE (50%-75%)
╔═══════════════════════════════════════════════════════════════════════════╗
│                                                                             │
│  [Do NOT enter at the whole FVG - that's low probability]                │
│                                                                             │
│  BULLISH FVG:                                                             │
│  ┌─────────────────────────────────────────────────────────┐             │
│  │  FVG: [1.1990, 1.2010]  (total size = 0.0020)          │             │
│  │                                                          │             │
│  │  50% zone = 1.1990 + (0.5 × 0.0020) = 1.2000           │             │
│  │  75% zone = 1.2010                                      │             │
│  │                                                          │             │
│  │  ENTRY ZONE = [1.2000, 1.2010]  ← Sweet spot!          │             │
│  │  Mid-point  = 1.2005              ← Optimal entry      │             │
│  │                                                          │             │
│  │  Zone size: 0.0010 (50% of original gap)               │             │
│  └─────────────────────────────────────────────────────────┘             │
│                                                                             │
│  BEARISH FVG:                                                             │
│  ┌─────────────────────────────────────────────────────────┐             │
│  │  FVG: [1.1990, 1.2010]  (total size = 0.0020)          │             │
│  │                                                          │             │
│  │  25% zone = 1.2010 - (0.5 × 0.0020) = 1.2000           │             │
│  │  50% zone = 1.1990                                      │             │
│  │                                                          │             │
│  │  ENTRY ZONE = [1.1990, 1.2000]  ← Sweet spot!          │             │
│  │  Mid-point  = 1.1995              ← Optimal entry      │             │
│  │                                                          │             │
│  │  Zone size: 0.0010 (50% of original gap)               │             │
│  └─────────────────────────────────────────────────────────┘             │
│                                                                             │
│  KEY RULE: This is your EDGE                                             │
│  • Do NOT enter at top of bullish FVG                                   │
│  • Do NOT enter at bottom of bearish FVG                                │
│  • Optimal entry = mid-point ± small buffer                             │
│                                                                             │
│  Result: ENTRY ZONE DEFINED                                              │
│  • Zone boundaries                                                       │
│  • Mid-point (recommended entry)                                        │
│  • Zone size (helps with risk calculation)                              │
│                                                                             │
╚═══════════════════════════════════════════════════════════════════════════╝


STEP 5: CONFIRM ENTRY (INSIDE ENTRY ZONE ONLY)
╔═══════════════════════════════════════════════════════════════════════════╗
│                                                                             │
│  [Check if current price is in entry zone]                               │
│                                                                             │
│  price_in_entry_zone() → Is price within [zone_low, zone_high]?         │
│                                                                             │
│  IF YES:                                                                  │
│  └─ Look for Confirmation Candles                                        │
│                                                                             │
│     Bullish Confirmation:                                                │
│     ┌────────────────────────────────────────────────────┐              │
│     │ Previous Candle: bearish (close < open)           │              │
│     │ Current Candle:  bullish (close > open)           │              │
│     │                                                     │              │
│     │ bullish_engulfing() →                             │              │
│     │ Current.open < Previous.close AND                │              │
│     │ Current.close > Previous.open                    │              │
│     │                                                     │              │
│     │ ✓ REQUIRED: Engulfing pattern                     │              │
│     │ ✓ OPTIONAL: Displacement candle (large body)     │              │
│     │ ✓ OPTIONAL: Volume expansion                      │              │
│     └────────────────────────────────────────────────────┘              │
│                                                                             │
│     Bearish Confirmation:                                               │
│     ┌────────────────────────────────────────────────────┐              │
│     │ Previous Candle: bullish (close > open)           │              │
│     │ Current Candle:  bearish (close < open)           │              │
│     │                                                     │              │
│     │ bearish_engulfing() →                             │              │
│     │ Current.open > Previous.close AND                │              │
│     │ Current.close < Previous.open                    │              │
│     │                                                     │              │
│     │ ✓ REQUIRED: Engulfing pattern                     │              │
│     │ ✓ OPTIONAL: Displacement candle (large body)     │              │
│     │ ✓ OPTIONAL: Volume expansion                      │              │
│     └────────────────────────────────────────────────────┘              │
│                                                                             │
│  Result: ENTRY READY SIGNAL                                              │
│  If all checks pass → entry_ready = True                               │
│                                                                             │
╚═══════════════════════════════════════════════════════════════════════════╝


FINAL OUTPUT: TRADE SETUP
╔═══════════════════════════════════════════════════════════════════════════╗
│                                                                             │
│  execute_sweep_to_entry_workflow() returns:                              │
│                                                                             │
│  {                                                                         │
│    'sweep_detected': bool,                                               │
│    'structure_detected': 'BOS' | 'CHoCH' | None,  ← Signal type         │
│    'fvg_detected': bool,                          ← Gap exists          │
│    'entry_zone': {                                                       │
│      'entry_zone_low': float,    ← Min entry price                       │
│      'entry_zone_high': float,   ← Max entry price                       │
│      'zone_size': float,         ← Entry range                           │
│      'mid_point': float          ← Optimal entry ⭐              │
│    },                                                                     │
│    'entry_ready': bool,          ← GO/NO-GO SIGNAL ⭐⭐        │
│    'details': {...}              ← Additional info                       │
│  }                                                                         │
│                                                                             │
│  IF entry_ready == True:                                                 │
│  ✅ READY TO TRADE!                                                      │
│                                                                             │
│  Trade Parameters:                                                       │
│  • Entry: entry_zone['mid_point']                                       │
│  • Stop Loss: Below last swing low (bullish) / Above swing high (bearish)│
│  • Take Profit: Above FVG high (bullish) / Below FVG low (bearish)     │
│  • Signal Quality: CHoCH > BOS                                           │
│                                                                             │
╚═══════════════════════════════════════════════════════════════════════════╝


INTEGRATION WITH botfriday6000th.py
╔═══════════════════════════════════════════════════════════════════════════╗
│                                                                             │
│  Your bot flow:                                                           │
│                                                                             │
│  1. Main Loop                                                             │
│     ↓                                                                     │
│  2. Get Price Data (OHLC)                                               │
│     ↓                                                                     │
│  3. Call execute_sweep_to_entry_workflow(candles, ...)                  │
│     ↓                                                                     │
│  4. Check result['entry_ready']                                         │
│     ├─ If TRUE  → Execute entry logic                                  │
│     └─ If FALSE → Wait for next candle                                 │
│     ↓                                                                     │
│  5. Manage Position                                                      │
│     └─ Use entry_zone['mid_point'] for optimal entry                   │
│     └─ Use swing levels for stop loss                                  │
│     └─ Use FVG bounds for take profit                                  │
│                                                                             │
╚═══════════════════════════════════════════════════════════════════════════╝


CRITICAL RULES ENFORCED IN CODE
╔═══════════════════════════════════════════════════════════════════════════╗
│                                                                             │
│  1. SWEEP RULE:                                                           │
│     "A sweep is NOT confirmed until price re-enters the range"           │
│     → sweep_reentry_confirmed() checks for this                          │
│                                                                             │
│  2. STRUCTURE RULE:                                                       │
│     "Market bias defined mechanically (swing points), not emotionally"   │
│     → swing_high/low() enforce 3-candle pattern                         │
│                                                                             │
│  3. FVG RULE:                                                             │
│     "Only FVGs created AFTER BOS/CHoCH count"                            │
│     → detect_fvg_after_structure() enforces this                         │
│                                                                             │
│  4. ENTRY ZONE RULE:                                                      │
│     "Do NOT enter at the whole FVG (low probability)"                    │
│     → calculate_entry_zone() restricts to 50%-75%                        │
│                                                                             │
│  5. CONFIRMATION RULE:                                                    │
│     "Engulfing pattern REQUIRED, displacement+volume OPTIONAL"           │
│     → validate_entry_confirmation() enforces this                        │
│                                                                             │
│  6. PREFERENCE RULE:                                                      │
│     "CHoCH > BOS (CHoCH trades are higher quality)"                      │
│     → Result includes structure_detected for filtering                   │
│                                                                             │
╚═══════════════════════════════════════════════════════════════════════════╝


TIME-BASED ANALYSIS FLOW
╔═══════════════════════════════════════════════════════════════════════════╗
│                                                                             │
│  t₀   t₁   t₂   t₃   t₄   t₅   t₆   t₇   t₈   (candle times)            │
│  ├────┼────┼────┼────┼────┼────┼────┼────┼────                          │
│                       ▲                                                   │
│                   Swing High Detected                                     │
│                                                                             │
│                               ▲                                           │
│                            BOS/CHoCH                                      │
│                                                                             │
│                                   ▲              ▲              ▲        │
│                                   C1             C2             C3       │
│                                   FVG DETECTION (C1.high < C3.low)       │
│                                                                             │
│                                                        ▲ Current Price   │
│                                            In Entry Zone?                 │
│                                                                             │
│                                                              ▲ Entry     │
│                                               Engulfing + Confirmation   │
│                                                                             │
│  Total time: Usually 5-10 candles for full setup                        │
│                                                                             │
╚═══════════════════════════════════════════════════════════════════════════╝


ERROR HANDLING & FALLBACKS
╔═══════════════════════════════════════════════════════════════════════════╗
│                                                                             │
│  All functions safe:                                                      │
│  • Check results for None before using                                  │
│  • DataFrame/dict handling automatic                                     │
│  • Import has fallback functions (won't crash bot)                      │
│  • No division by zero errors                                            │
│  • All edge cases handled                                                │
│                                                                             │
│  If something returns None/False:                                         │
│  → Check candle data has 'open', 'high', 'low', 'close'                 │
│  → Verify lookback period is appropriate                                 │
│  → Run test_liquidity_sweep_engine.py to validate setup                 │
│                                                                             │
╚═══════════════════════════════════════════════════════════════════════════╝


═════════════════════════════════════════════════════════════════════════════

This diagram shows the COMPLETE flow from raw candles to trade execution.

Every step is automated and rule-based.
Every rule is falsifiable and mechanical.
No guessing. No emotion. Pure trading logic. 🚀

═════════════════════════════════════════════════════════════════════════════
"""
