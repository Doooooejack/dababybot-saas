Bot Dashboard & Remote Access
=============================

This directory contains a minimal Flask dashboard (`bot_dashboard.py`) that exposes simple
API endpoints to start/stop your trading bot and check status. `setup_remote_access.py` can
be used to create a Cloudflare Tunnel which exposes the dashboard to the internet securely.

Quick start
-----------

1. Install dependencies (recommend using a virtualenv):

```powershell
python -m pip install -r requirements.txt
```

2. Edit `dashboard_config.json` and set `trading_bot_cmd` to the command that runs your trading bot, e.g.:

```json
{
  "trading_bot_cmd": "python my_trading_bot.py",
  "api_token": "replace-with-strong-token"
}
```

3. (Optional) Set `BOT_DASHBOARD_TOKEN` environment variable to override the token:

```powershell
setx BOT_DASHBOARD_TOKEN "your_secret_token"
```

4. Run the dashboard locally:

```powershell
python bot_dashboard.py
```

5. Expose the dashboard via Cloudflare Tunnel (use `setup_remote_access.py`):

```powershell
python setup_remote_access.py
```

Security notes
--------------
- The dashboard uses a simple token-based auth. Use a strong token and keep it secret.
- For production, run behind a proper WSGI server (gunicorn/uWSGI) and enable TLS (Cloudflare handles TLS when using a tunnel).

Next steps I can do for you
---------------------------
- Integrate a stronger authentication flow (OAuth, Cloudflare Access, or JWT).
- Add WebSocket updates for live bot metrics.
- Create a Windows service / systemd unit to run the dashboard and tunnel on boot.
