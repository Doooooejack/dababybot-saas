# Trading Bot Server Setup Guide

## Overview
This guide helps you run your trading bot on a server with proper lifecycle management, health monitoring, and API control.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_server.txt
```

### 2. Start the Server
```bash
python bot_server_manager.py
```

The server will start on `http://localhost:8000`

### 3. API Documentation
Open your browser and go to: `http://localhost:8000/docs`

---

## API Endpoints

### Health Check
```
GET /api/health
```
Returns server and bot status.

### Bot Status
```
GET /api/bot/status
```
Returns current bot process status, PID, uptime, resource usage.

### Start Bot
```
POST /api/bot/start
```
Starts the trading bot process.

### Stop Bot
```
POST /api/bot/stop?force=false
```
Gracefully stops the bot. Set `force=true` to kill immediately.

### Restart Bot
```
POST /api/bot/restart?force=false
```
Restarts the bot process.

### Bot Logs
```
GET /api/bot/logs?lines=100
```
Returns last N lines of bot trading logs.

### Bot State
```
GET /api/bot/state
```
Returns current bot trading state (positions, trades, etc).

### WebSocket Updates
```
ws://localhost:8000/api/ws
```
Real-time bot status updates via WebSocket.

---

## Command-Line Usage

### Start Bot
```bash
curl -X POST http://localhost:8000/api/bot/start
```

### Stop Bot (Graceful)
```bash
curl -X POST http://localhost:8000/api/bot/stop
```

### Stop Bot (Force Kill)
```bash
curl -X POST "http://localhost:8000/api/bot/stop?force=true"
```

### Restart Bot
```bash
curl -X POST http://localhost:8000/api/bot/restart
```

### Get Logs
```bash
curl http://localhost:8000/api/bot/logs?lines=50
```

---

## Windows Service Setup

### Create Windows Service for Auto-Start

1. **Install NSSM** (Non-Sucking Service Manager):
```bash
# Download from: https://nssm.cc/download
# Or use choco:
choco install nssm
```

2. **Install Service**:
```bash
nssm install BotServer "C:\Python39\python.exe" "C:\path\to\bot_server_manager.py"
nssm set BotServer AppDirectory "C:\path\to\bot\directory"
nssm set BotServer AppStdout "C:\path\to\bot\logs\server.log"
nssm set BotServer AppStderr "C:\path\to\bot\logs\server_error.log"
```

3. **Start Service**:
```bash
nssm start BotServer
```

4. **Check Status**:
```bash
nssm status BotServer
```

5. **Stop Service**:
```bash
nssm stop BotServer
```

6. **Remove Service**:
```bash
nssm remove BotServer confirm
```

---

## Linux/Mac Service Setup

### Create SystemD Service

1. **Create service file**:
```bash
sudo nano /etc/systemd/system/bot-server.service
```

2. **Add content**:
```ini
[Unit]
Description=Trading Bot Server Manager
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/DABABYBOT
ExecStart=/usr/bin/python3 /home/youruser/DABABYBOT/bot_server_manager.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. **Enable and start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bot-server
sudo systemctl start bot-server
```

4. **Check status**:
```bash
sudo systemctl status bot-server
```

5. **View logs**:
```bash
sudo journalctl -u bot-server -f
```

---

## Docker Setup

### Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements_server.txt .
COPY requirements.txt . 2>/dev/null || true

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_server.txt

# Copy bot files
COPY . .

# Expose port
EXPOSE 8000

# Start server
CMD ["python", "bot_server_manager.py"]
```

### Build and Run Docker Image
```bash
# Build
docker build -t trading-bot-server .

# Run
docker run -d \
  --name bot-server \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  trading-bot-server

# Check logs
docker logs -f bot-server

# Stop
docker stop bot-server
```

---

## Monitoring

### Check Server Health
```bash
curl http://localhost:8000/api/health
```

### Watch Real-Time Status
Use WebSocket client or tool like `websocat`:
```bash
websocat ws://localhost:8000/api/ws
```

### Monitor Resource Usage
The `/api/bot/status` endpoint provides:
- Memory usage (MB)
- CPU usage (%)
- Number of threads
- Last heartbeat timestamp
- Uptime

---

## Troubleshooting

### Bot Won't Start
1. Check if bot script exists: `botfriday20000th.py`
2. Verify MT5 is installed and accessible
3. Check logs: `/api/bot/logs`
4. Ensure AutoTrading is enabled in MT5

### Server Won't Start
1. Check port 8000 is not in use:
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

2. Check dependencies:
```bash
pip install -r requirements_server.txt
```

3. Try different port:
Edit `bot_server_manager.py` and change `port=8000` to another port.

### Bot Process Keeps Dying
1. Check logs for errors: `/api/bot/logs`
2. Verify MT5 connection: `MetaTrader5.initialize()`
3. Check available disk space
4. Check system resources (RAM, CPU)

### WebSocket Connection Issues
1. Ensure firewall allows port 8000
2. Check browser console for errors
3. Try with different WebSocket client

---

## Advanced Configuration

### Custom Port
Edit `bot_server_manager.py`:
```python
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,  # Change port here
        log_level="info"
    )
```

### Multiple Bot Instances
Run multiple servers on different ports:
```bash
# Terminal 1
python bot_server_manager.py  # Port 8000

# Terminal 2 (after modifying port in code)
python bot_server_manager.py  # Port 8001
```

### Reverse Proxy (Nginx)
```nginx
upstream bot_servers {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://bot_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ws {
        proxy_pass http://bot_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Best Practices

1. **Always use graceful shutdown** (`force=false`) first
2. **Monitor resource usage** regularly
3. **Keep logs rotated** to prevent disk space issues
4. **Use a reverse proxy** for production
5. **Enable HTTPS** for API endpoints
6. **Implement authentication** for API access
7. **Set up alerts** for bot status changes
8. **Regular backups** of bot state and logs
9. **Test restarts** in non-trading hours
10. **Document your configuration** changes

---

## API Examples

### Python
```python
import requests

API_URL = "http://localhost:8000"

# Start bot
response = requests.post(f"{API_URL}/api/bot/start")
print(response.json())

# Get status
response = requests.get(f"{API_URL}/api/bot/status")
print(response.json())

# Get logs
response = requests.get(f"{API_URL}/api/bot/logs?lines=50")
print(response.json())

# Stop bot
response = requests.post(f"{API_URL}/api/bot/stop")
print(response.json())
```

### JavaScript
```javascript
const API_URL = "http://localhost:8000";

async function getBotStatus() {
    const response = await fetch(`${API_URL}/api/bot/status`);
    return response.json();
}

async function startBot() {
    const response = await fetch(`${API_URL}/api/bot/start`, {
        method: 'POST'
    });
    return response.json();
}

async function stopBot() {
    const response = await fetch(`${API_URL}/api/bot/stop`, {
        method: 'POST'
    });
    return response.json();
}

// WebSocket for real-time updates
const ws = new WebSocket("ws://localhost:8000/api/ws");

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Bot Status:", data.bot);
};
```

---

## Support & Updates

For updates and more information, check the official documentation or contact support.

Last Updated: 2026-01-06
Version: 1.0.0
