# 🚀 DABABYBOT Quick Start Guide

## Using Virtual Environment (.venv)

Your bot is configured to run with the `.venv` virtual environment which has all dependencies pre-installed.

### **Quick Start (Recommended)**

#### Option 1: PowerShell (Recommended for Windows)
```powershell
# Navigate to the bot directory
cd "e:\DABABYBOT!\DABABYBOT!"

# Run the startup script
.\START_BOT.ps1
```

#### Option 2: Command Prompt (Windows)
```cmd
cd e:\DABABYBOT!\DABABYBOT!
START_BOT.bat
```

#### Option 3: Manual PowerShell
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run the bot
python botfriday990000th.py
```

#### Option 4: Direct Python Execution
```powershell
# Use the venv python directly
.\.venv\Scripts\python.exe botfriday990000th.py
```

---

## Keyboard Controls During Runtime

| Key | Action |
|-----|--------|
| **Ctrl+C** | Graceful shutdown |
| **s + Enter** | Toggle market bypass (skip market closed checks) |
| **x + Enter** | Stop bot |

---

## What's Included in .venv

The virtual environment has all these packages pre-installed:

- ✅ MetaTrader5
- ✅ pandas
- ✅ numpy
- ✅ scikit-learn
- ✅ lightgbm
- ✅ xgboost
- ✅ requests
- ✅ joblib

---

## Troubleshooting

### If `.venv` doesn't activate:
```powershell
# Create it from backup
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

### If you get permission denied on PS1 files:
```powershell
# Temporarily allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Check which Python is being used:
```powershell
.\.venv\Scripts\python.exe --version
```

---

## Bot Log Files

Once running, check these for output:
- `bot_log.txt` - Main bot logs
- `bot_heartbeat.log` - Ping/health checks
- `bot_state.json` - Current trading state

---

**Last Updated**: April 1, 2026  
**Bot Version**: botfriday990000th.py
