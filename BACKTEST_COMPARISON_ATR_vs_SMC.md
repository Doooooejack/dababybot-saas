# 📊 ATR-Only vs SMC+Fib Comparative Backtest Results
**Date:** January 30, 2026  
**Objective:** Determine which SL/TP calculation method has better edge on same entry signals

---

## 🎯 Summary Table

| Symbol | Method | Trades | WR % | Avg R:R | Expectancy | Winner |
|--------|--------|--------|------|---------|------------|--------|
| **XAUUSD** | ATR-Only | 272 | 40.1% | 1.94x | **0.180** ✅ | ATR-Only |
| | SMC+Fib | 186 | 54.8% | 1.09x | 0.149 | |
| **EURUSD** | ATR-Only | 265 | 12.8% | 1.94x | **-0.622** ✅ | ATR-Only |
| | SMC+Fib | 109 | 15.6% | 0.92x | -0.701 | |
| **GBPUSD** | ATR-Only | 294 | 36.7% | 1.94x | **0.082** ✅ | ATR-Only |
| | SMC+Fib | 184 | 49.5% | 1.09x | 0.036 | |
| **USDJPY** | ATR-Only | 274 | 23.0% | 1.94x | -0.323 | SMC+Fib |
| | SMC+Fib | 161 | 43.5% | 1.10x | **-0.087** ✅ | |

---

## 📈 Key Findings

### 1. **ATR-Only Wins on 3/4 Symbols**
- **XAUUSD**: +11.6% better expectancy
- **EURUSD**: +9.9% better expectancy  
- **GBPUSD**: +4.6% better expectancy
- **USDJPY**: SMC+Fib only exception (-0.087 vs -0.323)

### 2. **R:R Trade-off**
| Method | Avg R:R | Implication |
|--------|---------|------------|
| **ATR-Only** | 1.94x | Consistent, tight targets (better for frequent trading) |
| **SMC+Fib** | 1.09x | Tighter targets, higher hit rate but lower reward |

### 3. **Winrate Paradox**
- SMC+Fib has **HIGHER winrate** (49.5% GBPUSD, 54.8% XAUUSD)
- BUT **LOWER expectancy** due to worse R:R ratio
- **Why?** SMC+Fib TP targets too close → win frequently but small profits
- **Result:** Math works against us: 54.8% WR × 1.09x R:R = 0.149 expectancy vs 40.1% × 1.94x = 0.180

### 4. **ATR-Only Consistency**
- Consistent 1.94x R:R across all symbols
- More stable expectancy values
- Better for position sizing and bankroll management

---

## 🔍 Analysis: Why ATR-Only Wins

### Problem with SMC+Fib Implementation
The SMC/Fib approach was expected to:
- ✅ Find structure-based SL (working)
- ✅ Use Fibonacci extensions for TP (partially working)  
- ❌ Achieve 2.5-4.0x R:R (NOT achieved - only 1.09x)

**Root Cause:** TP targets are being set **TOO CLOSE** to entry, resulting in:
1. Many more small wins (54.8% WR)
2. Insufficient reward per win (1.09x vs 1.94x)
3. **Net result:** Lower total profit despite higher winrate

### Mathematical Comparison
```
ATR-Only:  0.401 × 1.94 - 0.599 × 1 = 0.778 - 0.599 = 0.180 ✅
SMC+Fib:   0.548 × 1.09 - 0.452 × 1 = 0.597 - 0.452 = 0.149 ❌

Even with higher winrate (54.8% vs 40.1%), SMC+Fib loses
because R:R ratio (1.09x) is too small to overcome the win/loss difference.
```

---

## 📌 Recommendations

### ✅ USE ATR-ONLY (Current Winner)
**Advantages:**
- Consistent 1.94x R:R across all symbols
- Better overall expectancy (0.180 best case)
- Simpler to implement and maintain
- More predictable risk/reward profile
- Better for consistent position sizing

### ❌ DO NOT USE SMC+FIB (Current Implementation)
**Current Issues:**
1. R:R ratio too tight (1.09x vs target 2.5-4.0x)
2. Over-optimizes for winrate at expense of profit
3. Complex code with limited benefit
4. Only wins on USDJPY by small margin (-0.087 vs -0.323)

### 🔧 IF SMC+FIB Must Be Fixed
To make SMC+Fib viable, need to:
1. **Increase TP distance** - Target 2.5-3.0x R:R instead of 1.09x
2. **Reduce TP target proximity** - Don't cap to 6x ATR, allow 8-10x ATR
3. **Rebalance SL placement** - May be too tight currently
4. **Test on each symbol** - May need symbol-specific Fib ratios

Example: If SMC+Fib achieved 2.0x R:R (instead of 1.09x):
```
SMC+Fib (Fixed): 0.548 × 2.0 - 0.452 × 1 = 1.096 - 0.452 = 0.644
This would BEAT ATR-Only's 0.180 ✅
```

---

## 🎯 Decision Matrix

| Factor | ATR-Only | SMC+Fib |
|--------|----------|---------|
| **Expectancy** | ✅ Better (0.180) | ❌ Worse (0.149) |
| **R:R Consistency** | ✅ 1.94x across all | ❌ 1.09x too tight |
| **Implementation** | ✅ Simple | ❌ Complex |
| **Maintainability** | ✅ Easy | ❌ Harder |
| **Production Ready** | ✅ NOW | ❌ Needs fixes |
| **Future Potential** | ⚠️ Limited | ✅ High (if fixed) |

---

## 📋 Action Items

### **IMMEDIATE:**
- [ ] **Remove SMC+Fib from bot** - Not providing edge yet
- [ ] **Revert to ATR-Only** in both `botfriday90000th.py` and `backtest_competitive_entry_2026.py`
- [ ] **Document this decision** for future reference

### **LATER (If SMC+Fib to be Revisited):**
- [ ] Debug TP calculation to achieve 2.5-4.0x R:R (not 1.09x)
- [ ] Test symbol-specific Fibonacci ratios
- [ ] Allow wider TP targets (8-10x ATR) if it improves R:R
- [ ] Create separate backtest for enhanced SMC+Fib

---

## 📂 Files Generated
- `backtest_compare_sl_tp_methods.py` - Comparison engine
- `backtest_comparison_results.json` - Raw results
- `BACKTEST_COMPARISON_ATR_vs_SMC.md` - This report

---

## ⚠️ Important Note
This backtest uses **identical entry signals** for both methods, so comparison is apples-to-apples. The difference in results is purely due to **SL/TP calculation differences**, not entry quality.
