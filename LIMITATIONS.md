# BOT LIMITATIONS & ROADMAP

**Current Version**: 8.5/10  
**Target Version**: 9.5/10  
**Last Updated**: December 9, 2025

---

## KNOWN LIMITATIONS

### ❌ Code Organization
- **Duplicate `get_htf_trend()` functions** (FIXED in v8.5)
  - Previously at lines 6,155 and 23,006—consolidation complete
  - **Status**: ✅ RESOLVED

- **Multiple main trading loops** 
  - `main_trading_loop()` at line 7,241
  - `main_loop()` at line 14,022
  - `run_live_trading_loop()` at line 18,514 (currently active)
  - **Recommendation**: Consolidate all into single `run_live_trading_loop()`
  - **Impact**: ~300 lines of redundant code

### ❌ Testing & Validation
- **No unit tests** for core strategies
  - Multi-entry voting system untested in isolation
  - Risk management functions lack test coverage
  - **Status**: Unit test suite created (tests/test_multi_entry.py) with 20+ test cases
  - **Next**: Run `pytest tests/test_multi_entry.py -v`

- **Multi-entry system not yet backtested**
  - No historical performance comparison (single-ML vs 3-strategy)
  - Confidence thresholds not validated on 6+ months of data
  - Consensus voting win-rate not measured
  - **Recommendation**: Run 6-month backtest before live trading

- **No A/B testing framework**
  - Can't easily compare strategy versions
  - **Impact**: Harder to validate improvements

### ⚠️ Performance & Scalability
- **Sequential order processing** (not threaded)
  - Each of 5 symbols processes one after another
  - Potential for delays if MT5 order_send() is slow
  - **Impact**: <100ms loop ideal, currently ~150-200ms per cycle

- **No caching of expensive operations**
  - ML predictions recalculated every cycle (even within same bar)
  - HTF trend lookups repeated for same symbol
  - Feature engineering runs full calculations every time
  - **Estimated time savings**: 20-30% with caching

- **No async/await on trade execution**
  - Blocks main loop until MT5 confirms order
  - **Recommendation**: Use ThreadPoolExecutor for order submission

- **News API module incomplete**
  - News sentiment check returns stubs (always returns False/neutral)
  - Not integrated into trading decisions
  - **Impact**: Missing risk control during high-impact events

### ⚠️ Missing Advanced Features
- **No trailing stop implementation**
  - Mentioned in code but not fully integrated
  - Would be valuable for runner legs of partial TP strategy

- **No position scaling/pyramiding**
  - Can't add to winning positions
  - Limits upside capture on strong trends

- **No correlation matrix** for symbol decoupling
  - Could help reduce redundant signals across highly correlated pairs
  - Manual prevention in code but no automatic control

- **No ML model auto-retraining**
  - Models trained once at startup
  - Should retrain daily/weekly with fresh data
  - Feature drift detection exists but no auto-remedy

- **No parameter optimization framework**
  - Risk thresholds, confidence levels, ATR multipliers hard-coded
  - No systematic tuning for each symbol

### ⚠️ Risk Management Gaps
- **Daily profit cap is hard ($250)**
  - Could be scaled to account balance percentage
  - Limits upside on low-balance accounts

- **Per-session limits crude** (max 3 trades/symbol/session)
  - Doesn't adapt to market volatility or win-rate
  - Could be dynamic based on Sharpe or drawdown

- **No correlation-aware position sizing**
  - Opens EURUSD, GBPUSD, and AUDUSD all with same risk
  - These are highly correlated—should reduce 2nd and 3rd entries

---

## COMPLETED IMPROVEMENTS (v8.5)

✅ **Code Consolidation**
- Removed duplicate `get_htf_trend()` at line 6,155
- Updated all callers to use keyword arguments
- Single source of truth now at line 23,006

✅ **Unit Test Suite**
- Created `tests/test_multi_entry.py` with 20+ test cases
- Coverage for consensus voting, individual strategies, risk management
- Edge case handling (empty data, None features, invalid directions)

---

## ROADMAP TO 9.5/10

### Immediate (1-2 hours) 🔥
1. **Run Unit Tests**
   ```bash
   pip install pytest
   pytest tests/test_multi_entry.py -v
   ```
   - All tests should pass
   - Fix any failures found

2. **Backtest Multi-Entry System** (90 minutes)
   ```python
   python backtest_multi_entry.py --symbols EURUSD.m GBPUSD.m XAUUSD.m --timeframe H1 --bars 500
   ```
   - Compare 3-strategy vs single-ML win rates
   - Target: 5-10% improvement on consensus signals
   - Measure: win rate, avg RR, Sharpe, max drawdown

3. **Performance Profiling** (45 minutes)
   ```python
   # Add timing decorators to main loop
   import time
   start = time.time()
   # ... run one iteration of trading loop ...
   print(f"Cycle time: {(time.time()-start)*1000:.1f}ms")
   ```
   - Target: <100ms per symbol
   - Identify bottleneck functions

### Short-term (2-4 hours) ⏱️
4. **Implement Prediction Caching**
   ```python
   # Cache ML predictions & HTF trends with 5-minute TTL
   @lru_cache(maxsize=512)
   def get_htf_trend_cached(symbol, timeframe):
       # ...
   ```
   - Expected improvement: 20-30% speedup

5. **Merge Main Trading Loops**
   ```python
   # Delete main_trading_loop() and main_loop()
   # Keep only run_live_trading_loop() as entry point
   # Saves ~300 lines, improves maintainability
   ```

6. **Add Trailing Stop Logic**
   ```python
   def update_trailing_stop(ticket, entry_price, current_price, direction, trail_pips=20):
       # Move SL closer to price as profit accumulates
   ```

### Medium-term (4-8 hours) 📊
7. **ML Auto-Retraining Pipeline**
   ```python
   # Schedule daily at 00:00 UTC
   def retrain_models_daily():
       # Load last 3 months of data
       # Retrain ensemble models
       # Save with version timestamp
   ```

8. **Dynamic Parameter Optimization**
   ```python
   # For each symbol, optimize:
   # - confidence_threshold
   # - atr_multipliers for SL/TP
   # - per-session trade limits
   # Based on recent performance metrics
   ```

9. **Correlation-Aware Position Sizing**
   ```python
   def calculate_correlation_adjusted_risk(symbol, open_symbols):
       base_risk = 0.02
       correlation = get_correlation_to_others(symbol, open_symbols)
       return base_risk * (1 - correlation * 0.5)
   ```

10. **Complete News Module Integration**
    ```python
    # Fetch real economic calendar
    # Check sentiment with NewsAPI or similar
    # Reduce lot size or skip trades 30min before/after high-impact events
    ```

---

## PERFORMANCE TARGETS

| Metric | Current | Target 9.5/10 |
|--------|---------|-------------|
| **Unit Test Coverage** | 0% | 80%+ |
| **Backtest Win Rate** | N/A | 62%+ on consensus signals |
| **Main Loop Speed** | ~150ms | <100ms |
| **Code Redundancy** | 300 lines | 0 lines |
| **Feature Drift Detection** | Implemented | Automated remediation |
| **Auto-Retraining** | Manual | Daily at 00:00 UTC |
| **Position Correlation Check** | Manual prevention | Automatic sizing |

---

## TESTING CHECKLIST BEFORE LIVE TRADING

- [ ] Unit tests pass (20/20)
- [ ] Backtest shows +5% improvement on 3-strategy vs single-ML
- [ ] Main loop runs at <100ms per symbol
- [ ] 1 week paper trading shows consistent wins
- [ ] Daily max drawdown respected on live account
- [ ] No duplicate function definitions remaining
- [ ] News API functional (or safely stubbed)
- [ ] Model retraining scheduled and tested

---

## SUPPORT & DEBUGGING

### Common Issues

**"get_htf_trend() called with wrong arguments"**
- **Cause**: Old code using `get_htf_trend(symbol)` without keyword args
- **Fix**: Update all callers to `get_htf_trend(symbol, time_frame="H1")`

**"Multi-entry module not found"**
- **Cause**: `multi_entry_strategies.py` missing or in wrong directory
- **Fix**: Ensure file is in same folder as `botfriday6000th.py`

**"Main loop slow (>200ms)"**
- **Cause**: Likely slow MT5 connection or excessive feature calculation
- **Fix**: Run performance profiler to identify bottleneck

**Unit tests fail with assertion errors**
- **Cause**: Strategy logic changed or test assumptions outdated
- **Fix**: Update test assertions to match new behavior, or fix strategy logic

---

## QUESTIONS & NEXT STEPS

**Q: When should I go live with multi-entry system?**
A: After completing items 1-3 above:
   1. ✅ Unit tests pass
   2. ✅ Backtest validated (6+ months, 62%+ win rate on consensus)
   3. ✅ 1 week paper trading shows consistency
   Then: Small live account ($500-1000) for 1 week before scaling

**Q: How do I know if the bot is improving?**
A: Track these daily:
   - Win rate per symbol (target 60%+)
   - Daily profit vs daily loss (target +$5-10/day)
   - Largest drawdown (target <$50)
   - Consensus trade rate (target >30% of total trades)

**Q: Should I modify strategy parameters?**
A: Only after:
   1. 500+ live trades (large sample size)
   2. Clear pattern of underperformance on specific symbol
   3. Backtest validates new parameters
   Then: Test on paper trading first

---

## VERSION HISTORY

- **v8.5** (Dec 9, 2025): Consolidated duplicate functions, added unit tests
- **v8.0** (Dec 1, 2025): Multi-entry system integration complete
- **v7.5** (Nov 20, 2025): SMC/ICT entry system added
- **v7.0** (Nov 1, 2025): Ensemble ML models working

---

**Last Updated**: December 9, 2025  
**Next Review**: After implementing items 1-3 roadmap  
**Contact**: Review multi_entry_strategies.py and test_multi_entry.py for code examples
