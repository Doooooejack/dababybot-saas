# Licensing & Distribution Guide

## Quick Start

### 1. Generate RSA Keys (One-Time Setup)

```bash
cd D:\DABABYBOT!
python generate_keys.py
```

This creates `private.pem` (server-side) and `public.pem` (shared with clients).

### 2. Run License Server + Bot Server Locally

```bash
pip install -r requirements_license.txt -r requirements_server.txt

# Terminal 1: License Server (port 9000)
python license_server.py

# Terminal 2: Bot Server (port 8000)
python bot_server_manager.py
```

### 3. Create a Test License Token

```bash
python issue_license.py user@example.com --days 30 --country US
```

This outputs a JWT token. Save it to `license.json`:

```json
{
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 4. Start Bot via API

With `license.json` in place, the bot server will accept license validation on startup:

```bash
curl -X POST http://localhost:8000/api/bot/start
```

---

## Production Deployment

### Docker (Recommended)

1. **Generate keys:**
   ```bash
   python generate_keys.py
   ```

2. **Create `.env`:**
   ```bash
   cp .env.example .env
   # Edit .env with your LICENSE_TOKEN, STRIPE_SECRET_KEY, etc.
   ```

3. **Build and run:**
   ```bash
   docker-compose up -d
   ```

This starts:
- **Bot Server** on `localhost:8000` (dashboard at `/`)
- **License Server** on `localhost:9000` (`/issue`, `/validate`, `/revoke`, `/public_key`)

### Keys

- **private.pem** – Keep secret, on license server only.
- **public.pem** – Share with bot clients for token validation.

---

## Stripe Integration

### 1. Set Webhook

Go to Stripe Dashboard → Webhooks → Add endpoint:
- **URL**: `https://yourserver.com:9000/webhook/stripe`
- **Events**: `charge.succeeded`, `customer.subscription.created`

### 2. Environment Variables

```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 3. Create Products & Prices

```bash
python stripe_integration.py
```

This creates trial (free), monthly ($49), and yearly ($499) plans and outputs price IDs.

### 4. Generate Checkout Link

Use Stripe Checkout to sell licenses. On successful payment, the webhook triggers and auto-issues a JWT.

---

## License Token Claims

Each JWT includes:

```json
{
  "sub": "user@example.com",        // User email/ID
  "country": "US",                  // Allowed country ("*" = all)
  "features": ["paper_trading"],    // Enabled features
  "exp": 1704067200,                // Expiry timestamp
  "iat": 1703462400,                // Issued at
  "jti": "uuid"                     // Unique revocation ID
}
```

---

## Revocation

Revoke a license (disable immediately):

```bash
curl -X POST http://license-server:9000/revoke/jti-value
```

The bot checks revocation list on every 24-hour revalidation.

---

## Client Setup

1. Obtain license token from your server (via Stripe webhook or `/issue` endpoint).
2. Save to `license.json` or set `LICENSE_TOKEN` env var.
3. Start bot server: `python bot_server_manager.py`
4. Access dashboard: `http://localhost:8000/`

---

## Multi-Country Compliance

- **VAT**: Stripe handles VAT for EU/UK.
- **Export Controls**: Ensure trading software is not restricted in target countries.
- **GDPR**: Implement privacy policy, data retention, user consent.
- **KYC/AML**: For large customers or crypto/forex, may require identity verification.

Consult a legal advisor for your target markets.

---

## Monitoring

Check logs:

```bash
tail -f bot_server.log    # Bot server logs
tail -f bot_trading.log   # Bot trading logs
```

Validate license online (optional):

```bash
curl -X POST "http://license-server:9000/validate?token=..."
```

---

## Updates & Rotation

### Key Rotation

1. Generate new keys: `python generate_keys.py`
2. Update `public.pem` in clients.
3. Update `private.pem` on license server (or use secrets manager).
4. Reissue licenses with new key to active customers.

### Bot Updates

Rebuild Docker image and redeploy:

```bash
docker-compose down
docker-compose up -d --build
```
