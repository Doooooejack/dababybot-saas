# 🚀 QUICK START GUIDE - Bot Dashboard

## Status: ✅ READY TO USE

Your dashboard is fully integrated with real MT5 data and bot control.

---

## Step 1: Start the Dashboard

Open PowerShell or Command Prompt and run:

```bash
cd c:\Users\JEFFKID\Desktop\dabbay
python bot_dashboard.py
```

You should see:
```
================================================
BOT DASHBOARD - Phone Control Interface
================================================

Access dashboard:
   - From this PC:  http://localhost:5000
   - From phone:    http://10.30.18.114:5000
   
...
* Running on http://127.0.0.1:5000
* Running on http://10.30.18.114:5000
```

The dashboard is now running in the background.

---

## Step 2: Access Dashboard

### On Your PC:
Open browser and go to: `http://localhost:5000`

### On Your Phone (Same WiFi):
1. Get your PC's IP (shown in dashboard output, e.g., `10.30.18.114`)
2. On phone browser, go to: `http://10.30.18.114:5000`
3. You'll see the dashboard with real-time updates

---

## Step 3: Control Your Bot

### To RUN the Bot:
1. Click the **"Run"** button at the top-left
2. You'll see:
   - ✅ "Bot started (PID: xxxx)" in the Logs
   - 🟢 **Running** status appears
   - Real MT5 balance, equity, P&L display
   - Open trades appear in "Open Trades" tab

### To STOP the Bot:
1. Click the **"Stop"** button
2. Dashboard will gracefully terminate the bot
3. Status returns to **Stopped**

---

## What You'll See on Dashboard

### **Status Cards** (Top Row)
- 💰 **Account Balance**: Your MT5 account balance (real-time)
- 📊 **Today's P&L**: Profit/Loss for the day
- 📈 **Equity**: Current account equity
- ⚡ **Margin Level**: Margin usage percentage

### **Open Trades Tab**
Shows all active positions:
- Symbol (EURUSD, GBPUSD, etc.)
- Trade Type (BUY/SELL)
- Entry Price
- Current Price
- Profit/Loss (in $ and %)
- Entry Time

### **Logs Tab**
Shows all events:
- Bot start/stop
- Trade entries/exits
- Errors and warnings
- Symbol toggles

### **News Tab**
Shows:
- Latest economic news
- Upcoming economic events
- News sentiment (Bullish/Bearish/Neutral)

---

## Real-Time Updates

✅ **Dashboard updates every 5 seconds automatically**

The background thread:
1. Connects to MT5
2. Fetches live account data
3. Retrieves all open positions
4. Updates the UI

No need to refresh the page - it updates itself!

---

## Phone Controls

### Symbol Toggle
- Tap symbol buttons to enable/disable trading
- Green = Trading enabled
- Gray = Trading disabled

### Pause/Resume
- **Pause**: Stop taking new trades (keep existing ones)
- **Resume**: Start taking new trades again

### Close Trade
- Tap any trade and click "Close" to exit that position
- (Opens position at market)

### Settings
- Adjust lot size, max daily loss, confidence threshold
- Changes apply immediately

---

## Verify It's Working

Run the test script to verify everything:

```bash
python test_dashboard_api.py
```

You should see:
```
[1/4] Testing if dashboard server is running...
✓ Dashboard server is UP

[2/4] Fetching live account status...
✓ Status endpoint working
   Account Balance: $10,000.00
   Equity: $10,125.50
   Daily P&L: $125.50
   MT5 Connected: True
   Bot Running: False
   Open Trades: 2

[3/4] Testing bot start endpoint...
✓ Start endpoint working: Bot started successfully

[4/4] Bot Status: RUNNING
✓ Stop endpoint working: Bot stopped
```

---

## Troubleshooting

### "Can't access from phone"
1. Check both phone and PC are on **same WiFi**
2. Find your PC's IP:
   ```bash
   ipconfig
   ```
   Look for "IPv4 Address" under your WiFi connection (e.g., `10.30.18.114`)
3. Try: `http://10.30.18.114:5000`

### "MT5 Not Connected" appears
1. Open MetaTrader5 on your PC
2. Verify account is logged in
3. Wait 5 seconds for dashboard to reconnect
4. Refresh page

### "Bot file not found"
- Ensure `botfriday6000th.py` is in: `c:\Users\JEFFKID\Desktop\dabbay\`
- Check file path matches directory where you run the dashboard

### Dashboard shows 0 balance
- MT5 may not be fully connected
- Click "Refresh" button
- Verify MT5 has active account

### Port 5000 already in use
```bash
# Kill existing process
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Then restart dashboard
python bot_dashboard.py
```

---

## URL Shortcuts

Save these URLs on your phone for quick access:

```
Local Network (Same WiFi):
http://10.30.18.114:5000

Status Check:
http://10.30.18.114:5000/api/status

News & Events:
http://10.30.18.114:5000/api/news/EURUSD
```

---

## Advanced: Remote Access from Internet

To access dashboard from **anywhere** (outside your network):

### Option 1: Cloudflare Tunnel (Recommended)
```bash
# Install cloudflared
# https://developers.cloudflare.com/cloudflare-one/connections/connect-applications/install-and-setup/

# Create tunnel
cloudflared tunnel create bot-dashboard
cloudflared tunnel route dns bot-dashboard your-domain.com

# Run tunnel
cloudflared tunnel run bot-dashboard --url http://localhost:5000
```

### Option 2: ngrok (Simple)
```bash
# Download ngrok: https://ngrok.com/download

# Run ngrok
ngrok http 5000

# You'll get a URL like:
# https://1234-56-78-90-12.ngrok.io
```

---

## API Endpoints (For Reference)

If you want to control the bot programmatically:

```bash
# Get status
curl http://localhost:5000/api/status

# Start bot
curl -X POST http://localhost:5000/api/start

# Stop bot
curl -X POST http://localhost:5000/api/stop

# Pause trading
curl -X POST http://localhost:5000/api/pause

# Resume trading
curl -X POST http://localhost:5000/api/resume

# Toggle symbol
curl -X POST http://localhost:5000/api/toggle-symbol/EURUSD

# Get news for symbol
curl http://localhost:5000/api/news/EURUSD
```

---

## That's It! 🎉

You're ready to:
1. ✅ Control your bot from your phone
2. ✅ Monitor real MT5 account data
3. ✅ View live open trades
4. ✅ Make trades while away from your PC

**Start the dashboard and enjoy automated trading!**

---

## Need Help?

Check these files:
- `DASHBOARD_INTEGRATION_COMPLETE.md` - Full technical details
- `DASHBOARD_SETUP.md` - Remote access setup
- `bot_dashboard.py` - Dashboard source code
- `test_dashboard_api.py` - API test tool

---

**Happy Trading! 📈**
