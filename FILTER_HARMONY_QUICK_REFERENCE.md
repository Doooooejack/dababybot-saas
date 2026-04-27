# ⚡ FILTER HARMONY QUICK-REFERENCE

## TL;DR: Your Filters Don't Argue ✅

All filters work **independently** checking **different aspects** of price action:

| # | Filter | Checks | Blocks | Safe? |
|---|--------|--------|--------|-------|
| 1 | ML Signal | Prediction | No | ✅ |
| 2 | Trend Logic (NEW) | Structure + Momentum | Maybe | ✅ |
| 3 | Regime | Trend vs Range | Yes | ✅ |
| 4 | Session | Trading Hours | Yes | ✅ |
| 5 | Spread | Liquidity | Yes | ✅ |
| 6 | Daily Loss | Account Safety | Yes | ✅ |
| 7 | Displacement | Real Movement | Yes | ✅ |
| 8 | Cooldown | Stacking Prevention | Yes | ✅ |
| 9 | Entry | Pattern + Confidence | Yes | ✅ |

---

## How They Work Together

### The GOOD Redundancy ✨
- **Trend Logic + Regime Filter** = Two independent trend checks
  - Trend: Structural (HH/HL, LL/LH)
  - Regime: Oscillator-based (EMA, MACD)
  - If both fail = No real trend (GOOD)

- **Trend Logic + Displacement** = Two momentum checks
  - Trend: Candle body size (1.3× average)
  - Displacement: Range expansion (ATR)
  - If both fail = Low momentum (GOOD)

### The EFFICIENCY 🚀
Filters stop checking early:
```
ML says BUY → Trend fails → STOP (no point checking displacement)
           → Trend OK → Check Displacement
                     → Displacement fails → STOP
                     → Displacement OK → Continue...
```

This saves CPU while being safer.

---

## Setup Modes

### 🟢 Mode 1: ADVISORY (Recommended)
```python
RUN_ADVANCED_TREND_LOGIC = True
BLOCK_ON_TREND_FAILURE = False
```
- Get better SL/TP from trend logic
- Don't block trades if logic fails
- Other filters still protect you
- **Best for**: Live trading

### 🟠 Mode 2: STRICT
```python
RUN_ADVANCED_TREND_LOGIC = True
BLOCK_ON_TREND_FAILURE = True
```
- Trend logic acts like regime filter
- Must pass trend logic to trade
- Higher barrier, fewer trades
- **Best for**: Conservative traders

### ⚪ Mode 3: OFF
```python
RUN_ADVANCED_TREND_LOGIC = False
```
- Use only original filters
- No trend logic overhead
- **Best for**: Legacy compatibility

---

## What If Something Goes Wrong?

### I'm getting NO trades 😟
```python
# Check filter health:
from filter_conflict_monitor import check_filter_health
check_filter_health("EURUSD.m")

# Suggestion:
from filter_conflict_monitor import get_filter_suggestion
print(get_filter_suggestion("EURUSD.m"))

# Usually: One filter is too strict
# Solution: Relax that filter's threshold
```

### Two filters seem to contradict 🤔
```python
# Check for actual conflicts:
from filter_conflict_monitor import get_filter_conflicts
conflicts = get_filter_conflicts("EURUSD.m")
if conflicts:
    for c in conflicts:
        print(f"{c['type']}: {c['message']}")
        print(f"Fix: {c['recommendation']}")

# Usually: Not a real conflict, just both failing on choppy price
# Solution: Both failing together is SAFE (no false entry)
```

---

## Filter Decision Flowchart

```
┌─ Is there an ML signal?
│  └─ No → Skip symbol
│  └─ Yes ↓
├─ Advanced Trend Logic (if enabled)
│  └─ Fails → Log warning
│           └─ Block mode ON? → Skip symbol
│           └─ Block mode OFF? → Continue
│  └─ Passes → Continue (better SL/TP) ↓
├─ Regime filter (GBPUSD, AUDUSD only)
│  └─ Fails → Skip symbol
│  └─ Passes ↓
├─ Session filter
│  └─ Fails → Skip symbol
│  └─ Passes ↓
├─ Spread filter
│  └─ Fails → Skip symbol
│  └─ Passes ↓
├─ Daily loss cap
│  └─ Fails → Skip symbol
│  └─ Passes ↓
├─ Displacement filter
│  └─ Fails → Skip symbol
│  └─ Passes ↓
├─ Cooldown filter
│  └─ Fails → Skip symbol
│  └─ Passes ↓
├─ Trade entry filter
│  └─ Fails → Skip symbol
│  └─ Passes ↓
└─ ✅ PLACE TRADE
```

---

## Real-Time Monitoring

```python
# In your bot's main loop, after each filter:
record_filter(symbol, "TREND_LOGIC", passed, reason)
record_filter(symbol, "DISPLACEMENT_FILTER", passed, reason)
# ... etc

# Every hour, check health:
if time_to_check_health():
    check_filter_health()  # Print report
    print(get_filter_suggestion("EURUSD.m"))
```

Monitor will tell you:
- ✅ If all filters are healthy (balanced rejection rate)
- ⚠️ If one filter is too strict (rejecting too many)
- 🔴 If there's a real conflict (very rare)

---

## TLDR: Should I Worry? 🤔

**NO** ✅

✓ All filters have been validated  
✓ No logical conflicts  
✓ Redundancy is intentional (safety)  
✓ Real-time monitoring catches issues  
✓ Multiple configuration modes available  

**They work together beautifully.** 🎵

---

**Status**: ✅ All integrated and tested  
**Last Updated**: January 9, 2026
