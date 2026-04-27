# DababyBot SaaS - Cloud Deployment Guide

## Option 1: Deploy to Heroku (Recommended - Easiest)

### Prerequisites
- Heroku account (free tier available)
- GitHub account
- Heroku CLI installed

### Step 1: Prepare for Deployment
```bash
# Add to your repo
git add .
git commit -m "Add SaaS platform"

# Login to Heroku
heroku login
```

### Step 2: Create Heroku App
```bash
heroku create dababybot-saas
```

### Step 3: Add Database (PostgreSQL)
```bash
# Add free Postgres add-on
heroku addons:create heroku-postgresql:hobby-dev

# Verify it's added
heroku addons
```

### Step 4: Set Environment Variables
```bash
heroku config:set SECRET_KEY=$(openssl rand -hex 32)
heroku config:set JWT_SECRET_KEY=$(openssl rand -hex 32)
heroku config:set STRIPE_SECRET_KEY=sk_live_your_key
heroku config:set STRIPE_WEBHOOK_SECRET=whsec_your_secret
heroku config:set ENVIRONMENT=production
```

### Step 5: Deploy
```bash
git push heroku main
```

### Step 6: Initialize Database
```bash
heroku run python -c "from bot_platform import app, db; db.create_all()" -a dababybot-saas
```

### Step 7: Access Your App
```
https://dababybot-saas.herokuapp.com
```

---

## Option 2: Deploy to DigitalOcean (More Control - Better Value)

### Prerequisites
- DigitalOcean account
- $5-10/month for a basic droplet
- SSH client

### Step 1: Create Droplet
1. Go to DigitalOcean Dashboard
2. Create → Droplets
3. Choose: Ubuntu 22.04 LTS → $5/month plan → Add SSH key
4. Create Droplet

### Step 2: SSH into Server
```bash
ssh root@your_droplet_ip
```

### Step 3: Install Dependencies
```bash
# Update system
apt update && apt upgrade -y

# Install Python, Nginx, etc.
apt install -y python3-pip python3-venv nginx git postgresql postgresql-contrib

# Create app directory
mkdir -p /var/www/dababybot
cd /var/www/dababybot
```

### Step 4: Clone Repository
```bash
git clone https://github.com/yourusername/dababybot-saas.git .
```

### Step 5: Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 6: Setup PostgreSQL
```bash
sudo -u postgres psql

CREATE DATABASE dababybot_saas;
CREATE USER dbuser WITH PASSWORD 'strong_password_here';
ALTER ROLE dbuser SET client_encoding TO 'utf8';
ALTER ROLE dbuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE dbuser SET default_transaction_deferrable TO on;
ALTER ROLE dbuser SET default_transaction_read_only TO off;
GRANT ALL PRIVILEGES ON DATABASE dababybot_saas TO dbuser;
\q
```

### Step 7: Create .env File
```bash
cat > /var/www/dababybot/.env << EOF
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here
DATABASE_URL=postgresql://dbuser:strong_password_here@localhost:5432/dababybot_saas
STRIPE_SECRET_KEY=sk_live_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret
ENVIRONMENT=production
DOMAIN=your_domain.com
EOF
```

### Step 8: Initialize Database
```bash
source venv/bin/activate
python -c "from bot_platform import app, db; app.app_context().push(); db.create_all()"
```

### Step 9: Setup Gunicorn Service
```bash
cat > /etc/systemd/system/dababybot.service << EOF
[Unit]
Description=DababyBot SaaS Platform
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/dababybot
ExecStart=/var/www/dababybot/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 bot_platform:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl enable dababybot
systemctl start dababybot
systemctl status dababybot
```

### Step 10: Setup Nginx
```bash
cat > /etc/nginx/sites-available/dababybot << EOF
server {
    listen 80;
    server_name your_domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias /var/www/dababybot/static/;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/dababybot /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Step 11: Setup SSL (Free with Let's Encrypt)
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your_domain.com
```

### Step 12: Setup Automatic Renewal
```bash
systemctl enable certbot.timer
systemctl start certbot.timer
```

---

## Option 3: Deploy to AWS (Advanced - Scalable)

### Simple EC2 + RDS Setup

1. **Create EC2 Instance**
   - AMI: Ubuntu 22.04 LTS
   - Instance Type: t3.micro (free tier)
   - Security Group: Allow ports 80, 443, 22

2. **Create RDS Database**
   - Engine: PostgreSQL
   - Template: Free tier
   - Instance: db.t3.micro

3. **Connect & Setup** (same as DigitalOcean Option 2)

4. **Use Elastic IP** for static IP address

---

## Domain Setup (All Options)

### Add Custom Domain to Heroku
```bash
heroku domains:add www.yourdomain.com
```

Then add CNAME record in your DNS provider:
```
www.yourdomain.com CNAME your-app-name.herokuapp.com
```

### Add Custom Domain to DigitalOcean/AWS
Just point your domain's A record to your server's IP.

---

## SSL Certificate (HTTPS)

### Heroku
- Automatic SSL provided on herokuapp.com domain
- Free SSL with custom domain included

### DigitalOcean/AWS
- Use Let's Encrypt (free, shown in setup above)
- Or purchase certificate from AWS Certificate Manager (free for AWS resources)

---

## Monitoring & Logs

### Heroku
```bash
# View logs
heroku logs --tail

# Scale dynos
heroku ps:scale web=2

# View metrics
heroku metrics
```

### DigitalOcean/AWS
```bash
# View app logs
journalctl -u dababybot -f

# View Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Monitor system
top
df -h
free -h
```

---

## Backup & Recovery

### Database Backups

**Heroku:**
```bash
heroku pg:backups capture
heroku pg:backups download
```

**DigitalOcean:**
```bash
# Manual backup
pg_dump -U dbuser dababybot_saas > backup.sql

# Scheduled backups (via DigitalOcean Spaces or external service)
```

---

## Performance Optimization

### Enable Caching
```python
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/trade-stats')
@cache.cached(timeout=300)
def get_stats():
    ...
```

### Use CDN for Static Files
- Heroku: Use Cloudflare (free)
- DigitalOcean: Use S3 + CloudFront
- AWS: Native CloudFront integration

### Database Optimization
```sql
-- Create indexes for frequently queried columns
CREATE INDEX idx_user_id ON trades(user_id);
CREATE INDEX idx_user_subscription ON users(subscription_plan);
CREATE INDEX idx_trade_timestamp ON trades(created_at);
```

---

## Scaling for 1000+ Users

### Heroku
- Upgrade from hobby dyno to standard
- Use performance add-ons
- Implement caching layer (Redis)

### DigitalOcean
- Upgrade droplet size
- Add load balancer
- Use managed Postgres
- Separate bot instances to different servers

### AWS
- Add RDS read replicas
- Use Auto Scaling groups
- Implement ElastiCache (Redis)
- Use Lambda for bot instances

---

## Troubleshooting

### App won't start
```bash
heroku logs --tail  # Check logs
heroku run bash     # Debug in production
```

### Database connection error
- Verify DATABASE_URL is set correctly
- Check database credentials
- Ensure database exists

### SSL certificate issues
```bash
certbot renew --force-renewal
systemctl restart nginx
```

### Bot instances not running
- Check bot logs
- Verify MT5 credentials
- Check subprocess permissions

---

## Next Steps

1. Choose your deployment option
2. Follow the setup steps
3. Set environment variables
4. Deploy your app
5. Test login: `/login`
6. Test trader portal: `/dashboard`
7. Access admin panel: `/admin` (with admin account)

**That's it! Your SaaS is now live! 🚀**
