# Advanced Trade Execution Framework - Integration Guide

## Overview

The advanced trade execution framework consists of three core modules providing sophisticated, enterprise-grade order routing, risk management, and performance analytics:

1. **advanced_trade_executor.py** - Intelligent order routing and execution
2. **advanced_risk_manager.py** - Position risk assessment and portfolio management  
3. **performance_analytics.py** - Trade metrics and performance tracking

## Module 1: Advanced Trade Executor

### Purpose
Provides multi-strategy intelligent order routing with fallback logic, dynamic lot sizing, and execution quality metrics.

### Key Features

#### 1. Intelligent Order Routing
Routes orders through three execution strategies in priority:

```python
from advanced_trade_executor import execute_trade_intelligent

# Automatic strategy selection
result = execute_trade_intelligent(
    symbol="EURUSD",
    direction="buy",
    lot=0.1,
    entry=1.0950,
    sl=1.0900,
    tp=1.1050
)
```

**Strategies:**
1. **Market Order** - Fastest execution, immediate price
2. **Limit Order** - 1-2 pips better entry, 5-minute expiry
3. **Aggressive Market** - Market with 50 pips deviation tolerance

#### 2. Dynamic Lot Sizing
Calculates optimal lot size considering:
- Account balance and risk percentage
- Current open positions
- Position correlation
- Broker volume limits

```python
from advanced_trade_executor import calculate_optimal_lot

lot = calculate_optimal_lot(
    symbol="EURUSD",
    entry=1.0950,
    sl=1.0900,
    balance=10000.0,
    risk_percent=1.0,
    existing_positions=positions_list
)
```

#### 3. Partial Take-Profit Management
Closes positions in tiers at different Risk:Reward levels:

```python
from advanced_trade_executor import manage_partial_tp

results = manage_partial_tp(
    position_ticket=12345,
    entry_price=1.0950,
    tp_price=1.1050,
    direction="buy",
    symbol="EURUSD"
)

# Returns:
# {
#     "total_closed": 0.05,
#     "closures": [
#         {"level": 1, "price": 1.0980, "volume": 0.05, "profit": 50.0}
#     ]
# }
```

**Tier Configuration:**
- Level 1: 1x R:R closes 50% of position
- Level 2: 2x R:R closes 30% of position  
- Level 3: 3x R:R closes 20% of position

#### 4. Intelligent Trailing Stops
Dynamically adjusts stop loss to protect profits:

```python
from advanced_trade_executor import update_trailing_stop

success = update_trailing_stop(
    position_ticket=12345,
    direction="buy",
    symbol="EURUSD"
)
```

**Features:**
- Only trails when in profit
- Uses ATR-based step sizing (1 pip steps)
- Minimum 5 pip profit threshold to prevent whipsaws

#### 5. Execution Quality Tracking
Measures and reports execution quality:

```python
from advanced_trade_executor import get_execution_stats

stats = get_execution_stats()
# Returns:
# {
#     "total_orders": 245,
#     "successful": 240,
#     "failed": 5,
#     "success_rate": "97.9%",
#     "execution_quality": {
#         "EXCELLENT": 156,  # <= 0.5 pips slippage
#         "GOOD": 70,        # <= 2.0 pips
#         "ACCEPTABLE": 14   # <= 5.0 pips
#     }
# }
```

### Configuration

Edit `ExecutionConfig` class for customization:

```python
class ExecutionConfig:
    MAX_SLIPPAGE_PIPS = 2.0
    MAX_EXECUTION_TIME_MS = 5000
    MAX_SAME_DIRECTION_POSITIONS = 3
    MAX_LOT_PER_TRADE = 0.50
    PARTIAL_TP_LEVELS = [1.0, 2.0, 3.0]  # R:R levels
    TRAILING_STEP_PIPS = 1.0
```

---

## Module 2: Advanced Risk Manager

### Purpose
Comprehensive pre-trade risk assessment and portfolio-level risk monitoring.

### Key Features

#### 1. Pre-Trade Risk Assessment
Evaluates trade viability before execution:

```python
from advanced_risk_manager import assess_trade_viability

assessment = assess_trade_viability(
    symbol="EURUSD",
    direction="buy",
    lot=0.1,
    entry=1.0950,
    sl=1.0900,
    tp=1.1050
)

# Returns:
# {
#     "symbol": "EURUSD",
#     "direction": "buy",
#     "confidence": 85,
#     "can_execute": True,
#     "recommendation": "PROCEED - Low risk",
#     "risks": [],
#     "warnings": ["High correlation with GBPUSD"]
# }
```

**Risk Checks:**
1. **R:R Ratio** - Minimum 1.5:1 required
2. **Account Exposure** - Max 10% of account at risk
3. **Correlation** - Identifies correlated pairs trading same side
4. **Position Clustering** - Detects positions within 20 pips
5. **Margin Availability** - Requires 5% free margin
6. **Drawdown Limits** - Checks daily/weekly/monthly DD
7. **Lot Size Validation** - Broker min/max compliance

**Confidence Scoring:**
- 100: Optimal conditions
- 80+: Proceed
- 60-80: Caution
- <60: Block execution

#### 2. Dynamic Lot Sizing with Correlation
Reduces lot size based on correlated positions:

```python
from advanced_risk_manager import RiskConfig

RiskConfig.MAX_CORRELATION_SAME_SIDE = 0.85
RiskConfig.CORRELATION_LOT_REDUCTION = 0.5  # 50% reduction per correlated pair

# Lot automatically reduced by 50% for each similar position
```

#### 3. Portfolio Risk Metrics
Real-time portfolio analysis:

```python
from advanced_risk_manager import get_risk_metrics

metrics = get_risk_metrics()
# {
#     "account_balance": 10000.0,
#     "account_equity": 9850.0,
#     "margin_percentage": 25.5,
#     "open_positions": 3,
#     "profit_loss": -150.0,
#     "drawdown_percent": 1.5
# }
```

#### 4. Risk Report Generation
Formatted risk status report:

```python
from advanced_risk_manager import print_risk_report

print_risk_report()
```

Output:
```
╔══════════════════════════════════════════════════════╗
║           PORTFOLIO RISK REPORT                       ║
╚══════════════════════════════════════════════════════╝

💰 ACCOUNT METRICS:
   Balance:           $10,000.00
   Equity:            $9,850.00
   P&L:               -$150.00
   Margin Used:       25.5%

📊 POSITION METRICS:
   Open Positions:    3
   Total Exposure:    $24,500.00
   Current Drawdown:  1.50%

⚠️  RISK STATUS:
   Margin Buffer:     74.5%
   Safe to Trade:     ✓ YES
   Daily DD OK:       ✓ YES
```

### Configuration

```python
class RiskConfig:
    MAX_ACCOUNT_EXPOSURE_PERCENT = 10.0
    MAX_CORRELATION_SAME_SIDE = 0.85
    MAX_CORRELATED_POSITIONS = 3
    MAX_DAILY_DRAWDOWN_PERCENT = 5.0
    MIN_FREE_MARGIN_PERCENT = 5.0
    MIN_REWARD_RISK_RATIO = 1.5
```

---

## Module 3: Performance Analytics

### Purpose
Tracks and analyzes trading performance with statistical metrics.

### Key Features

#### 1. Trade Recording
Record completed trades:

```python
from performance_analytics import record_closed_trade
from datetime import datetime

success = record_closed_trade(
    symbol="EURUSD",
    direction="buy",
    entry=1.0950,
    exit=1.0995,
    entry_time=datetime.now() - timedelta(hours=2),
    exit_time=datetime.now(),
    lot_size=0.1,
    sl=1.0900,
    tp=1.1050,
    status="TP_HIT"
)
```

#### 2. Performance Metrics
Calculates comprehensive performance statistics:

```python
from performance_analytics import get_analytics

analytics = get_analytics()
summary = analytics.get_performance_summary()

# {
#     "total_trades": 45,
#     "winning_trades": 32,
#     "losing_trades": 13,
#     "win_rate_percent": 71.1,
#     "profit_factor": 2.5,      # Total wins / total losses
#     "expectancy": 125.50,       # Average profit per trade
#     "sharpe_ratio": 1.45,       # Risk-adjusted returns
#     "max_drawdown": 450.0,      # Largest losing streak
#     "recovery_factor": 2.1,     # Profit / max drawdown
#     "avg_trade_duration_minutes": 185
# }
```

**Key Metrics:**
- **Win Rate** - Percentage of winning trades
- **Profit Factor** - Gross wins / gross losses (>1.5 is good)
- **Expectancy** - Average profit per trade
- **Sharpe Ratio** - Risk-adjusted returns (>1.0 is good)
- **Max Drawdown** - Largest peak-to-trough decline
- **Recovery Factor** - How quickly profits recover losses

#### 3. Symbol Performance
Track performance by trading symbol:

```python
symbol_stats = analytics.get_symbol_stats("EURUSD")

# {
#     "symbol": "EURUSD",
#     "trades": 20,
#     "wins": 15,
#     "losses": 5,
#     "win_rate": 75.0,
#     "total_pnl": 1250.0,
#     "avg_win": 125.0,
#     "avg_loss": -50.0,
#     "largest_win": 450.0,
#     "largest_loss": -125.0
# }
```

#### 4. Trading Hours Analysis
Optimal trading time identification:

```python
hourly_performance = analytics.get_trading_hours_performance()

# {
#     8: {"trades": 5, "win_rate": 80.0, "total_pnl": 500.0, "avg_pnl": 100.0},
#     9: {"trades": 8, "win_rate": 62.5, "total_pnl": 400.0, "avg_pnl": 50.0},
#     # ... etc for each hour
# }
```

#### 5. Formatted Report
Generate trading report:

```python
from performance_analytics import print_performance_report

print_performance_report()
```

Output:
```
╔══════════════════════════════════════════════════════════════╗
║              TRADE PERFORMANCE ANALYSIS REPORT                ║
║              Last 30 Days                                     ║
╚══════════════════════════════════════════════════════════════╝

📊 TRADE STATISTICS:
   Total Trades:           45
   Winning Trades:         32
   Losing Trades:          13
   Win Rate:               71.1%

📈 PERFORMANCE METRICS:
   Profit Factor:          2.50x
   Expectancy (avg):       $125.50
   Sharpe Ratio:           1.45
   Max Drawdown:           $450.00
   Recovery Factor:        2.10

⏱️  TRADING ACTIVITY:
   Avg Trade Duration:     185 minutes

📌 SYMBOL PERFORMANCE:
   EURUSD   | Trades:  20 | Win%: 75.0% | P&L: +$1250.00
   GBPUSD   | Trades:  15 | Win%: 66.7% | P&L:  +$750.00
```

---

## Integration Examples

### Example 1: Complete Trade Execution Flow

```python
from advanced_trade_executor import execute_trade_intelligent, get_execution_stats
from advanced_risk_manager import assess_trade_viability
from performance_analytics import record_closed_trade
from datetime import datetime, timedelta

# 1. Assess risk
assessment = assess_trade_viability(
    symbol="EURUSD",
    direction="buy",
    lot=0.1,
    entry=1.0950,
    sl=1.0900,
    tp=1.1050
)

# Only execute if risk assessment passes
if assessment["can_execute"]:
    # 2. Execute trade with intelligent routing
    result = execute_trade_intelligent(
        symbol="EURUSD",
        direction="buy",
        lot=0.1,
        entry=1.0950,
        sl=1.0900,
        tp=1.1050
    )
    
    if result:
        print(f"Order executed: {result}")
        # 3. Record for analytics when trade closes
        # (Called when trade exits)
        record_closed_trade(
            symbol="EURUSD",
            direction="buy",
            entry=1.0950,
            exit=1.1050,  # Closed at TP
            entry_time=datetime.now() - timedelta(hours=2),
            exit_time=datetime.now(),
            lot_size=0.1,
            sl=1.0900,
            tp=1.1050,
            status="TP_HIT"
        )

# 4. Check execution quality
stats = get_execution_stats()
print(stats)
```

### Example 2: Portfolio Risk Monitoring

```python
from advanced_risk_manager import get_risk_metrics, print_risk_report
from advanced_trade_executor import get_executor
import time

# Monitor portfolio every 60 seconds
while True:
    metrics = get_risk_metrics()
    
    # Alert if margin usage too high
    if metrics["margin_percentage"] > 70:
        print(f"⚠️  HIGH MARGIN: {metrics['margin_percentage']:.1f}%")
    
    # Alert if drawdown exceeds limit
    if metrics["drawdown_percent"] > 5:
        print(f"⚠️  DRAWDOWN LIMIT: {metrics['drawdown_percent']:.2f}%")
    
    # Print full report every 10 iterations
    if int(time.time()) % 10 == 0:
        print_risk_report()
    
    time.sleep(60)
```

### Example 3: Position Management

```python
from advanced_trade_executor import manage_partial_tp, update_trailing_stop
import time

# Monitor open positions
position_ticket = 12345
direction = "buy"
symbol = "EURUSD"
entry_price = 1.0950
tp_price = 1.1050

while True:
    # Manage partial take-profits
    tp_results = manage_partial_tp(
        position_ticket=position_ticket,
        entry_price=entry_price,
        tp_price=tp_price,
        direction=direction,
        symbol=symbol
    )
    
    if tp_results["total_closed"] > 0:
        print(f"Partial TP closed: {tp_results['total_closed']} lots")
    
    # Update trailing stop
    if update_trailing_stop(position_ticket, direction, symbol):
        print("Trailing stop updated")
    
    time.sleep(30)
```

### Example 4: Performance Reporting

```python
from performance_analytics import get_analytics
import logging

# Setup logging
logging.basicConfig(
    filename='trading.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

analytics = get_analytics()

# Periodic reporting
if int(datetime.now().timestamp()) % 3600 == 0:  # Every hour
    summary = analytics.get_performance_summary()
    
    logging.info(f"Hourly Performance: {summary['total_trades']} trades, "
                f"Win rate: {summary['win_rate_percent']}%, "
                f"Profit Factor: {summary['profit_factor']:.2f}")
    
    # Check for best/worst hours
    hourly_perf = analytics.get_trading_hours_performance()
    best_hour = max(hourly_perf.items(), key=lambda x: x[1]["total_pnl"])
    logging.info(f"Best trading hour: {best_hour[0]}:00 "
                f"P&L: {best_hour[1]['total_pnl']:.2f}")
```

---

## Integration with Existing Bot

Add to `botfriday6000th.py`:

```python
# At top of file, after existing imports
from advanced_trade_executor import (
    execute_trade_intelligent,
    calculate_optimal_lot,
    manage_partial_tp,
    update_trailing_stop
)
from advanced_risk_manager import assess_trade_viability, print_risk_report
from performance_analytics import record_closed_trade, print_performance_report

# In place_trade() function:
def place_trade(symbol, direction, predicted_confidence):
    """Enhanced trade placement with advanced execution"""
    
    entry = current_price
    sl = entry - (atr * SL_ATR_MULTIPLIER)
    tp = entry + (atr * TP_ATR_MULTIPLIER)
    
    # Calculate optimal lot with correlation awareness
    lot = calculate_optimal_lot(
        symbol=symbol,
        entry=entry,
        sl=sl,
        balance=account_equity,
        existing_positions=mt5.positions_get()
    )
    
    # Risk assessment before execution
    assessment = assess_trade_viability(
        symbol=symbol,
        direction=direction,
        lot=lot,
        entry=entry,
        sl=sl,
        tp=tp
    )
    
    if not assessment["can_execute"]:
        logger.warning(f"Trade blocked: {assessment['recommendation']}")
        return None
    
    # Execute with intelligent routing
    result = execute_trade_intelligent(
        symbol=symbol,
        direction=direction,
        lot=lot,
        entry=entry,
        sl=sl,
        tp=tp
    )
    
    return result

# In main loop, periodically:
# - Call update_trailing_stop() for each open position
# - Call manage_partial_tp() for scaling exits
# - Print performance reports for monitoring
```

---

## Best Practices

1. **Always use `assess_trade_viability()` before execution**
   - Prevents over-leveraged positions
   - Catches correlated pairs
   - Enforces risk/reward minimums

2. **Monitor `margin_percentage` continuously**
   - Keep below 70% for safety
   - Alert at 50% usage threshold

3. **Use partial take-profits for volatile pairs**
   - Lock in gains progressively
   - Reduces risk from sudden reversals

4. **Track performance by symbol**
   - Identify best/worst performing pairs
   - Optimize strategy per symbol

5. **Review execution quality metrics**
   - Target <1.0 pips average slippage
   - Identify best execution hours

6. **Set trading hour limits**
   - Trade only during optimal hours
   - Avoid low-liquidity sessions

---

## Troubleshooting

**Q: Trades blocked by risk manager**
A: Check correlation thresholds and account exposure. Reduce lot sizes or wait for existing positions to close.

**Q: High slippage on orders**
A: Use limit order strategy (lower market impact) or trade during high-liquidity hours.

**Q: Margin warnings**
A: Reduce position sizes or close losing trades first. Keep >10% free margin buffer.

**Q: Inconsistent execution quality**
A: Monitor connection stability and broker latency. Use adaptive deviation limits.

---

## Performance Targets

### Execution Metrics
- Success Rate: >95%
- Average Slippage: <1.0 pip
- Order Fill Time: <100ms

### Trading Metrics
- Win Rate: >60%
- Profit Factor: >1.5
- Sharpe Ratio: >1.0
- Max Drawdown: <20% of equity

### Risk Management
- Account Exposure: <10%
- Margin Usage: <70%
- DD Recovery: <5 days

---

## Next Steps

1. Integrate modules into existing bot
2. Configure parameters to match trading style
3. Monitor execution quality metrics
4. Backtest on historical data
5. Run paper trading for 1-2 weeks
6. Gradually scale live deployment
