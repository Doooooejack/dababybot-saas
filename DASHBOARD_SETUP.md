# Bot Dashboard Setup Guide

## Quick Start

### 1. Install Required Packages
```powershell
pip install flask flask-cors
```

### 2. Start the Dashboard
```powershell
cd c:\Users\JEFFKID\Desktop\dabbay
python bot_dashboard.py
```

You should see:
```
 ╔═══════════════════════════════════════════════════════════╗
 ║       BOT DASHBOARD - Phone Control Interface              ║
 ╚═══════════════════════════════════════════════════════════╝
 
 📱 Access dashboard:
    - From this PC:  http://localhost:5000
    - From phone:    http://<your-pc-ip>:5000
```

### 3. Find Your PC's IP Address
```powershell
ipconfig
```
Look for "IPv4 Address" (typically looks like `192.168.x.x` or `10.0.x.x`)

Example: `192.168.1.100`

### 4. Access from Phone/Tablet
Open browser on your phone and go to:
```
http://192.168.1.100:5000
```

## Features

✅ **Real-time Status** — Balance, P&L, equity, win rate  
✅ **Start/Stop** — Control bot from anywhere  
✅ **Pause/Resume** — Pause trading without stopping the bot  
✅ **Symbol Toggle** — Enable/disable specific trading pairs  
✅ **Open Trades** — View all open positions  
✅ **Close Trades** — Close positions from dashboard  
✅ **News & Events** — Check economic events for each symbol  
✅ **Live Logs** — See bot activity in real-time  
✅ **Settings** — Adjust bot parameters  

## Integration with Your Bot

The dashboard reads bot state from a JSON file. To make it work:

### Option A: Update Your Bot to Write State File
Add this to your `botfriday6000th.py`:

```python
import json

def save_bot_state():
    """Save current bot state for dashboard"""
    state = {
        'running': True,  # or False
        'trading_paused': False,
        'account_balance': 10000.0,
        'equity': 10125.50,
        'daily_pnl': 125.50,
        'open_trades': [],  # List of {'symbol': 'EURUSD', 'entry': 1.0850, 'pnl': 25.0}
        'total_trades': 42,
        'wins': 28,
        'losses': 14,
        'active_symbols': ['XAUUSD.m', 'EURUSD.m', 'GBPUSD.m'],
        'status_log': []
    }
    with open('bot_state.json', 'w') as f:
        json.dump(state, f)

# Call this periodically in your main loop:
save_bot_state()
```

### Option B: Use the API to Control Bot
The dashboard has endpoints you can call from your bot:
- `POST /api/start` - Start trading
- `POST /api/stop` - Stop trading  
- `POST /api/pause` - Pause trading
- `POST /api/close-trade/<id>` - Close a specific trade

## Running on Startup

### Windows: Add to Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: On log on
4. Action: Start program `python.exe` with arguments:
   ```
   c:\Users\JEFFKID\Desktop\dabbay\bot_dashboard.py
   ```

### Or Create a .bat File
Create `start_dashboard.bat`:
```batch
@echo off
cd c:\Users\JEFFKID\Desktop\dabbay
python bot_dashboard.py
pause
```
Double-click to run.

## Security Notes

⚠️ **Current Setup:**
- Dashboard is accessible to anyone on your network
- No authentication required

✅ **For Production:**
- Add username/password authentication
- Use HTTPS (SSL certificate)
- Run on private VPN or restrict IP access
- Never expose to the internet without proper security

### Add Basic Authentication (Optional)
```python
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    if username == 'admin' and password == 'your_password':
        return username

@app.route('/api/status')
@auth.login_required
def get_status():
    # ... your code
```

## Troubleshooting

### "Port already in use"
Change port in `bot_dashboard.py`:
```python
app.run(host='0.0.0.0', port=5001, debug=True)  # Use 5001 instead
```

### "Cannot connect from phone"
1. Check both devices are on same WiFi
2. Verify Windows Firewall isn't blocking port 5000:
   - Open Settings → Privacy & Security → Windows Firewall
   - Click "Allow an app through firewall"
   - Add `python.exe`

### Dashboard shows outdated data
- Make sure bot is calling `save_bot_state()` regularly
- Check that `bot_state.json` is being updated

## Next Steps

1. ✅ Dashboard running
2. ⏭️ Integrate bot state saving (see "Integration" section above)
3. ⏭️ Add authentication for security
4. ⏭️ Deploy to cloud (optional) for access from anywhere

## Support

If you encounter issues, check:
- Flask is installed: `pip show flask`
- Port 5000 is open: `netstat -an | findstr 5000`
- Bot state file exists: `bot_state.json`
