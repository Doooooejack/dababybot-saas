# 🤖 DababyBot EA-Like Trading System Guide

## **What is This?**

Your bot now works like **Expert Advisors (EAs)** in MetaTrader:
- **Set it once** with rules
- **Bot trades automatically** all day
- **You control everything** from dashboard
- **Multiple users** can trade simultaneously
- **Each user has their own equity** - no conflicts

---

## **How It Works**

### **Three Simple Steps:**

```
1. CREATE STRATEGY
   ├─ Choose symbol (EURUSD, GBPUSD, etc)
   ├─ Set entry rules (RSI, MACD, moving averages, etc)
   ├─ Set exit rules (take profit, stop loss signals)
   └─ Set risk management (position size, max loss)

2. ACTIVATE STRATEGY
   ├─ Bot starts monitoring market
   ├─ Checks conditions every candle
   └─ Executes trades automatically

3. BOT TRADES 24/7
   ├─ User can see all trades in dashboard
   ├─ Can modify rules anytime
   ├─ Can pause/resume anytime
   └─ Can create multiple strategies
```

---

## **Example: Simple EURUSD Scalper**

### **Your Goal:**
Trade EURUSD automatically all day. Buy when RSI drops below 30, sell when RSI goes above 70.

### **Create Strategy (REST API)**

```bash
curl -X POST https://your-api.com/api/strategy/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "EURUSD Quick Scalper",
    "symbol": "EURUSD",
    "entry_rules": [
      {
        "name": "RSI Oversold",
        "indicator": "rsi",
        "condition": "<",
        "value": 30
      }
    ],
    "exit_rules": [
      {
        "name": "RSI Overbought",
        "indicator": "rsi",
        "condition": ">",
        "value": 70
      }
    ],
    "risk_management": {
      "position_size": 0.1,
      "stop_loss_pips": 15,
      "take_profit_pips": 30,
      "max_concurrent_trades": 1
    }
  }'
```

### **Response:**
```json
{
  "strategy_id": "strat_abc123def456",
  "message": "Strategy created successfully",
  "strategy": {
    "name": "EURUSD Quick Scalper",
    "symbol": "EURUSD",
    "is_active": false,
    "position_size": 0.1,
    "sl_pips": 15,
    "tp_pips": 30
  }
}
```

### **Activate Strategy**

```bash
curl -X POST https://your-api.com/api/strategy/strat_abc123def456/activate \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **What Happens Next:**

```
┌─────────────────────────────────────────────┐
│ BOT STARTS MONITORING (Every M15 Candle)    │
├─────────────────────────────────────────────┤
│ 10:15 → Check: Is RSI < 30? NO, wait...     │
│ 10:30 → Check: Is RSI < 30? YES! BUY!       │
│         ├─ Entry: EURUSD @ 1.0850           │
│         ├─ Stop Loss: 1.0835 (15 pips)      │
│         └─ Take Profit: 1.0880 (30 pips)    │
│                                              │
│ 10:45 → Check: Is RSI > 70? NO, holding...  │
│ 11:00 → Check: Is RSI > 70? YES! SELL!      │
│         ├─ Exit: EURUSD @ 1.0880            │
│         ├─ Profit: +30 pips = +$30          │
│         └─ Ready for next signal            │
│                                              │
│ 11:15 → Check: Is RSI < 30? YES! BUY again! │
│         (Repeats all day automatically)      │
└─────────────────────────────────────────────┘
```

### **In Your Dashboard:**
```
✅ EURUSD Quick Scalper
   ├─ Status: RUNNING (Since 8:00 AM)
   ├─ Symbol: EURUSD
   ├─ Position: OPEN (1 trade)
   │  └─ Entry: 1.0850 | SL: 1.0835 | TP: 1.0880
   │
   ├─ Today's Results:
   │  ├─ Completed Trades: 5
   │  ├─ Winning Trades: 4
   │  ├─ Losing Trades: 1
   │  └─ Total P&L: +$110
   │
   └─ Controls:
      ├─ ⏸️ PAUSE (Pause trading)
      ├─ ✏️ EDIT (Modify rules while running)
      ├─ ⏹️ STOP (Turn off strategy)
      └─ 🗑️ DELETE (Remove strategy)
```

---

## **Advanced: Multiple Strategies Per User**

### **User Can Run Multiple EAs Simultaneously:**

```
User: Joe Trader

STRATEGY 1: "EURUSD Scalper"
├─ Symbol: EURUSD
├─ Timeframe: M15
├─ Status: RUNNING ✅
├─ Trades Today: 5
└─ P&L: +$110

STRATEGY 2: "GBPUSD Swing"
├─ Symbol: GBPUSD
├─ Timeframe: H1
├─ Status: RUNNING ✅
├─ Trades Today: 2
└─ P&L: +$250

STRATEGY 3: "USDJPY Trend"
├─ Symbol: USDJPY
├─ Timeframe: H4
├─ Status: PAUSED ⏸️
├─ Trades Today: 0
└─ P&L: $0
```

**Each strategy is completely independent:**
- Different symbols ✅
- Different time frames ✅
- Different rules ✅
- **Shared account equity** (all profits/losses go to same account) ✅

---

## **API Endpoints - Full Reference**

### **1. Create Strategy (Template)**
```
POST /api/strategy/create
Body: {
  "name": "Strategy Name",
  "symbol": "EURUSD",
  "entry_rules": [...],
  "exit_rules": [...],
  "risk_management": {...}
}
Returns: { strategy_id, message }
```

### **2. Get Strategy Templates**
```
GET /api/strategy/templates
Returns: 
{
  "templates": {
    "scalper": { pre-built scalping strategy },
    "swing": { pre-built swing strategy },
    "trend": { pre-built trend following strategy }
  }
}
```

### **3. List All User Strategies**
```
GET /api/strategy/list
Returns: { strategies: [...], total }
```

### **4. Get Strategy Status**
```
GET /api/strategy/{strategy_id}/status
Returns: {
  "strategy_id": "...",
  "name": "...",
  "symbol": "EURUSD",
  "is_active": true,
  "status": "in_trade",
  "last_trade_id": "trade_123",
  "position_size": 0.1,
  "sl_pips": 50,
  "tp_pips": 100
}
```

### **5. Activate Strategy (Turn ON)**
```
POST /api/strategy/{strategy_id}/activate
Returns: { message, is_active: true }
```

### **6. Deactivate Strategy (Turn OFF)**
```
POST /api/strategy/{strategy_id}/deactivate
Returns: { message, is_active: false }
```

### **7. Update Strategy Parameters (While Running!)**
```
POST /api/strategy/{strategy_id}/update
Body: {
  "entry_rules": [...],      # Update entry conditions
  "exit_rules": [...],        # Update exit conditions
  "risk_management": {...},   # Update position size, SL, TP
  "name": "New Name"
}
Returns: { message, updates }
```

---

## **Available Indicators & Conditions**

### **1. RSI (Relative Strength Index)**
```json
{
  "indicator": "rsi",
  "condition": ">",  // Can be >, <, ==
  "value": 70        // Overbought threshold
}
```
**What it means:** If RSI > 70 = overbought (sell signal)

---

### **2. MACD (Moving Average Convergence Divergence)**
```json
{
  "indicator": "macd",
  "condition": "cross_above",  // cross_above, cross_below
  "value": 0                   // Not used, MACD crosses signal line
}
```
**What it means:** If MACD crosses above signal line = buy signal

---

### **3. SMA Cross (Simple Moving Averages)**
```json
{
  "indicator": "sma_cross",
  "condition": "cross_above",  // cross_above, cross_below
  "value": "50,200"            // Fast SMA = 50, Slow SMA = 200
}
```
**What it means:** If SMA50 > SMA200 = uptrend (buy signal)

---

### **4. Price Level**
```json
{
  "indicator": "price_level",
  "condition": ">",  // >, <
  "value": 1.1000    // Price level
}
```
**What it means:** If current price > 1.1000 = enter

---

## **Pre-Built Strategy Templates**

### **Template 1: Scalper (RSI Quick Profits)**
```
Entry: RSI < 30 (oversold)
Exit: RSI > 70 (overbought)
Position Size: 0.1 lot
Stop Loss: 15 pips
Take Profit: 30 pips
```
✅ Best for: Quick 5-minute profits, experienced traders

---

### **Template 2: Swing Trader (SMA Crossover)**
```
Entry: SMA50 crosses above SMA200 (bullish trend)
Exit: SMA50 crosses below SMA200 (trend reverses)
Position Size: 0.5 lot
Stop Loss: 100 pips
Take Profit: 250 pips
```
✅ Best for: Capturing larger swings, less stressful

---

### **Template 3: Trend Follower (MACD Signal)**
```
Entry: MACD crosses above signal (trend starts)
Exit: MACD crosses below signal (trend ends)
Position Size: 0.3 lot
Stop Loss: 75 pips
Take Profit: 200 pips
Max Concurrent: 2 (can have 2 open trades)
```
✅ Best for: Following strong trends, position trading

---

## **Dashboard UI Example**

```
╔════════════════════════════════════════════╗
║ 🤖 DababyBot EA Trading Dashboard         ║
╠════════════════════════════════════════════╣
║                                            ║
║ CREATE NEW STRATEGY                        ║
│ ┌──────────────────────────────────────┐   ║
│ │ Strategy Name: EURUSD Scalper        │   ║
│ │ Symbol: EURUSD                       │   ║
│ │ Timeframe: M15                       │   ║
│ │                                      │   ║
│ │ ENTRY CONDITIONS:                    │   ║
│ │ [+] Add Entry Rule                   │   ║
│ │     └─ RSI < 30                      │   ║
│ │                                      │   ║
│ │ EXIT CONDITIONS:                     │   ║
│ │ [+] Add Exit Rule                    │   ║
│ │     └─ RSI > 70                      │   ║
│ │     └─ Time: 4 PM (daily close)      │   ║
│ │                                      │   ║
│ │ RISK MANAGEMENT:                     │   ║
│ │ Position Size: 0.1 lot               │   ║
│ │ Stop Loss: 15 pips                   │   ║
│ │ Take Profit: 30 pips                 │   ║
│ │ Max Concurrent Trades: 1             │   ║
│ │                                      │   ║
│ │ [CREATE] [USE TEMPLATE] [CANCEL]     │   ║
│ └──────────────────────────────────────┘   ║
║                                            ║
║ YOUR ACTIVE STRATEGIES                     ║
│                                            │
│ ✅ EURUSD Scalper (Running)                │
│    ├─ Position: 1 open trade              │
│    ├─ Entry: 1.0850                       │
│    ├─ Today P&L: +$110 (+5 trades)        │
│    └─ Controls: [PAUSE] [EDIT] [STOP]     │
│                                            │
│ ✅ GBPUSD Swing (Running)                  │
│    ├─ Position: 0 open trades             │
│    ├─ Waiting for SMA cross               │
│    ├─ Today P&L: +$250 (+2 trades)        │
│    └─ Controls: [PAUSE] [EDIT] [STOP]     │
│                                            │
│ ⏸️  USDJPY Trend (Paused)                  │
│    ├─ Position: 1 open trade              │
│    ├─ Entry: 110.50                       │
│    ├─ Today P&L: $0                       │
│    └─ Controls: [RESUME] [EDIT] [STOP]    │
│                                            │
╚════════════════════════════════════════════╝
```

---

## **User Scenarios**

### **Scenario 1: Lazy Trader (No experience)**
```
1. Logs into dashboard
2. Clicks "Use Template" → selects "Swing Trader"
3. Changes symbol to EURUSD
4. Clicks "Activate"
5. Goes to sleep
6. Bot trades EURUSD all night automatically
7. Next morning: Checks results (+$250)
```

---

### **Scenario 2: Active Trader (Day trader)**
```
1. Creates 3 strategies (Scalper, Swing, Trend)
2. Morning: Activates all 3 strategies
3. 10:15 AM: Sees scalper entered 2 trades (+$60)
4. 10:30 AM: Modifies exit rule to tighter SL
5. 11:00 AM: Pauses trend strategy (market too choppy)
6. 2:00 PM: Resumes trend strategy (market clearer)
7. 5:00 PM: Stops all strategies before market close
8. Total P&L: +$430
```

---

### **Scenario 3: SaaS Owner (10+ Users)**
```
User 1: EURUSD Scalper (Running) ✅
User 2: GBPUSD Swing (Running) ✅
User 3: USDJPY Trend (Paused) ⏸️
User 4: EURUSD + GBPUSD (2 strategies, both running) ✅
User 5: XAUUSD Scalper (Running) ✅
...
User 10: Multiple strategies (each with own relay bot)

Cloud Relay:
├─ Route User 1 trades → User 1's Bot → User 1's MT5 Account
├─ Route User 2 trades → User 2's Bot → User 2's MT5 Account
├─ Route User 3 trades → User 3's Bot → User 3's MT5 Account
└─ ...all without conflicts!
```

---

## **Billing Model**

### **Free Tier:**
```
✅ 1 strategy
✅ 1 symbol
✅ Relay system (FREE)
✅ Basic indicators (RSI, SMA, MACD)
```

### **Pro Tier ($29/month):**
```
✅ 5 strategies
✅ 5 symbols
✅ Advanced indicators (ATR, Bollinger, etc)
✅ Custom entry/exit rules
✅ Email alerts
```

### **Elite Tier ($99/month):**
```
✅ Unlimited strategies
✅ Unlimited symbols
✅ All indicators
✅ Cloud Windows bot (if needed)
✅ Priority support
✅ Backtesting (coming soon)
```

---

## **FAQ**

### **Q: Can I run multiple strategies on different symbols?**
✅ Yes! Each strategy trades its own symbol independently.

### **Q: What if I want to change the rules while it's trading?**
✅ Just update the strategy! Changes take effect on next candle.

### **Q: Does the bot need 24/7 internet?**
✅ Your relay bot on Windows needs internet. Desktop connection (yours) doesn't need to stay open.

### **Q: Can I backtest before going live?**
⏳ Coming soon - backtesting tool will let you test strategies on historical data.

### **Q: What if I lose connection?**
✅ Bot will keep trading offline on Windows. Once reconnected, it syncs results back.

### **Q: How many users can I support?**
✅ Unlimited! Each user has their own strategy, bot, and MT5 account. No conflicts.

### **Q: Can I charge users per strategy?**
✅ Yes! Build your billing model: 
- Free: 1 strategy
- Pro: 5 strategies
- Elite: Unlimited

---

## **Next Steps**

1. **Try the Scalper Template** - Fastest way to start
2. **Set symbol to your favorite** - EURUSD, GBPUSD, USDJPY
3. **Activate & watch it trade!** - Bot handles everything
4. **Modify rules anytime** - Even while running
5. **Scale to 10+ users** - Same relay system handles them all!

Happy bot trading! 🚀

