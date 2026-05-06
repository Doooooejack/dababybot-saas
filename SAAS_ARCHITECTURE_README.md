# DABABYBOT SaaS Architecture

## Overview

DABABYBOT now uses a **hybrid SaaS architecture** where:

- **Web Service** (runs on Render/Linux): User management, subscriptions, web dashboard
- **Trading VPS** (Windows server per user): MT5 connection and trading execution

This solves the mobile/remote user problem by providing each user with their own dedicated Windows VPS for trading.

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Render Cloud  │    │  Windows VPS    │
│   (Any Device)  │    │   (Linux)       │    │   (Per User)    │
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

1. **User registers** via web dashboard on any device (phone, tablet, desktop)
2. **User gets assigned** a dedicated Windows VPS with MT5 pre-installed
3. **MT5 credentials are configured** through the web dashboard
4. **Trading bot runs 24/7** on the user's VPS, connecting to their MT5 account
5. **All trading data syncs** back to the web dashboard for monitoring
6. **User can control bot** from any device via web interface

## Setup Instructions

### For Users

1. **Sign up** on the web dashboard (works on any device)
2. **Configure MT5 credentials** through the web interface
3. **Get assigned** a personal Windows VPS automatically
4. **Start trading** - bot runs automatically on your VPS
5. **Monitor performance** from any device via web dashboard

### For Administrators

#### 1. Deploy Web Service to Render

Follow the deployment guide in `DEPLOYMENT_RENDER.md`

#### 2. Set Up VPS Infrastructure

You'll need a VPS provider that offers Windows servers:

**Recommended Providers:**
- AWS EC2 Windows instances
- DigitalOcean Droplets (Windows option)
- Vultr Windows VPS
- Hetzner Windows VPS
- Contabo Windows VPS

**VPS Requirements:**
- Windows Server 2019/2022 or Windows 10/11 Pro
- At least 2GB RAM, 1 CPU core per user
- MT5 platform installed
- Python 3.8+ installed
- 24/7 uptime guarantee

#### 3. Deploy Trading Client to VPS

For each user VPS, install:
- MT5 terminal
- Python environment
- DABABYBOT trading client
- Auto-start configuration

### VPS Client Setup Script

Create `setup_vps_client.ps1` for automated VPS setup:

```powershell
# Download and install MT5
# Install Python and dependencies
# Copy trading client files
# Configure auto-start
# Set up API communication with web service
```

## Key Benefits

✅ **Mobile-Friendly**: Users can access from phones/tablets
✅ **Fully Cloud-Based**: No local software installation required
✅ **Real MT5 Connections**: Trading works on dedicated Windows servers
✅ **Scalable**: Each user gets their own VPS
✅ **Secure**: Isolated environments per user
✅ **24/7 Trading**: Bots run continuously on VPS

## VPS Management

### Automated Provisioning

When a user signs up:
1. Web service provisions new Windows VPS
2. Installs MT5 and trading client automatically
3. Configures user-specific settings
4. Provides connection details to user

### Cost Structure

- **Web Service**: $7/month on Render
- **Windows VPS per user**: $10-20/month depending on provider
- **Total per user**: $17-27/month

### Monitoring & Maintenance

- **Health Checks**: Web service monitors all VPS clients
- **Auto-Restart**: Failed bots automatically restart
- **Updates**: Push client updates to all VPS instances
- **Backup**: Regular MT5 data backups

## Security Considerations

- **Isolated VPS**: Each user on separate Windows server
- **Encrypted Communication**: All API calls use HTTPS
- **MT5 Credentials**: Stored encrypted, never transmitted in plain text
- **Access Control**: Users only access their own VPS via web interface
- **Firewall**: Strict firewall rules on all VPS instances

```
DABABYBOT/
├── bot_platform.py              # Web service (Flask app)
├── dababybot_vps_client.py      # VPS Windows client (auto-deployed)
├── botMayl999990000th.py        # Main trading bot logic
├── dashboard_enhanced.html      # Web dashboard
├── requirements.txt             # Python dependencies
├── setup_vps_client.ps1         # VPS setup automation script
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

### VPS Connection Issues
- Check VPS server status and network connectivity
- Verify MT5 terminal is running on VPS
- Confirm API keys and endpoints are correct
- Check firewall settings allow outbound connections

### MT5 Connection Issues
- Verify account credentials are correct
- Check MT5 server settings (Demo vs Live)
- Ensure MT5 terminal has market data access
- Confirm VPS timezone matches broker requirements

### Performance Issues
- Monitor VPS resource usage (CPU, RAM, disk)
- Check for MT5 platform updates
- Verify internet connection stability
- Review trading frequency and API rate limits

## Security Notes

- MT5 passwords are stored encrypted in production
- JWT tokens expire after 30 days
- All API calls require authentication
- Rate limiting prevents abuse
- HTTPS enforced in production

## Support

For technical issues:
1. Check VPS logs via web dashboard
2. Verify MT5 terminal status on VPS
3. Review API response logs
4. Contact support with VPS ID and error details

---

**DABABYBOT SaaS** - Professional algorithmic trading accessible from anywhere! 📱💻🖥️