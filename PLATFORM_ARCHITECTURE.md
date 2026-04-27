# DababyBot SaaS Platform Architecture

## Overview
A multi-user trading platform where each trader connects their own MT5 account and manages trades via their phone/PC/iPad.

---

## Architecture Components

### 1. **Backend (Flask/Python)**
```
├── User Management (Login/Register/Profile)
├── Multi-Account Handler (each user → own MT5)
├── Bot Instance Manager (spawn bot per user)
├── API Layer (REST endpoints)
├── Admin Dashboard (manage all users)
└── Payment Integration (Stripe)
```

### 2. **Database**
```
Users Table:
├── ID, Username, Email, Password (hashed)
├── MT5 Server, Account, Password (encrypted)
├── Subscription Plan, Status
├── Credits/Balance
└── Created Date

Trades Table:
├── User ID
├── Symbol, Direction, Entry, Exit
├── P&L, Status
└── Timestamp

Bot Instances Table:
├── User ID
├── Bot PID, Status
├── Active Symbols
└── Last Update
```

### 3. **Frontend (React/Vue)**
```
User Portal:
├── Dashboard (trades, stats, P&L)
├── Bot Control (start/stop/pause)
├── Settings (symbols, strategy, API keys)
├── Performance Charts
└── Account Profile

Admin Panel:
├── User Management
├── Monitoring All Bots
├── Payment History
└── Support Tickets
```

### 4. **Deployment**
```
Option A: AWS
├── EC2 (Backend + Bot instances)
├── RDS (PostgreSQL)
├── S3 (Backups)
└── CloudFront (CDN)

Option B: Heroku (Simpler, Easier)
├── Dynos (Backend)
├── Postgres Add-on
└── GitHub Deploy

Option C: DigitalOcean (Best Value)
├── Droplet
├── Managed Database
└── App Platform
```

---

## Development Phases

### Phase 1: Multi-User Backend (Week 1-2)
- [ ] Database setup (PostgreSQL)
- [ ] User authentication (JWT)
- [ ] API endpoints for user management
- [ ] Separate bot instances per user
- [ ] API token system

### Phase 2: User Dashboard (Week 2-3)
- [ ] Simple React frontend
- [ ] User login/register
- [ ] Personal dashboard (trades, stats)
- [ ] Individual bot control

### Phase 3: Admin Panel (Week 3-4)
- [ ] Admin login
- [ ] User management
- [ ] Payment tracking
- [ ] Bot monitoring

### Phase 4: Payment Integration (Week 4-5)
- [ ] Stripe integration
- [ ] Subscription plans
- [ ] License key system
- [ ] Billing dashboard

### Phase 5: Deployment (Week 5-6)
- [ ] Docker containerization
- [ ] Cloud deployment
- [ ] SSL/Security
- [ ] Monitoring/Alerts

---

## Key Features

### User Isolation
Each trader:
- Connects own MT5 credentials (encrypted storage)
- Gets own bot instance
- Views only their trades
- Can start/stop own bot

### Subscription Plans
```
Free Tier:
├── 1 Symbol
├── Limited to 3 trades/day
└── No support

Pro Tier ($50/month):
├── 5 Symbols
├── Unlimited trades
└── Email support

Elite Tier ($150/month):
├── All Symbols
├── Priority support
└── Custom settings
```

### Security
- Passwords hashed (bcrypt)
- MT5 credentials encrypted (AES-256)
- JWT auth tokens
- Rate limiting
- API keys for external access

---

## Tech Stack Recommendation

**Backend:**
- Python 3.10+
- Flask or FastAPI
- SQLAlchemy (ORM)
- PostgreSQL
- JWT (PyJWT)
- Stripe Python SDK

**Frontend:**
- React or Vue.js
- Tailwind CSS
- Recharts (analytics)
- Axios (API calls)

**DevOps:**
- Docker
- GitHub Actions (CI/CD)
- DigitalOcean or AWS
- Nginx (reverse proxy)

**Monitoring:**
- Sentry (error tracking)
- New Relic or DataDog
- Grafana (dashboards)

---

## Next Steps

1. **Database Design** → Create PostgreSQL schema
2. **Authentication** → Add JWT login system
3. **Multi-instance Bot** → Modify bot to run per-user
4. **API Expansion** → Add user management endpoints
5. **Frontend** → Build React dashboard
6. **Deployment** → Docker + Cloud hosting
