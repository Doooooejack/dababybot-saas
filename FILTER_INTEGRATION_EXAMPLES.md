# Integration Examples - How to Use the 7 Filters in Your Bot

## Example 1: Simple Integration in Main Trading Loop

```python
def execute_trade_with_filters(symbol, direction, price_data, account_info):
    """
    Example function showing how to use all 7 filters before placing a trade.
    """
    
    print(f"\n[{symbol}] Entry Signal: {direction.upper()}")
    print("=" * 60)
    
    # Get current price
    entry_price = price_data['close'].iloc[-1]
    
    # === APPLY ALL 7 FILTERS ===
    filter_results = apply_all_entry_filters(
        symbol=symbol,
        df=price_data,
        direction=direction,
        entry_price=entry_price
    )
    
    # === LOG FILTER RESULTS ===
    print(f"\nFilter Results: {filter_results['filters_passed']}/7 passed")
    print(f"Recommendation: {filter_results['recommendation']}")
    
    if not filter_results['allowed']:
        print(f"❌ Entry BLOCKED: {filter_results['reason']}")
        for failed in filter_results['filters_failed'][:3]:
            print(f"   - {failed}")
        return False
    
    # === EXTRACT VALIDATED STOPS FROM FILTER #4 ===
    f4_data = filter_results['details']['filter_4_atr_stops']
    sl_price = f4_data['sl']
    tp_price = f4_data['tp']
    rr_ratio = f4_data['metrics']['rr_ratio']
    
    # === CALCULATE LOT SIZE ===
    lot = get_fixed_lot_size(symbol, confidence=0.8)
    
    # === PLACE TRADE ===
    print(f"\n✅ Entry ALLOWED - Placing trade:")
    print(f"   Direction: {direction.upper()}")
    print(f"   Entry: {entry_price:.5f}")
    print(f"   SL: {sl_price:.5f}")
    print(f"   TP: {tp_price:.5f}")
    print(f"   RR: {rr_ratio:.2f}:1")
    print(f"   Lot: {lot}")
    
    try:
        result = place_trade(symbol, direction, lot, sl_price, tp_price)
        print(f"   Result: {result}")
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False


# Usage in main loop:
# ===========================
for symbol in SYMBOLS:
    df = get_price_data(symbol, timeframe=mt5.TIMEFRAME_M30, bars=100)
    
    # Example: Check for SELL signal
    if check_sell_signal(df):  # Your existing signal detection
        execute_trade_with_filters(symbol, 'sell', df, mt5.account_info())
    
    # Example: Check for BUY signal
    if check_buy_signal(df):  # Your existing signal detection
        execute_trade_with_filters(symbol, 'buy', df, mt5.account_info())
```

---

## Example 2: Progressive Filter Application

Start strict, then relax filters as you gain confidence:

```python
def execute_trade_smart(symbol, direction, price_data, confidence_level='normal'):
    """
    Apply filters with varying strictness based on confidence level.
    
    confidence_level: 'strict' (7/7), 'normal' (5/7), 'aggressive' (4/7)
    """
    
    entry_price = price_data['close'].iloc[-1]
    filter_results = apply_all_entry_filters(symbol, price_data, direction, entry_price)
    
    # Define requirements per confidence level
    min_filters = {
        'strict': 7,      # All filters must pass
        'normal': 5,      # Most filters must pass (recommended)
        'aggressive': 4   # Minimum consensus
    }
    
    required = min_filters.get(confidence_level, 5)
    can_trade = filter_results['filters_passed'] >= required
    
    print(f"\n[{symbol}] Confidence Level: {confidence_level.upper()}")
    print(f"Filters: {filter_results['filters_passed']}/{required} required")
    
    if not can_trade:
        print(f"❌ Insufficient filters passed for {confidence_level} mode")
        return False
    
    # Extract stops and trade
    f4_data = filter_results['details']['filter_4_atr_stops']
    sl_price = f4_data['sl']
    tp_price = f4_data['tp']
    
    lot = get_fixed_lot_size(symbol, confidence=0.8)
    
    print(f"✅ Trade allowed in {confidence_level} mode")
    place_trade(symbol, direction, lot, sl_price, tp_price)
    return True
```

---

## Example 3: Per-Symbol Custom Filter Thresholds

```python
# Define custom settings per symbol
SYMBOL_FILTER_CONFIG = {
    'EURUSD.m': {
        'min_filters_required': 6,  # EUR is reliable, need 6/7
        'min_distance_from_swing': 12,  # EUR is tight
        'session_filter_required': True,
        'impulse_multiplier': 1.5,
    },
    'USDJPY.m': {
        'min_filters_required': 6,  # JPY is directional
        'min_distance_from_swing': 15,  # JPY is wider
        'session_filter_required': True,  # MUST be NY session
        'impulse_multiplier': 1.8,  # JPY is volatile
    },
    'XAUUSD.m': {
        'min_filters_required': 5,  # Gold has wider swings
        'min_distance_from_swing': 20,  # Gold needs room
        'session_filter_required': False,  # Gold trades 24/5
        'impulse_multiplier': 2.0,  # Gold has big impulses
    },
    'AUDUSD.m': {
        'min_filters_required': 5,
        'min_distance_from_swing': 10,
        'session_filter_required': True,
        'impulse_multiplier': 1.5,
    },
    'GBPUSD.m': {
        'min_filters_required': 6,
        'min_distance_from_swing': 10,
        'session_filter_required': True,
        'impulse_multiplier': 1.6,
    },
}


def execute_trade_with_symbol_config(symbol, direction, price_data):
    """
    Execute trade using symbol-specific filter configuration.
    """
    
    # Get symbol config (use defaults if not defined)
    config = SYMBOL_FILTER_CONFIG.get(symbol, {
        'min_filters_required': 5,
        'min_distance_from_swing': 15,
        'session_filter_required': True,
        'impulse_multiplier': 1.5,
    })
    
    entry_price = price_data['close'].iloc[-1]
    
    # Apply custom Filter #3 (Impulse)
    is_safe, reason, metrics = filter_3_avoid_impulse_candles(
        price_data, symbol, 
        max_range_multiplier=config['impulse_multiplier']
    )
    
    # Apply custom Filter #5 (Session)
    if config['session_filter_required']:
        can_trade, session, reason = filter_5_session_filter(symbol)
        if not can_trade:
            print(f"❌ {symbol}: {reason}")
            return False
    
    # Apply custom Filter #7 (Anti-Drawdown)
    is_safe, reason, metrics = filter_7_anti_drawdown_rule(
        price_data, direction, 
        min_distance_from_swing=config['min_distance_from_swing']
    )
    
    # Apply all filters
    filter_results = apply_all_entry_filters(symbol, price_data, direction, entry_price)
    
    if filter_results['filters_passed'] < config['min_filters_required']:
        print(f"❌ {symbol}: Only {filter_results['filters_passed']}/{config['min_filters_required']} filters passed")
        return False
    
    # Trade is allowed
    f4_data = filter_results['details']['filter_4_atr_stops']
    sl_price = f4_data['sl']
    tp_price = f4_data['tp']
    lot = get_fixed_lot_size(symbol)
    
    print(f"✅ {symbol}: {filter_results['filters_passed']}/{config['min_filters_required']} filters - TRADE")
    place_trade(symbol, direction, lot, sl_price, tp_price)
    return True
```

---

## Example 4: Filter Results Logging & Analysis

```python
import json
from datetime import datetime

def log_filter_analysis(symbol, direction, filter_results):
    """
    Log detailed filter analysis for later review and optimization.
    """
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol,
        'direction': direction,
        'filters_passed': filter_results['filters_passed'],
        'total_filters': 7,
        'recommendation': filter_results['recommendation'],
        'filters': {}
    }
    
    # Log each filter result
    for filter_name, filter_data in filter_results['details'].items():
        filter_num = filter_name.split('_')[1]
        filter_status = 'PASS' if filter_data.get('valid') or filter_data.get('safe') or filter_data.get('can_trade') else 'FAIL'
        
        log_entry['filters'][filter_num] = {
            'status': filter_status,
            'reason': filter_data.get('reason', 'N/A')[:100],
        }
    
    # Write to JSON file for analysis
    try:
        with open(f'filter_logs_{symbol}.json', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        print(f"Error logging filter results: {e}")
    
    return log_entry


def analyze_filter_performance(symbol, num_entries=100):
    """
    Analyze which filters are blocking trades most often.
    """
    
    filter_stats = {
        'filter_1_pullback': {'pass': 0, 'fail': 0},
        'filter_2_htf_trend': {'pass': 0, 'fail': 0},
        'filter_3_impulse': {'pass': 0, 'fail': 0},
        'filter_4_atr_stops': {'pass': 0, 'fail': 0},
        'filter_5_session': {'pass': 0, 'fail': 0},
        'filter_6_structure': {'pass': 0, 'fail': 0},
        'filter_7_anti_drawdown': {'pass': 0, 'fail': 0},
    }
    
    try:
        with open(f'filter_logs_{symbol}.json', 'r') as f:
            lines = f.readlines()[-num_entries:]
            
            for line in lines:
                entry = json.loads(line)
                for filter_num, filter_data in entry['filters'].items():
                    filter_key = f'filter_{filter_num}'
                    if filter_data['status'] == 'PASS':
                        filter_stats[filter_key]['pass'] += 1
                    else:
                        filter_stats[filter_key]['fail'] += 1
    
    except Exception as e:
        print(f"Error analyzing filters: {e}")
        return None
    
    # Print report
    print(f"\n[{symbol}] Filter Performance Analysis (last {num_entries} entries)")
    print("=" * 60)
    for filter_name, stats in filter_stats.items():
        total = stats['pass'] + stats['fail']
        pass_rate = (stats['pass'] / total * 100) if total > 0 else 0
        print(f"{filter_name}: {stats['pass']}/{total} passed ({pass_rate:.0f}%)")
    
    # Identify most restrictive filters
    restrictive = sorted(
        [(k, v['fail']/(v['pass']+v['fail'])*100) for k, v in filter_stats.items()],
        key=lambda x: x[1], reverse=True
    )
    
    print("\nMost Restrictive (most rejections):")
    for filter_name, reject_rate in restrictive[:3]:
        print(f"  {filter_name}: {reject_rate:.0f}% rejection rate")
    
    return filter_stats


# Usage:
# ===========================
# results = apply_all_entry_filters('EURUSD.m', df, 'sell')
# log_filter_analysis('EURUSD.m', 'sell', results)
#
# # After 100+ trades, analyze performance:
# analyze_filter_performance('EURUSD.m', num_entries=100)
```

---

## Example 5: Real-Time Filter Visualization

```python
def print_filter_results_detailed(symbol, filter_results):
    """
    Print detailed, easy-to-read filter results.
    """
    
    # Color codes for terminal output
    PASS = "✅"
    FAIL = "❌"
    WARN = "⚠️"
    
    print(f"\n" + "="*70)
    print(f"  ENTRY ANALYSIS: {symbol}")
    print("="*70)
    
    # Filter #1
    f1 = filter_results['details']['filter_1_pullback']
    status = PASS if f1['valid'] else FAIL
    print(f"{status} Filter 1 - Pullback Confirmation")
    print(f"   └─ {f1['reason']}")
    if f1['valid']:
        print(f"      Entry at: {f1['metrics'].get('pullback_status', 'N/A')}")
    
    # Filter #2
    f2 = filter_results['details']['filter_2_htf_trend']
    status = PASS if f2['valid'] else FAIL
    print(f"{status} Filter 2 - Higher Timeframe Trend")
    print(f"   └─ {f2['reason']}")
    if f2['trend']:
        print(f"      H1: {f2['trend'].get('h1_trend', 'N/A')} | H4: {f2['trend'].get('h4_trend', 'N/A')}")
    
    # Filter #3
    f3 = filter_results['details']['filter_3_impulse']
    status = PASS if f3['safe'] else FAIL
    print(f"{status} Filter 3 - Impulse Avoidance")
    print(f"   └─ {f3['reason']}")
    if not f3['safe']:
        print(f"      Candle range: {f3['metrics'].get('last_candle_range', 0):.6f}")
    
    # Filter #4
    f4 = filter_results['details']['filter_4_atr_stops']
    status = PASS if f4['valid'] else FAIL
    print(f"{status} Filter 4 - ATR-Based Stops")
    print(f"   └─ {f4['reason']}")
    if f4['valid']:
        print(f"      SL: {f4['sl']:.5f} | TP: {f4['tp']:.5f} | RR: {f4['metrics']['rr_ratio']:.2f}:1")
    
    # Filter #5
    f5 = filter_results['details']['filter_5_session']
    status = PASS if f5['can_trade'] else FAIL
    print(f"{status} Filter 5 - Session Filter")
    print(f"   └─ {f5['session']}: {f5['reason']}")
    
    # Filter #6
    f6 = filter_results['details']['filter_6_structure']
    status = PASS if f6['valid'] else FAIL
    print(f"{status} Filter 6 - Structure Break")
    print(f"   └─ {f6['reason']}")
    if f6['valid']:
        print(f"      Level: {f6['level']:.5f} | Retest: {f6['retest']}")
    
    # Filter #7
    f7 = filter_results['details']['filter_7_anti_drawdown']
    status = PASS if f7['safe'] else FAIL
    print(f"{status} Filter 7 - Anti-Drawdown")
    print(f"   └─ {f7['reason']}")
    
    # Summary
    print("\n" + "-"*70)
    passed = filter_results['filters_passed']
    print(f"RESULT: {passed}/7 filters passed")
    if filter_results['allowed']:
        print(f"🚀 RECOMMENDATION: {filter_results['recommendation'].upper()} - Entry is valid")
    else:
        print(f"🛑 RECOMMENDATION: {filter_results['recommendation'].upper()} - Entry is blocked")
    print("="*70 + "\n")


# Usage:
# ===========================
# results = apply_all_entry_filters('EURUSD.m', df, 'sell')
# print_filter_results_detailed('EURUSD.m', results)
```

---

## Quick Copy-Paste Template

Use this template in your bot to quickly integrate all filters:

```python
# In your main trading loop:
def check_and_execute_entry(symbol, direction):
    df = get_price_data(symbol, timeframe=mt5.TIMEFRAME_M30, bars=100)
    
    if df is None or len(df) < 50:
        return False
    
    # Apply filters
    results = apply_all_entry_filters(symbol, df, direction)
    
    # Skip if not enough filters passed
    if not results['allowed']:
        return False
    
    # Extract validated stops from Filter #4
    f4 = results['details']['filter_4_atr_stops']
    sl = f4['sl']
    tp = f4['tp']
    
    # Place trade
    lot = get_fixed_lot_size(symbol)
    place_trade(symbol, direction, lot, sl, tp)
    
    return True
```

That's it! You're now using all 7 anti-drawdown filters. 🚀
