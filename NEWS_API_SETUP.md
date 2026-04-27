# News API Integration Setup

Your trading bot now includes real-time news filtering for economic events. Follow these steps to set it up.

## Option 1: Using NewsAPI (Recommended for Easy Setup)

### Step 1: Get a Free NewsAPI Key
1. Go to https://newsapi.org/
2. Sign up for a free account (100 requests/day limit)
3. Copy your API key from the dashboard

### Step 2: Configure the Environment Variable
**On Windows PowerShell:**
```powershell
$env:NEWSAPI_KEY = "your-api-key-here"
python c:\Users\JEFFKID\Desktop\dabbay\botfriday6000th.py
```

**Persistent setup (add to your system):**
1. Open "Environment Variables" on Windows
2. Create new user variable: `NEWSAPI_KEY` = `your-api-key-here`
3. Restart PowerShell/terminal and run the bot

### Step 3: Test the News Module
```powershell
cd c:\Users\JEFFKID\Desktop\dabbay
python news_module.py
```

You should see:
```
[TEST] Fetching articles for EURUSD...
  - [Article title]
  - [Article title]

[TEST] Checking economic events for EURUSD...
  - NFP (Employment) at 2025-12-05 12:30:00+00:00 (high)

[TEST] Checking news sentiment for EURUSD...
  Sentiment: neutral (score: 0.00)

[TEST] Should block trade for EURUSD?
  Block: True, Reason: High-impact economic event: NFP (Employment)
```

## Option 2: Using Only Economic Calendar (No API Key Needed)

The bot includes a **hardcoded economic calendar** with major events:
- **NFP** (Non-Farm Payroll) - First Friday, 12:30 UTC
- **CPI** (Consumer Price Index) - 13th of month, 12:30 UTC
- **FOMC** (Federal Reserve) - 3rd Wednesday, 18:00 UTC
- **ECB** (European Central Bank) - 1st Thursday, 13:45 UTC
- **BOE** (Bank of England) - Thursdays, 12:00 UTC
- **BOJ** (Bank of Japan) - Fridays, 08:30 UTC
- **RBA** (Reserve Bank Australia) - 1st Tuesday, 05:30 UTC

Even without NewsAPI, the bot will:
- Block trades 30 minutes before/after high-impact events
- Log which events are approaching
- Use the economic calendar for trade filtering

## Features

### What the News Module Does

1. **Fetches Real-Time News** (if NewsAPI configured)
   - Searches for news related to your trading symbols
   - Caches results for 5 minutes to avoid API rate limits
   - Analyzes sentiment (bullish/bearish/neutral)

2. **Detects Economic Events** (always active)
   - Checks if current time is near a major economic release
   - Automatically blocks trades within ±30 minutes of events
   - Supports all major forex pairs and gold

3. **Integrates with Trading Logic**
   - Automatically skips trade entries near news events
   - Logs all blocked trades with reason
   - Respects your trade confirmation requirements

### Example Output in Bot Logs

```
[NEWS] Fetched 8 articles for EURUSD
[NEWS] Blocking trade on EURUSD: High-impact economic event: ECB Decision
[EURUSD] Trade not placed: High-impact economic event: ECB Decision
[NEWS] Sentiment check: bullish (score: 0.45)
```

## Customization

### Adjust News Blocking Window
Edit `botfriday6000th.py` and change:
```python
# Look back 30 minutes, look ahead 15 minutes by default
should_block_trade_due_to_news(symbol, minutes_before=30, minutes_after=15)
```

### Add More Economic Events
Edit `news_module.py` in the `MAJOR_EVENTS` dictionary to add custom events:
```python
MAJOR_EVENTS = {
    ("nfp", 0, 12, 30, "USD", "NFP (Employment)", "high"),
    # Add your custom events here
}
```

### Increase NewsAPI Rate Limit
- Upgrade your NewsAPI plan at https://newsapi.org/pricing
- Paid plans offer 10,000+ requests/day

## Troubleshooting

### "news_module not found" warning
- Ensure `news_module.py` is in the same folder as `botfriday6000th.py`
- The bot will still work using the economic calendar fallback

### "NEWSAPI_KEY not configured" message
- Set the environment variable `NEWSAPI_KEY` and restart the bot
- Or proceed without it; the hardcoded calendar will still filter trades

### API quota exceeded
- Wait for the next day (resets at UTC midnight)
- Or switch to paid NewsAPI plan
- The bot will still use the economic calendar as a fallback

## Files

- `news_module.py` - Core news API integration
- `botfriday6000th.py` - Updated with news filtering
- `NEWS_API_SETUP.md` - This file

## Next Steps

1. Get your free NewsAPI key (optional but recommended)
2. Set the `NEWSAPI_KEY` environment variable
3. Run the bot; it will automatically filter trades around economic events
4. Monitor logs to see news-related trade blocks
