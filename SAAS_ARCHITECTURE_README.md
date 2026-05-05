# DABABYBOT SaaS Architecture

## Overview

DABABYBOT now uses a **SaaS (Software as a Service) architecture** where:

- **Web Service** (runs on Render/Linux): User management, subscriptions, web dashboard
- **Local Client** (runs on Windows): MT5 connection and trading execution

This solves the problem of MT5 only working on Windows while allowing cloud deployment.

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Render Cloud  │    │  Windows Local  │
│                 │    │   (Linux)       │    │   (MT5)         │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • User Login    │◄──►│ • User Auth     │    │ • MT5 Connect   │
│ • Dashboard     │    │ • Subscriptions │    │ • Trading Bot   │
│ • Bot Control   │    │ • Data Storage  │    │ • Live Trading   │
│ • View Logs     │    │ • API Endpoints │    │ • Account Sync   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
       │                       │                       │
       └───────────────────────┼───────────────────────┘
                               ▼
                       SQLite Database
```

## How It Works

1. **User registers/logs in** via web dashboard on Render
2. **MT5 credentials are stored** securely in the cloud database
3. **User configures trading** (symbols, risk settings) via web interface
4. **Local client connects** to web service API to get credentials
5. **Local client connects to MT5** and starts trading
6. **Trading data syncs** back to cloud for dashboard viewing

## Setup Instructions

### 1. Deploy Web Service to Render

Follow the deployment guide in `DEPLOYMENT_RENDER.md`

### 2. Run Local Client on Windows

```bash
# On your Windows machine with MT5 installed
python dababybot_local_client.py
```

The client will prompt for:
- Web service URL (your Render app URL)
- Your username
- Your password

### 3. Start Trading

1. Log into web dashboard
2. Configure MT5 credentials
3. Set trading symbols and risk settings
4. Click "Start Bot" (configures for local startup)
5. Run local client on Windows
6. Trading begins automatically

## Key Benefits

✅ **MT5 Compatibility**: Trading works on Windows where MT5 is available
✅ **Cloud Management**: User accounts, subscriptions, and data in cloud
✅ **Real-time Sync**: Account balances and trading data sync to dashboard
✅ **Scalable**: Multiple users can run bots simultaneously
✅ **Secure**: MT5 credentials stored securely, trading happens locally

## File Structure

```
DABABYBOT/
├── bot_platform.py              # Web service (Flask app)
├── dababybot_local_client.py    # Local Windows client
├── botMayl999990000th.py        # Main trading bot logic
├── dashboard_enhanced.html      # Web dashboard
├── requirements.txt             # Python dependencies
├── DEPLOYMENT_RENDER.md         # Render deployment guide
└── Procfile                     # Render startup config
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

### User Management
- `GET /api/user/profile` - Get user profile
- `POST /api/user/mt5-connect` - Store MT5 credentials

### Bot Control
- `POST /api/bot/start` - Configure bot for local startup
- `POST /api/bot/stop` - Stop bot
- `GET /api/bot/status` - Get bot status
- `GET /api/bot/logs` - Get trading logs

### Subscription
- `POST /api/subscription/activate-key` - Activate subscription

## Troubleshooting

### Web Service Issues
- Check Render logs for errors
- Verify environment variables are set
- Ensure database file has write permissions

### Local Client Issues
- Ensure MT5 is installed and running
- Check internet connection for API calls
- Verify MT5 credentials are correct
- Check Windows firewall allows connections

### MT5 Connection Issues
- Verify account number, server, and password
- Check MT5 terminal is not already connected
- Try different MT5 server (Demo vs Live)

## Security Notes

- MT5 passwords are stored encrypted in production
- JWT tokens expire after 30 days
- All API calls require authentication
- Rate limiting prevents abuse
- HTTPS enforced in production

## Support

For issues:
1. Check the logs in `dababybot_local.log`
2. Verify MT5 terminal is working
3. Check web service status on Render
4. Review API responses for error messages

---

**DABABYBOT SaaS** - Professional algorithmic trading for everyone! 🚀