# Remote Access Setup Guide

Access your bot dashboard from anywhere in the world — any country, any network!

## Quick Start (One Command)

```powershell
python setup_remote_access.py
```

That's it! The script will:
1. Install Cloudflare Tunnel (if needed)
2. Create a secure tunnel to your dashboard
3. Generate a public HTTPS URL you can share
4. Run forever in the background

## What You Get

✅ **Access from anywhere** — Work on your bot from any country  
✅ **Secure HTTPS** — All data encrypted  
✅ **No port forwarding** — No networking complexity  
✅ **Always available** — 24/7 uptime  
✅ **Share access** — Give others the public URL  

## How It Works

The script uses **Cloudflare Tunnel**, a free service that:
- Creates a secure connection from your computer to Cloudflare's global network
- Generates a unique public URL (e.g., `https://my-bot.trycloudflare.com`)
- Requires only a browser, no VPN or complex setup

## After Setup

1. **Copy your public URL** from the terminal output
2. **Open in any browser** from any device/country
3. **Share the URL** with anyone you trust
4. **URL persists** across restarts (same URL each time)

## Manual Steps (if needed)

1. Download Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
2. Run setup script: `python setup_remote_access.py`
3. Follow the on-screen prompts

## Verify It's Working

Local access:
```
http://127.0.0.1:5000
```

Remote access (after setup):
```
https://your-tunnel-url.trycloudflare.com
```

## Troubleshooting

**"cloudflared not found"**
- Run `python setup_remote_access.py` again to install it

**"Connection refused"**
- Make sure `bot_dashboard.py` is running on port 5000
- Check: `http://127.0.0.1:5000` locally first

**"Tunnel URL changes"**
- By default, tunnels are temporary. To keep the same URL forever:
  - Create a Cloudflare account (free)
  - Configure a permanent domain
  - See: https://developers.cloudflare.com/cloudflare-one/setup/

## Command Reference

Start the dashboard:
```powershell
python .\bot_dashboard.py
```

Set up remote access:
```powershell
python .\setup_remote_access.py
```

Check logs:
```powershell
Get-Content .\dashboard.log -Tail 50
```

Stop everything (Ctrl+C in terminal windows)

## Security Notes

- The tunnel URL is unique and difficult to guess
- Only share the URL with people you trust
- HTTPS protects your data in transit
- The local port 5000 is only accessible to you

## Questions?

See Cloudflare Tunnel docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
