# Local Dashboard for Trading Bot

Files added under `dashboard/`:
- `app.py` - Flask dashboard and API to start/stop the bot subprocess
- `config.py` - Dashboard API key (change before exposing)
- `templates/index.html` - Simple web UI
- `requirements.txt` - Python dependencies
- `run_dashboard.ps1` - PowerShell helper to run the dashboard
- `dashboard_bot.log` - runtime log created when the bot runs

Quick start (Windows PowerShell):

1. Install Python dependencies (recommended in a virtualenv):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r dashboard\requirements.txt
```

2. Set a strong API key in `dashboard/config.py` or as an environment variable:

```powershell
$env:DASHBOARD_API_KEY = 'YOUR_STRONG_KEY'
```

3. Start the dashboard:

```powershell
cd dashboard
python app.py
# or: .\run_dashboard.ps1
```

4. Open `http://localhost:5000` in your browser and enter the API key.

Exposing remotely (NOT RECOMMENDED without hardening):
Exposing remotely (NOT RECOMMENDED without hardening):
- Use `ngrok` to expose port 5000 for quick remote access: see `dashboard/ngrok_start.ps1`.
- For secure access, host the dashboard behind a VPN or on a cloud VM with firewall rules and HTTPS.

Security notes:
Start/stop is performed via a graceful stop-request mechanism:
- The dashboard writes a `dashboard/stop.signal` file to request a graceful shutdown.
- The bot checks for the stop file (and Unix signals) and exits cleanly (closes MT5, flushes logs).
- If the bot does not exit within a timeout, the dashboard will force-terminate the process.

Use the PowerShell helper to start an ngrok tunnel (if you have ngrok installed):

```powershell
cd dashboard
.\ngrok_start.ps1
```

Security reminder: exposing your trading bot to the internet carries significant risk. Always use a VPN or secure VM, strong credentials, and limit access by IP where possible.

How control works:
- The dashboard starts `botfriday6000th.py` as a subprocess using the same Python executable.
- Logs are written to `dashboard_bot.log` in the project root.
- Start/stop is performed via `subprocess` termination; for graceful stop implement a `--stop` signal handler in the bot if needed.
