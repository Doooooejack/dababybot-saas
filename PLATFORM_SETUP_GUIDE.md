# DababyBot SaaS Platform - Setup Guide

## Quick Start (5 Steps)

### Step 1: Install Dependencies
```bash
pip install flask flask-cors flask-sqlalchemy flask-jwt-extended werkzeug
```

### Step 2: Create .env file
```bash
# .env
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=sqlite:///botplatform.db
PORT=5000
BOT_DASHBOARD_PORT=5001
```

### Step 3: Initialize Database
```python
from bot_platform import app, db

with app.app_context():
    db.create_all()
    print("Database created!")
```

### Step 4: Run the Backend
```bash
python bot_platform.py
```

Backend runs at: `http://localhost:5000`

### Step 5: Build Login Page + Integrate Frontend

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│         USER DEVICES (Phone/PC/Laptop)          │
│  Browser → Trader Portal (React/Vue Frontend)   │
└────────────┬────────────────────────────────────┘
             │ HTTPS
             ↓
┌─────────────────────────────────────────────────┐
│     SaaS Backend (Flask on Cloud Server)        │
│  ├─ User Management (Register/Login)            │
│  ├─ Bot Instance Manager                        │
│  ├─ API Endpoints                               │
│  └─ Admin Dashboard                             │
└────────────┬────────────────────────────────────┘
             │
             ├─→ PostgreSQL Database (User Data)
             ├─→ MetaTrader 5 (Each User's Account)
             └─→ Bot Instances (Per User)
```

---

## Key Concepts

### 1. User Isolation
- Each user has separate database record
- Each user connects their own MT5 account
- Trades are filtered by `user_id`
- Bots run separately per user

### 2. Authentication Flow
```
Register → Create User → Hash Password → Issue JWT Token
                                         ↓
                                    Login with Token
                                         ↓
                                    Access Protected Routes
```

### 3. Bot Instance Management
```
User Clicks "Start Bot"
    ↓
Check if bot running
    ↓
Spawn new bot process (with user-specific config)
    ↓
Store PID in database
    ↓
Monitor via BotInstance table
```

---

## API Endpoints

### Authentication
```
POST   /api/auth/register          → Register new user
POST   /api/auth/login             → Login (returns JWT)
```

### User Profile
```
GET    /api/user/profile           → Get user info
POST   /api/user/mt5-connect       → Save MT5 credentials
POST   /api/user/symbols           → Set trading symbols
```

### Bot Control
```
POST   /api/bot/start              → Start bot for user
POST   /api/bot/stop               → Stop bot for user
GET    /api/bot/status             → Get bot status
```

### Trading Data
```
GET    /api/trades                 → Get user's trades
GET    /api/trades/stats           → Get win rate, P&L, etc
```

### Admin Only
```
GET    /api/admin/users            → List all users
DELETE /api/admin/user/<id>        → Delete user
PUT    /api/admin/user/<id>/subscription → Change plan
```

---

## Deployment Options

### Option 1: Local Network (Easiest)
1. Run on your PC
2. Share IP: `http://192.168.1.X:5000`
3. Others access from WiFi

### Option 2: DigitalOcean (Recommended)
```bash
# 1. Create Droplet ($5-10/month)
# 2. SSH into server
# 3. Clone repo
# 4. Install dependencies
# 5. Use Gunicorn + Nginx
```

**Setup Nginx + Gunicorn:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 bot_platform:app
```

**Nginx config:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
    }
}
```

### Option 3: Heroku (Easiest Cloud)
```bash
# 1. Create Procfile:
echo "web: gunicorn bot_platform:app" > Procfile

# 2. Deploy:
heroku create dababybot-saas
git push heroku main

# 3. Set environment variables:
heroku config:set SECRET_KEY=your-secret
heroku config:set DATABASE_URL=<postgres-url>
```

### Option 4: AWS EC2 + RDS
- Scalable option
- More complex setup
- Best for large user base

---

## Next: Build Frontend Login Page

Create `login.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>DababyBot - Login</title>
    <style>
        body { background: linear-gradient(135deg, #0F0F1E, #1a1a2e); }
        .login-box {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background: rgba(255, 107, 53, 0.1);
            border: 2px solid #FF6B35;
            border-radius: 15px;
            color: white;
        }
        input { 
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            background: rgba(0,0,0,0.2);
            border: 1px solid #FF6B35;
            color: white;
            border-radius: 5px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #FF6B35;
            color: white;
            border: none;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover { background: #E85A2C; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>DababyBot Platform</h2>
        <div id="login-form">
            <h3>Login</h3>
            <input type="text" id="username" placeholder="Username">
            <input type="password" id="password" placeholder="Password">
            <button onclick="login()">Login</button>
            <p style="text-align: center; margin-top: 15px;">
                New user? <a href="#" onclick="switchToRegister()" style="color: #FF6B35;">Register here</a>
            </p>
        </div>
        
        <div id="register-form" style="display: none;">
            <h3>Create Account</h3>
            <input type="text" id="reg-username" placeholder="Username">
            <input type="email" id="reg-email" placeholder="Email">
            <input type="password" id="reg-password" placeholder="Password">
            <button onclick="register()">Register</button>
            <p style="text-align: center; margin-top: 15px;">
                Have account? <a href="#" onclick="switchToLogin()" style="color: #FF6B35;">Login here</a>
            </p>
        </div>
    </div>
    
    <script>
        const API = 'http://localhost:5000/api';
        
        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const res = await fetch(API + '/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            const data = await res.json();
            if (res.ok) {
                localStorage.setItem('auth_token', data.access_token);
                window.location.href = '/dashboard';
            } else {
                alert('Login failed: ' + data.error);
            }
        }
        
        async function register() {
            const username = document.getElementById('reg-username').value;
            const email = document.getElementById('reg-email').value;
            const password = document.getElementById('reg-password').value;
            
            const res = await fetch(API + '/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password })
            });
            
            const data = await res.json();
            if (res.ok) {
                localStorage.setItem('auth_token', data.access_token);
                window.location.href = '/dashboard';
            } else {
                alert('Registration failed: ' + data.error);
            }
        }
        
        function switchToRegister() {
            document.getElementById('login-form').style.display = 'none';
            document.getElementById('register-form').style.display = 'block';
        }
        
        function switchToLogin() {
            document.getElementById('login-form').style.display = 'block';
            document.getElementById('register-form').style.display = 'none';
        }
    </script>
</body>
</html>
```

---

## What's Next?

**Phase 1 (Done):**
- ✅ Backend with user management
- ✅ Database models
- ✅ JWT authentication
- ✅ Bot control endpoints

**Phase 2 (To Do):**
- [ ] Frontend login page
- [ ] Trader portal dashboard
- [ ] Admin panel
- [ ] Integrate with your existing bot

**Phase 3 (To Do):**
- [ ] Payment integration (Stripe)
- [ ] Subscription plans
- [ ] Cloud deployment

---

## Running Everything

**Terminal 1 (Backend):**
```bash
python bot_platform.py
```

**Terminal 2 (Dashboard - Optional):**
```bash
python bot_dashboard.py
```

**Access:**
- Trader Portal: `http://localhost:5000/login`
- Admin Dashboard: `http://localhost:5000/admin` (when built)
- Original Dashboard: `http://localhost:5001` (still works for direct bot control)

---

## Database Tables

```sql
-- Users
id, username, email, password_hash, mt5_server, mt5_account, 
mt5_password, subscription_plan, bot_running, selected_symbols, created_at

-- Trades
id, user_id, symbol, direction, entry_price, exit_price, pnl, status, entry_time

-- Bot Instances
id, user_id, pid, status, started_at, error_message
```

---

## Security Checklist

- [ ] Change SECRET_KEY and JWT_SECRET_KEY in production
- [ ] Encrypt MT5 credentials in database
- [ ] Use HTTPS only
- [ ] Add rate limiting
- [ ] Add CORS whitelist
- [ ] Hash passwords (already done with werkzeug)
- [ ] Use PostgreSQL instead of SQLite in production
- [ ] Add input validation on all endpoints
- [ ] Setup database backups

---

## Questions?

Need help with:
- Setting up payments?
- Deploying to cloud?
- Adding more features?
- Performance optimization?

Let me know!
