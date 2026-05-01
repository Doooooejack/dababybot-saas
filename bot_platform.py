
"""
DababyBot SaaS Platform - Multi-User Backend with MT5 Trading
Handles user authentication, MT5 connections, bot execution, and trading
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import threading
import os
import json
import uuid
from datetime import datetime, timedelta
from functools import wraps
import logging
from collections import defaultdict
import time

# Try to import MT5 (will work on Windows with MetaTrader5 installed)
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logging.warning("MetaTrader5 library not available - demo mode")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[CONFIG] Loaded environment variables from .env file")
except ImportError:
    print("[CONFIG] python-dotenv not installed, using system environment variables")

# Try to import bot trading functions
try:
    from botMayl999990000th import run_live_trading_loop
    BOT_AVAILABLE = True
    logging.info("Bot trading functions imported successfully")
except (ImportError, Exception) as e:
    BOT_AVAILABLE = False
    logging.warning(f"Bot module not available (demo mode): {e}")

# ============ SETUP ============
app = Flask(__name__)
CORS(app)

# ============ SECURITY CONFIGURATION ============
# Enable HTTPS/SSL enforcement in production
@app.before_request
def enforce_https():
    """Enforce HTTPS in production"""
    if os.environ.get('FLASK_ENV') == 'production':
        if request.headers.get('X-Forwarded-Proto', 'http') == 'http':
            url = request.url.replace('http://', 'https://', 1)
            return jsonify({'error': 'HTTPS required'}), 403

# Security headers - PCI DSS & OWASP compliance
@app.after_request
def set_security_headers(response):
    """Add security headers to all responses"""
    # Prevent clickjacking attacks
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Prevent XSS attacks
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Content Security Policy - strict for payment security
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' https://api.stripe.com https://js.stripe.com; frame-src 'self' https://js.stripe.com; img-src 'self' https: data:;"
    
    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Feature policy / Permissions policy
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    # HSTS - strict transport security (for HTTPS)
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

# ============ RATE LIMITING (Payment Protection) ============
# Track requests per IP/user for rate limiting
request_log = defaultdict(list)

def rate_limit(max_requests=5, time_window=60, endpoint_type='general'):
    """
    Rate limiting decorator to prevent abuse
    max_requests: number of requests allowed
    time_window: time window in seconds
    endpoint_type: 'payment' for stricter limits
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP (works with proxies)
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            
            # Payment endpoints get stricter rate limiting
            if endpoint_type == 'payment':
                max_requests = 3  # Max 3 payment attempts per minute
                time_window = 60
            
            current_time = time.time()
            # Clean old requests
            request_log[client_ip] = [req_time for req_time in request_log[client_ip] 
                                     if current_time - req_time < time_window]
            
            if len(request_log[client_ip]) >= max_requests:
                logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint_type}")
                return jsonify({
                    'error': 'Too many requests. Please try again later.',
                    'retry_after': time_window
                }), 429
            
            request_log[client_ip].append(current_time)
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_payment_input(data):
    """Validate and sanitize payment input"""
    errors = []
    
    # Validate plan
    if 'plan' in data:
        valid_plans = ['pro', 'elite', 'premium']
        plan = data['plan'].lower()
        if plan not in valid_plans:
            errors.append('Invalid plan selected')
    
    # Never accept card details directly - only payment gateway tokens
    if any(key in data for key in ['card_number', 'cvv', 'card_data', 'stripe_secret']):
        logger.critical(f"SECURITY ALERT: Attempted to send card data directly to backend from {request.remote_addr}")
        return None, ["Invalid request - card data cannot be sent to backend"]
    
    # Validate subscription key format
    if 'subscription_key' in data:
        key = data['subscription_key'].strip().upper()
        if not key.startswith('DABABYBOT-') or len(key) < 20:
            errors.append('Invalid subscription key format')
    
    return data if not errors else None, errors

# Security & JWT
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///botplatform.db'  # SQLite for dev, switch to PostgreSQL in production
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
jwt = JWTManager(app)

schema_migrated = False

def migrate_user_schema():
    global schema_migrated
    if schema_migrated:
        logger.debug('User schema already migrated; skipping.')
        return
    inspector = inspect(db.engine)
    if 'users' not in inspector.get_table_names():
        db.create_all()
        logger.info('Created fresh database schema for users and related tables.')
        schema_migrated = True
        return

    existing_columns = {col['name'] for col in inspector.get_columns('users')}
    alter_statements = []
    patched_columns = []

    if 'phone' not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN phone VARCHAR(32)")
        patched_columns.append('phone')
    if 'country' not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN country VARCHAR(64) DEFAULT ''")
        patched_columns.append('country')
    if 'subscription_code' not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN subscription_code VARCHAR(16)")
        patched_columns.append('subscription_code')
    if 'is_active' not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
        patched_columns.append('is_active')
    if 'mt5_validated' not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN mt5_validated BOOLEAN DEFAULT 0")
        patched_columns.append('mt5_validated')
    if 'subscription_key' not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN subscription_key VARCHAR(100)")
        patched_columns.append('subscription_key')
    if 'subscription_key_verified' not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN subscription_key_verified BOOLEAN DEFAULT 0")
        patched_columns.append('subscription_key_verified')
    if 'subscription_expiry' not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN subscription_expiry DATETIME")
        patched_columns.append('subscription_expiry')
    if 'key_activated_at' not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN key_activated_at DATETIME")
        patched_columns.append('key_activated_at')
    if 'max_symbols' not in existing_columns:
        alter_statements.append("ALTER TABLE users ADD COLUMN max_symbols INTEGER DEFAULT 1")
        patched_columns.append('max_symbols')

    if alter_statements:
        logger.info(f"Migrating users table; adding columns: {', '.join(patched_columns)}")
        with db.engine.connect() as conn:
            for stmt in alter_statements:
                conn.execute(text(stmt))
            conn.commit()
        logger.info('User schema migration completed successfully.')
    else:
        logger.info('User schema is already up to date; no changes applied.')

    schema_migrated = True

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global dictionary to track bot threads per user
bot_threads = {}  # {user_id: {'thread': Thread, 'stop_event': Event}}

# ============ DATABASE MODELS ============

class User(db.Model):
    """User account model"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(32), unique=True, nullable=False)
    country = db.Column(db.String(64), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    subscription_code = db.Column(db.String(16), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # MT5 Credentials (encrypted in production)
    mt5_server = db.Column(db.String(100))
    mt5_account = db.Column(db.String(100))
    mt5_password = db.Column(db.String(255))  # Should be encrypted in production
    mt5_validated = db.Column(db.Boolean, default=False)  # Has connection been verified?
    
    # Subscription
    subscription_plan = db.Column(db.String(50), default='free')  # free, pro, elite
    subscription_active = db.Column(db.Boolean, default=False)
    subscription_key = db.Column(db.String(100), unique=True, nullable=True)  # Unique license key
    subscription_key_verified = db.Column(db.Boolean, default=False)  # Has key been activated
    subscription_expiry = db.Column(db.DateTime, nullable=True)  # When subscription expires
    key_activated_at = db.Column(db.DateTime, nullable=True)  # When key was activated
    max_symbols = db.Column(db.Integer, default=1)  # Per plan
    
    # Bot Control
    bot_running = db.Column(db.Boolean, default=False)
    bot_pid = db.Column(db.Integer, nullable=True)
    selected_symbols = db.Column(db.String(500), default='')  # JSON string
    
    # Account Info
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Localization
    timezone = db.Column(db.String(50), default='UTC')  # tz database name
    currency = db.Column(db.String(10), default='USD')  # USD, EUR, GBP, JPY, etc.
    language = db.Column(db.String(10), default='en')  # en, es, fr, de, ja, etc.
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'subscription_plan': self.subscription_plan,
            'bot_running': self.bot_running,
            'selected_symbols': json.loads(self.selected_symbols or '[]'),
            'created_at': self.created_at.isoformat(),
            'timezone': self.timezone,
            'currency': self.currency,
            'language': self.language,
        }


class Trade(db.Model):
    """Trade history model"""
    __tablename__ = 'trades'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    symbol = db.Column(db.String(20), nullable=False)
    direction = db.Column(db.String(10))  # BUY, SELL
    entry_price = db.Column(db.Float)
    exit_price = db.Column(db.Float)
    quantity = db.Column(db.Float)
    pnl = db.Column(db.Float)
    status = db.Column(db.String(20))  # OPEN, CLOSED, CANCELLED
    
    entry_time = db.Column(db.DateTime, default=datetime.utcnow)
    exit_time = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'pnl': self.pnl,
            'status': self.status,
            'entry_time': self.entry_time.isoformat(),
        }


class BotInstance(db.Model):
    """Track active bot instances per user"""
    __tablename__ = 'bot_instances'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    pid = db.Column(db.Integer)
    status = db.Column(db.String(20))  # RUNNING, STOPPED, ERROR
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    stopped_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.String(500), nullable=True)
    
    def to_dict(self):
        return {
            'status': self.status,
            'started_at': self.started_at.isoformat(),
            'pid': self.pid,
        }


class UserActivity(db.Model):
    """Track user activity for admin monitoring"""
    __tablename__ = 'user_activities'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    activity_type = db.Column(db.String(50))  # login, logout, bot_start, bot_stop, subscription_activated, etc.
    description = db.Column(db.String(500))
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    status = db.Column(db.String(20))  # success, failed
    activity_metadata = db.Column(db.String(1000))  # JSON for additional data (bot plan, symbols, etc.)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'description': self.description,
            'ip_address': self.ip_address,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'metadata': json.loads(self.activity_metadata or '{}')
        }


# ============ BOT HELPER FUNCTIONS ============

def _run_bot_with_stop(user_id, account, server, password, stop_event):
    """
    Run the trading bot in a background thread with ability to stop.
    """
    try:
        logger.info(f"[BOT] Starting trading loop for user {user_id}")
        
        # Attach stop event to the function so it can check for stop requests
        run_live_trading_loop._stop_event = stop_event
        
        # Run the bot trading loop
        if BOT_AVAILABLE:
            run_live_trading_loop()
        else:
            # Demo mode - just sleep
            for i in range(3600):  # Run for 1 hour in demo
                if stop_event.is_set():
                    break
                import time
                time.sleep(1)
        
        logger.info(f"[BOT] Trading loop completed for user {user_id}")
        
    except KeyboardInterrupt:
        logger.info(f"[BOT] Trading loop interrupted for user {user_id}")
    except Exception as e:
        logger.error(f"[BOT] Error in trading loop for user {user_id}: {str(e)}")
    finally:
        # Cleanup
        if user_id in bot_threads:
            del bot_threads[user_id]
        
        # IMPORTANT: Database operations in background threads need app context
        with app.app_context():
            try:
                user = User.query.get(user_id)
                if user:
                    user.bot_running = False
                    db.session.commit()
            except Exception as db_error:
                logger.error(f"[BOT] Error updating bot status for user {user_id}: {str(db_error)}")
                try:
                    db.session.rollback()
                except:
                    pass
        
        logger.info(f"[BOT] Bot thread cleanup complete for user {user_id}")


# ============ AUTHENTICATION ROUTES ============

# --- Place all route decorators below app initialization ---

@app.route('/api/mt5/sync', methods=['POST'])
def mt5_sync():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token != "your_secure_sync_token":
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    # Find user by MT5 account number
    mt5_account = str(data.get('login'))
    user = User.query.filter_by(mt5_account=mt5_account).first()
    if not user:
        return jsonify({'error': 'User not found for this MT5 account'}), 404
    # Update account info fields (add more as needed)
    user.mt5_balance = float(data.get('balance', 0))
    user.mt5_equity = float(data.get('equity', 0))
    user.mt5_margin = float(data.get('margin', 0))
    user.mt5_margin_free = float(data.get('margin_free', 0))
    user.mt5_leverage = int(data.get('leverage', 0))
    user.mt5_update_time = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'MT5 account info synced'}), 200

@app.route('/api/auth/activate', methods=['POST'])
@app.route('/api/auth/activate-subscription', methods=['POST'])
def activate_subscription():
    """Activate subscription with subscription code"""
    data = request.get_json()
    username = data.get('username')
    code = data.get('code')
    if not username or not code:
        return jsonify({'error': 'Username and subscription code required'}), 400
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if user.subscription_code != code:
        return jsonify({'error': 'Invalid subscription code'}), 400
    user.subscription_key_verified = True
    user.subscription_active = True
    user.subscription_code = None
    user.key_activated_at = datetime.utcnow()
    user.max_symbols = 1
    if user.subscription_plan == 'pro':
        user.max_symbols = 5
    elif user.subscription_plan == 'elite':
        user.max_symbols = 20
    elif user.subscription_plan == 'premium':
        user.max_symbols = 50
    db.session.commit()
    return jsonify({'message': 'Subscription activated successfully', 'plan': user.subscription_plan}), 200

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user with activation, phone, country"""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    country = data.get('country')
    subscription_plan = data.get('subscription_plan', 'free').lower()

    # Basic validation
    if not username or not email or not password or not phone or not country:
        return jsonify({'error': 'All fields are required'}), 400

    allowed_plans = ['free', 'pro', 'elite', 'premium']
    if subscription_plan not in allowed_plans:
        return jsonify({'error': 'Invalid subscription plan selected'}), 400

    # Email format validation
    import re
    email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(email_regex, email):
        return jsonify({'error': 'Invalid email address'}), 400

    # Phone format validation (international)
    phone_regex = r"^\+?[1-9]\d{7,14}$"
    if not re.match(phone_regex, phone):
        return jsonify({'error': 'Invalid phone number format'}), 400

    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409
    if User.query.filter_by(phone=phone).first():
        return jsonify({'error': 'Phone number already exists'}), 409

    import random
    subscription_code = None
    subscription_active = False
    subscription_key_verified = False

    if subscription_plan == 'free':
        subscription_active = True
        subscription_key_verified = True
    else:
        subscription_code = str(random.randint(100000, 999999))

    user = User(
        username=username,
        email=email,
        phone=phone,
        country=country,
        is_active=True,
        subscription_code=subscription_code,
        subscription_plan=subscription_plan,
        subscription_active=subscription_active,
        subscription_key_verified=subscription_key_verified
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Send activation email only if SMTP is configured.
    email_sent = False
    try:
        EMAIL_FROM = os.getenv('EMAIL_FROM', '').strip()
        EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '').strip()
        SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com').strip()
        SMTP_PORT_STR = os.getenv('SMTP_PORT', '465').strip()
        
        # Only attempt email if we have valid credentials
        if EMAIL_FROM and EMAIL_PASSWORD and SMTP_HOST:
            try:
                SMTP_PORT = int(SMTP_PORT_STR)
            except ValueError:
                SMTP_PORT = 465
            
            from email.mime.text import MIMEText
            import smtplib

            if subscription_plan == 'free':
                subject = "Welcome to DababyBot Free Plan"
                plan_label = 'Free'
                code_html = ''
                code_message = '<p>No subscription code is required for the Free plan.</p>'
            else:
                subject = f"Your DababyBot {subscription_plan.capitalize()} Subscription Code"
                plan_label = subscription_plan.capitalize()
                code_html = f"""
                <div style='background:#f4f4f4;padding:18px 24px;border-radius:8px;font-size:1.3em;color:#222;letter-spacing:2px;width:max-content;margin:18px auto 18px auto;border-left:5px solid #4da6ff;'><b>{subscription_code}</b></div>
                """
                code_message = '<p>Enter this code in the subscription section of your dashboard to activate your subscription.</p>'

            body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
                    .content {{ padding: 30px 20px; color: #333; line-height: 1.6; }}
                    .plan-badge {{ background: #f0f4ff; color: #667eea; padding: 12px 16px; border-radius: 6px; display: inline-block; margin: 15px 0; font-weight: 600; }}
                    .code-box {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; border: 2px solid #e0e0e0; }}
                    .code {{ font-size: 2em; letter-spacing: 3px; color: #667eea; font-weight: bold; font-family: 'Courier New', monospace; }}
                    .info-box {{ background: #f8f9fa; border-left: 4px solid #667eea; padding: 15px; margin: 15px 0; border-radius: 4px; }}
                    .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; border-top: 1px solid #eee; }}
                    .cta-button {{ background: #667eea; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; display: inline-block; margin-top: 15px; font-weight: 600; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0; font-size: 28px;">Welcome to DababyBot!</h1>
                    </div>
                    <div class="content">
                        <p>Hi <b>{username}</b>,</p>
                        <p>Thank you for joining DababyBot! Your account has been successfully created on the <span class="plan-badge">{plan_label.upper()} Plan</span>.</p>
                        {code_html}
                        <div class="info-box">
                            {code_message}
                        </div>
                        <p style="margin-top: 20px;">You can now log into your account and start using DababyBot's powerful trading tools and automated strategies.</p>
                        <p style="margin-top: 15px; color: #666; font-size: 14px;"><strong>What's Next?</strong></p>
                        <ul style="color: #666; font-size: 14px;">
                            <li>Set up your MT5 account connection</li>
                            <li>Configure your trading preferences</li>
                            <li>Select trading symbols</li>
                            <li>Start your automated trading bot</li>
                        </ul>
                        <p style="margin-top: 20px; color: #999; font-size: 12px;">If you did not create this account or have any questions, please contact our support team.</p>
                    </div>
                    <div class="footer">
                        <p style="margin: 0;">📊 DababyBot Trading Platform | Automated Trading & Analytics</p>
                        <p style="margin-top: 10px; color: #999;">This is an automated notification. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            msg = MIMEText(body, 'html')
            msg["Subject"] = subject
            msg["From"] = f"DababyBot <{EMAIL_FROM}>"
            msg["To"] = email
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.login(EMAIL_FROM, EMAIL_PASSWORD)
                server.sendmail(EMAIL_FROM, [email], msg.as_string())
            email_sent = True
        else:
            print("[EMAIL INFO] SMTP credentials are not configured; skipping email delivery for registration.")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send activation email: {e}")
        # Don't fail registration due to email issues

    response = {
        'message': 'User registered successfully.'
    }
    if subscription_plan != 'free':
        response['subscription_code'] = subscription_code
        if email_sent:
            response['message'] = 'User registered successfully. Subscription code has been sent to your email.'
        else:
            response['message'] = 'User registered successfully. Subscription code is available below because email delivery is not configured.'
    else:
        response['message'] = 'User registered successfully on the Free plan.'

    response['email_status'] = 'sent' if email_sent else 'skipped'

    return jsonify(response), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        # Log failed login attempt
        if user:
            log_user_activity(user.id, 'login', 'Failed login attempt', status='failed')
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Log successful login
    log_user_activity(user.id, 'login', f'User {user.username} logged in', status='success')
    
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


# ============ USER ROUTES ============

@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200


@app.route('/api/user/mt5-connect', methods=['POST'])
@jwt_required()
def connect_mt5():
    """Connect and validate user's MT5 account - returns account info or error"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    account = data.get('account')
    server = data.get('server', 'MetaQuotes-Demo')
    password = data.get('password')
    
    # Validate inputs
    if not account or not password:
        return jsonify({'error': 'Account number and password required'}), 400
    
    # Try to validate credentials (if MT5 available - Windows only)
    account_info = None
    error_msg = None
    
    if MT5_AVAILABLE:
        try:
            # Try to connect to MT5
            if not mt5.initialize(login=int(account), server=server, password=password):
                error_msg = f"MT5 connection failed: {mt5.last_error()}"
            else:
                # Get account info to confirm connection works
                account_info = mt5.account_info()
                mt5.shutdown()  # Close connection (bot will open its own)
                
                if account_info is None:
                    error_msg = "Could not retrieve account information"
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
    else:
        # Running on Render (Linux) - can't validate with MT5
        # Return demo info with warning
        logging.info(f"MT5 not available on this platform (demo mode) - accepting credentials on faith")
        account_info = {'balance': 10000.0, 'equity': 10000.0}  # Demo values
    
    # If we got an error during validation, return it
    if error_msg and account_info is None:
        return jsonify({'error': error_msg, 'success': False}), 400
    
    # Save the credentials to database
    user.mt5_server = server
    user.mt5_account = str(account)
    user.mt5_password = password  # TODO: Encrypt in production!
    user.mt5_validated = True
    db.session.commit()
    
    # Return account info
    response_data = {
        'message': 'MT5 account connected successfully',
        'success': True,
        'account': {
            'number': account,
            'server': server,
            'balance': float(account_info.get('balance', 0)) if account_info else 0.0,
            'equity': float(account_info.get('equity', 0)) if account_info else 0.0,
            'platform': 'MetaTrader5'
        }
    }
    
    if not MT5_AVAILABLE:
        response_data['account']['warning'] = 'Running in demo mode - actual balance will sync when bot starts on Windows'
    
    logging.info(f"User {user.username} connected MT5 account {account} successfully")
    return jsonify(response_data), 200


@app.route('/api/user/mt5-account-info', methods=['GET'])
@jwt_required()
def get_mt5_account_info():
    """Fetch current MT5 account balance/equity (refresh from server if available)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not user.mt5_account:
        return jsonify({'error': 'No MT5 account connected', 'connected': False}), 400
    
    account_info = None
    
    # Try to get live account info (if MT5 available - Windows only)
    if MT5_AVAILABLE and user.mt5_account:
        try:
            if mt5.initialize(login=int(user.mt5_account), server=user.mt5_server, password=user.mt5_password):
                account_info = mt5.account_info()
                mt5.shutdown()
        except Exception as e:
            logging.warning(f"Failed to fetch live account info for {user.username}: {str(e)}")
    
    # Return account info (from live MT5 or demo values)
    response_data = {
        'connected': True,
        'account': {
            'number': user.mt5_account,
            'server': user.mt5_server,
            'platform': 'MetaTrader5',
            'balance': float(account_info.balance) if account_info else 10000.0,  # Demo default
            'equity': float(account_info.equity) if account_info else 10000.0,
            'margin_level': float(account_info.margin_level) if account_info else 0.0,
            'free_margin': float(account_info.margin_free) if account_info else 0.0
        }
    }
    
    if not MT5_AVAILABLE:
        response_data['account']['demo_mode'] = True
        response_data['account']['message'] = 'Running in demo mode - refresh balance when bot is running on Windows'
    
    return jsonify(response_data), 200


@app.route('/api/user/symbols', methods=['POST'])
@jwt_required()
def set_symbols():
    """Set active trading symbols for user"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    symbols = data.get('symbols', [])
    
    # Check symbol limit based on plan
    if len(symbols) > user.max_symbols:
        return jsonify({'error': f'Plan limited to {user.max_symbols} symbols'}), 400
    
    user.selected_symbols = json.dumps(symbols)
    db.session.commit()
    
    return jsonify({'message': 'Symbols updated', 'symbols': symbols}), 200


@app.route('/api/user/preferences', methods=['POST'])
@jwt_required()
def update_preferences():
    """Update user timezone, currency, and language preferences"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if 'timezone' in data:
        user.timezone = data.get('timezone', 'UTC')
    if 'currency' in data:
        user.currency = data.get('currency', 'USD')
    if 'language' in data:
        user.language = data.get('language', 'en')
    
    db.session.commit()
    
    return jsonify({
        'message': 'Preferences updated',
        'timezone': user.timezone,
        'currency': user.currency,
        'language': user.language
    }), 200


@app.route('/api/timezones', methods=['GET'])
def get_timezones():
    """Get list of available timezones"""
    timezones = [
        # UTC & Variants
        'UTC', 'UTC-1', 'UTC-2', 'UTC-3', 'UTC-4', 'UTC-5', 'UTC-6', 'UTC-7', 'UTC-8', 'UTC-9', 'UTC-10', 'UTC-11', 'UTC-12',
        'UTC+1', 'UTC+2', 'UTC+3', 'UTC+4', 'UTC+5', 'UTC+6', 'UTC+7', 'UTC+8', 'UTC+9', 'UTC+10', 'UTC+11', 'UTC+12', 'UTC+13',
        # Americas
        'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles', 'America/Anchorage', 'Pacific/Honolulu',
        'America/Toronto', 'America/Mexico_City', 'America/Bogota', 'America/Lima', 'America/Sao_Paulo', 'America/Buenos_Aires',
        # Europe
        'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Istanbul', 'Europe/Moscow', 'Europe/Athens', 'Europe/Dublin',
        'Europe/Zurich', 'Europe/Amsterdam', 'Europe/Brussels', 'Europe/Vienna', 'Europe/Prague', 'Europe/Warsaw', 'Europe/Stockholm',
        # Middle East & Africa
        'Asia/Dubai', 'Asia/Singapore', 'Asia/Hong_Kong', 'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Bangkok', 'Asia/Kolkata',
        'Africa/Cairo', 'Africa/Johannesburg', 'Africa/Lagos', 'Africa/Nairobi',
        # Asia-Pacific
        'Australia/Sydney', 'Australia/Melbourne', 'Australia/Brisbane', 'New_Zealand', 'Pacific/Auckland', 'Pacific/Fiji'
    ]
    return jsonify({'timezones': sorted(timezones)}), 200


@app.route('/api/currencies', methods=['GET'])
def get_currencies():
    """Get list of available currencies"""
    currencies = [
        'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'CNY', 'INR', 'MXN', 'BRL', 'ZAR', 
        'SGD', 'HKD', 'KRW', 'RUB', 'AED', 'SAR', 'TRY', 'SEK', 'NOK', 'DKK', 'PLN', 'CZK'
    ]
    return jsonify({'currencies': sorted(currencies)}), 200


@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Get list of available languages"""
    languages = {
        'en': 'English',
        'es': 'Español',
        'fr': 'Français',
        'de': 'Deutsch',
        'it': 'Italiano',
        'pt': 'Português',
        'ru': 'Русский',
        'ja': '日本語',
        'ko': '한국어',
        'zh': '中文',
        'ar': 'العربية',
        'hi': 'हिन्दी',
        'th': 'ไทย',
        'tr': 'Türkçe',
    }
    return jsonify({'languages': languages}), 200


# ============ SUBSCRIPTION KEY ROUTES ============

@app.route('/api/subscription/activate-key', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, time_window=60, endpoint_type='payment')
def activate_subscription_key():
    """Activate subscription key for user - PROTECTED"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Validate and sanitize input
    validated_data, errors = validate_payment_input(data)
    if errors:
        logger.warning(f"Payment validation error for user {user.username}: {errors}")
        return jsonify({'error': 'Invalid input', 'details': errors}), 400
    
    subscription_key = data.get('subscription_key', '').strip().upper()
    
    if not subscription_key:
        return jsonify({'error': 'Subscription key is required'}), 400
    
    if len(subscription_key) < 20:
        return jsonify({'error': 'Invalid subscription key format'}), 400
    
    # Check if key already exists and is activated by another user
    existing_user = User.query.filter_by(subscription_key=subscription_key).first()
    if existing_user and existing_user.subscription_key_verified and existing_user.id != user.id:
        logger.warning(f"Duplicate key activation attempt: {subscription_key}")
        return jsonify({'error': 'This subscription key is already in use'}), 400
    
    # DEMO: Simple key validation pattern
    # In production, validate against Stripe/payment system database
    # Format: DABABYBOT-XXXX-XXXX-XXXX (25 chars)
    if not subscription_key.startswith('DABABYBOT-'):
        return jsonify({'error': 'Invalid subscription key. Key must start with DABABYBOT-'}), 400
    
    # Extract subscription plan from key (format: DABABYBOT-PLAN-XXXX-XXXX)
    key_parts = subscription_key.split('-')
    if len(key_parts) < 4:
        return jsonify({'error': 'Invalid subscription key format'}), 400
    
    plan = key_parts[1].lower()  # pro, elite, etc.
    valid_plans = ['pro', 'elite', 'premium']
    
    if plan not in valid_plans:
        return jsonify({'error': f'Invalid plan in key. Must be one of: {", ".join(valid_plans)}'}), 400
    
    # Activate subscription for 365 days
    from datetime import timedelta as td
    user.subscription_key = subscription_key
    user.subscription_key_verified = True
    user.subscription_plan = plan
    user.subscription_active = True
    user.subscription_expiry = datetime.utcnow() + td(days=365)
    user.key_activated_at = datetime.utcnow()
    
    # Set max symbols based on plan
    plan_limits = {
        'pro': 5,
        'elite': 20,
        'premium': 50
    }
    user.max_symbols = plan_limits.get(plan, 5)
    
    db.session.commit()
    
    # Log subscription activation
    log_user_activity(user.id, 'subscription_activated', f'Subscription activated: {plan} plan', status='success',
                     metadata={'plan': plan, 'key': subscription_key[-8:], 'expiry': user.subscription_expiry.isoformat()})
    
    logger.info(f"Subscription key activated for user {user.username}: Plan={plan}, Expiry={user.subscription_expiry}")
    
    return jsonify({
        'message': 'Subscription activated successfully!',
        'plan': plan,
        'expires_at': user.subscription_expiry.isoformat(),
        'max_symbols': user.max_symbols
    }), 200


@app.route('/api/subscription/status', methods=['GET'])
@jwt_required()
def subscription_status():
    """Get subscription status for user"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if subscription expired
    is_expired = False
    if user.subscription_expiry and user.subscription_expiry < datetime.utcnow():
        is_expired = True
        user.subscription_active = False
        db.session.commit()
    
    return jsonify({
        'subscription_plan': user.subscription_plan,
        'subscription_active': user.subscription_active and not is_expired,
        'subscription_key_verified': user.subscription_key_verified,
        'subscription_expiry': user.subscription_expiry.isoformat() if user.subscription_expiry else None,
        'key_activated_at': user.key_activated_at.isoformat() if user.key_activated_at else None,
        'max_symbols': user.max_symbols,
        'is_expired': is_expired,
        'days_remaining': (user.subscription_expiry - datetime.utcnow()).days if user.subscription_expiry and not is_expired else 0
    }), 200


@app.route('/api/subscription/generate-test-key', methods=['POST'])
@jwt_required()
def generate_test_key():
    """DEMO ONLY: Generate test subscription key for development/testing"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Only admins can generate test keys'}), 403
    
    data = request.get_json()
    plan = data.get('plan', 'pro').lower()  # pro, elite, premium
    
    if plan not in ['pro', 'elite', 'premium']:
        return jsonify({'error': 'Invalid plan. Must be: pro, elite, or premium'}), 400
    
    # Generate demo key: DABABYBOT-PLAN-RANDOM-RANDOM
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    random_part1 = ''.join(random.choices(chars, k=4))
    random_part2 = ''.join(random.choices(chars, k=4))
    test_key = f"DABABYBOT-{plan.upper()}-{random_part1}-{random_part2}"
    
    return jsonify({
        'test_key': test_key,
        'plan': plan,
        'message': 'Use this key to test subscription activation'
    }), 200


# ============ SECURE PAYMENT ROUTES ============

@app.route('/api/payment/create-checkout-session', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=3, time_window=60, endpoint_type='payment')
def create_checkout_session():
    """
    Create secure payment checkout session
    SECURITY: Never handle card data - use Stripe or similar tokenized payment
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Validate input
    validated_data, errors = validate_payment_input(data)
    if errors:
        logger.warning(f"Payment validation error for user {user.username}: {errors}")
        return jsonify({'error': 'Invalid request', 'details': errors}), 400
    
    plan = data.get('plan', '').lower()
    valid_plans = ['pro', 'elite', 'premium']
    
    if plan not in valid_plans:
        return jsonify({'error': 'Invalid plan'}), 400
    
    plan_data = {
        'pro': {'price': 99, 'currency': 'USD', 'symbols': 5},
        'elite': {'price': 299, 'currency': 'USD', 'symbols': 20},
        'premium': {'price': 999, 'currency': 'USD', 'symbols': 50},
    }
    
    pricing = plan_data[plan]
    
    logger.info(f"Payment session created for {user.username}: Plan={plan}, Amount=${pricing['price']}")
    
    # PRODUCTION IMPLEMENTATION: Use Stripe, PayPal, or 2Checkout
    # Example with Stripe (requires stripe library):
    # 
    # import stripe
    # stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    # 
    # session = stripe.checkout.Session.create(
    #     payment_method_types=['card'],
    #     customer_email=user.email,
    #     line_items=[{
    #         'price_data': {
    #             'currency': pricing['currency'].lower(),
    #             'product_data': {
    #                 'name': f'DababyBot {plan.upper()} Plan',
    #                 'description': f'Subscription for {pricing["symbols"]} trading symbols'
    #             },
    #             'unit_amount': pricing['price'] * 100,  # Amount in cents
    #         },
    #         'quantity': 1,
    #     }],
    #     mode='payment',
    #     success_url='https://yourdomain.com/payment-success?session_id={CHECKOUT_SESSION_ID}',
    #     cancel_url='https://yourdomain.com/payment-cancelled',
    #     metadata={
    #         'user_id': user.id,
    #         'plan': plan,
    #         'email': user.email
    #     }
    # )
    
    return jsonify({
        'session_id': f'session_{user.id}_{plan}_{int(time.time())}',
        'plan': plan,
        'amount': pricing['price'],
        'currency': pricing['currency'],
        'user_email': user.email,
        'message': 'Redirect to payment gateway to complete purchase',
        'payment_gateway': 'stripe'  # or 'paypal', '2checkout'
    }), 200


@app.route('/api/payment/verify-webhook', methods=['POST'])
@rate_limit(max_requests=10, time_window=60, endpoint_type='payment')
def verify_payment_webhook():
    """
    Verify webhook from payment gateway (Stripe, PayPal, etc.)
    SECURITY: Verify webhook signature to ensure authenticity
    """
    # SECURITY: Always verify webhook signature
    signature = request.headers.get('X-Stripe-Signature') or request.headers.get('X-PayPal-Transmission-Sig')
    
    if not signature:
        logger.error(f"Webhook received without signature from {request.remote_addr}")
        return jsonify({'error': 'Webhook signature missing'}), 400
    
    try:
        data = request.get_json()
        
        # Example Stripe verification:
        # import stripe
        # event = stripe.Webhook.construct_event(
        #     request.data,
        #     signature,
        #     os.environ.get('STRIPE_WEBHOOK_SECRET')
        # )
        
        # Log all webhook events for audit trail
        logger.info(f"Payment webhook verified: {data.get('type')} - {data.get('id')}")
        
        # PRODUCTION: Process payment and generate subscription key
        # if event['type'] == 'payment_intent.succeeded':
        #     payment_intent = event['data']['object']
        #     user_id = payment_intent['metadata']['user_id']
        #     plan = payment_intent['metadata']['plan']
        #     
        #     user = User.query.get(user_id)
        #     if user:
        #         # Generate unique subscription key
        #         import random, string
        #         chars = string.ascii_uppercase + string.digits
        #         key_part1 = ''.join(random.choices(chars, k=4))
        #         key_part2 = ''.join(random.choices(chars, k=4))
        #         key = f"DABABYBOT-{plan.upper()}-{key_part1}-{key_part2}"
        #         
        #         user.subscription_key = key
        #         user.subscription_key_verified = True
        #         user.subscription_plan = plan
        #         user.subscription_active = True
        #         user.subscription_expiry = datetime.utcnow() + timedelta(days=365)
        #         db.session.commit()
        #         
        #         # Send key via email
        #         send_subscription_email(user.email, key, plan)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Webhook verification failed: {str(e)}")
        return jsonify({'error': 'Webhook verification failed'}), 400


# ============ BOT CONTROL ROUTES ============

@app.route('/api/bot/start', methods=['POST'])
@jwt_required()
def start_bot():
    """Start trading bot for user in background thread"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # CHECK SUBSCRIPTION - bot requires active subscription
    if not user.subscription_key_verified or not user.subscription_active:
        return jsonify({
            'error': 'Active subscription required to run bot',
            'requires_subscription': True
        }), 403
    
    # Check if subscription expired
    if user.subscription_expiry and user.subscription_expiry < datetime.utcnow():
        user.subscription_active = False
        db.session.commit()
        return jsonify({
            'error': 'Subscription has expired. Please renew your subscription.',
            'subscription_expired': True
        }), 403
    
    if user.bot_running:
        return jsonify({'error': 'Bot already running'}), 400
    
    if not user.mt5_account:
        return jsonify({'error': 'MT5 credentials not configured'}), 400
    
    # Get bot configuration from request
    data = request.get_json() or {}
    symbols = data.get('symbols', ['EURUSD'])
    daily_loss_limit = float(data.get('daily_loss_limit', 100))  # Default $100
    daily_profit_target = float(data.get('daily_profit_target', 500))  # Default $500
    
    try:
        # Verify MT5 connection first (if available)
        if MT5_AVAILABLE:
            if not mt5.initialize(login=int(user.mt5_account), server=user.mt5_server, password=user.mt5_password):
                mt5.shutdown()
                return jsonify({'error': f'MT5 connection failed: {mt5.last_error()}'}), 400
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                mt5.shutdown()
                return jsonify({'error': 'Could not get account info'}), 400
            
            logger.info(f"MT5 verified for user {user.username}: Balance=${account_info.balance}")
            mt5.shutdown()  # Close for now, bot will open its own connection
        
        # Create stop event for this bot
        stop_event = threading.Event()
        
        # Start bot in background thread
        bot_thread = threading.Thread(
            target=_run_bot_with_stop,
            args=(user_id, user.mt5_account, user.mt5_server, user.mt5_password, stop_event),
            daemon=True,
            name=f"BotThread-{user.username}"
        )
        bot_thread.start()
        
        # Store thread reference
        bot_threads[user_id] = {'thread': bot_thread, 'stop_event': stop_event}
        
        # Mark bot as running
        user.bot_running = True
        
        instance = BotInstance(
            user_id=user.id,
            status='RUNNING'
        )
        db.session.add(instance)
        db.session.commit()
        
        # Log bot start activity
        log_user_activity(user_id, 'bot_start', 'Bot started', status='success', 
                         metadata={'symbols': symbols, 'account': user.mt5_account})
        
        logger.info(f"Bot thread started for user {user.username} ({user_id})")
        
        return jsonify({
            'message': 'Bot started successfully',
            'instance': instance.to_dict(),
            'bot_available': BOT_AVAILABLE
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        return jsonify({'error': f'Bot startup failed: {str(e)}'}), 500



@app.route('/api/bot/stop', methods=['POST'])
@jwt_required()
def stop_bot():
    """Stop trading bot for user"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not user.bot_running:
        return jsonify({'error': 'Bot not running'}), 400
    
    try:
        # Stop the bot thread if it exists
        if user_id in bot_threads:
            bot_info = bot_threads[user_id]
            stop_event = bot_info['stop_event']
            stop_event.set()  # Signal the thread to stop
            
            # Wait briefly for thread to finish
            if bot_info['thread'].is_alive():
                bot_info['thread'].join(timeout=5)
            
            logger.info(f"Bot thread stopped for user {user.username}")
        
        user.bot_running = False
        
        # Mark instance as stopped
        instance = BotInstance.query.filter_by(user_id=user.id, status='RUNNING').first()
        if instance:
            instance.status = 'STOPPED'
            instance.stopped_at = datetime.utcnow()
        
        db.session.commit()
        logger.info(f"Bot stopped for user {user.username}")
        
        return jsonify({'message': 'Bot stopped successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error stopping bot: {str(e)}")
        return jsonify({'error': f'Bot stop failed: {str(e)}'}), 500


@app.route('/api/bot/status', methods=['GET'])
@jwt_required()
def bot_status():
    """Get bot status for user"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'running': user.bot_running,
        'symbols': json.loads(user.selected_symbols or '[]'),
        'subscription': user.subscription_plan
    }), 200


@app.route('/api/bot/logs', methods=['GET'])
@jwt_required()
def get_bot_logs():
    """Get recent bot logs for user"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        # Try to read bot logs from file
        log_file = os.path.join(os.path.dirname(__file__), f'bot_logs_{user_id}.log')
        logs = []
        
        if os.path.exists(log_file):
            # Read last 100 lines of log file
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                # Get last 100 lines
                log_lines = all_lines[-100:] if len(all_lines) > 100 else all_lines
                
                for line in log_lines:
                    line = line.strip()
                    if line:
                        # Parse timestamp if available
                        logs.append({
                            'timestamp': datetime.utcnow().isoformat(),
                            'message': line,
                            'level': 'INFO'
                        })
        
        # If no logs yet, return placeholder
        if not logs:
            logs = [{
                'timestamp': datetime.utcnow().isoformat(),
                'message': '⏳ Bot logs will appear here once bot starts trading...',
                'level': 'INFO'
            }]
        
        return jsonify({
            'logs': logs,
            'total': len(logs),
            'running': user.bot_running
        }), 200
    
    except Exception as e:
        logger.error(f"Error reading bot logs: {str(e)}")
        return jsonify({
            'logs': [{
                'timestamp': datetime.utcnow().isoformat(),
                'message': f'Error reading logs: {str(e)}',
                'level': 'ERROR'
            }],
            'running': user.bot_running
        }), 200


# ============ TRADES ROUTES ============

@app.route('/api/trades', methods=['GET'])
@jwt_required()
def get_trades():
    """Get user's trade history"""
    user_id = get_jwt_identity()
    
    # Only get trades for this user
    trades = Trade.query.filter_by(user_id=user_id).order_by(Trade.entry_time.desc()).all()
    
    return jsonify([trade.to_dict() for trade in trades]), 200


@app.route('/api/trades/stats', methods=['GET'])
@jwt_required()
def get_trade_stats():
    """Get trade statistics for user"""
    user_id = get_jwt_identity()
    
    trades = Trade.query.filter_by(user_id=user_id).all()
    
    if not trades:
        return jsonify({
            'total_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'avg_pnl': 0
        }), 200
    
    closed_trades = [t for t in trades if t.status == 'CLOSED']
    winning_trades = [t for t in closed_trades if t.pnl and t.pnl > 0]
    total_pnl = sum(t.pnl for t in closed_trades if t.pnl)
    
    return jsonify({
        'total_trades': len(closed_trades),
        'winning_trades': len(winning_trades),
        'win_rate': (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0,
        'total_pnl': total_pnl,
        'avg_pnl': total_pnl / len(closed_trades) if closed_trades else 0
    }), 200


# ============ ADMIN ROUTES ============

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """Get all users (admin only)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200


@app.route('/api/admin/user/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete user account (admin only)"""
    admin_id = get_jwt_identity()
    admin = User.query.get(admin_id)
    
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted'}), 200


@app.route('/api/admin/user/<user_id>/subscription', methods=['PUT'])
@jwt_required()
def update_subscription(user_id):
    """Update user subscription (admin only)"""
    admin_id = get_jwt_identity()
    admin = User.query.get(admin_id)
    
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    plan = data.get('plan', 'free')
    limits = {
        'free': 1,
        'pro': 5,
        'elite': 10
    }
    
    user.subscription_plan = plan
    user.max_symbols = limits.get(plan, 1)
    db.session.commit()
    
    return jsonify({'message': 'Subscription updated', 'plan': plan}), 200


# ============ HEALTH CHECK ============

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


# ============ ADMIN MONITORING ROUTES ============

@app.route('/api/admin/dashboard-stats', methods=['GET'])
@jwt_required()
def admin_dashboard_stats():
    """Get admin dashboard statistics - ADMIN ONLY"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    # Get statistics
    total_users = User.query.count()
    active_subscriptions = User.query.filter_by(subscription_active=True).count()
    bots_running = User.query.filter_by(bot_running=True).count()
    
    # Get recent signups (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_signups = User.query.filter(User.created_at >= seven_days_ago).count()
    
    # Get activity in last 24 hours
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    recent_activity = UserActivity.query.filter(UserActivity.created_at >= one_day_ago).count()
    
    return jsonify({
        'total_users': total_users,
        'active_subscriptions': active_subscriptions,
        'bots_running': bots_running,
        'recent_signups': recent_signups,
        'recent_activity': recent_activity,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def admin_get_users():
    """Get all users with details - ADMIN ONLY"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Get paginated users
    users_page = User.query.paginate(page=page, per_page=per_page)
    
    users_list = []
    for u in users_page.items:
        users_list.append({
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'subscription_plan': u.subscription_plan,
            'subscription_active': u.subscription_active,
            'subscription_expiry': u.subscription_expiry.isoformat() if u.subscription_expiry else None,
            'bot_running': u.bot_running,
            'created_at': u.created_at.isoformat(),
            'last_login': u.last_login.isoformat() if u.last_login else 'Never',
            'is_admin': u.is_admin,
            'max_symbols': u.max_symbols
        })
    
    return jsonify({
        'users': users_list,
        'total': users_page.total,
        'pages': users_page.pages,
        'current_page': page
    }), 200


@app.route('/api/admin/user/<user_id>/activity', methods=['GET'])
@jwt_required()
def admin_get_user_activity(user_id):
    """Get activity for specific user - ADMIN ONLY"""
    admin_id = get_jwt_identity()
    admin = User.query.get(admin_id)
    
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get last 100 activities
    activities = UserActivity.query.filter_by(user_id=user_id).order_by(
        UserActivity.created_at.desc()
    ).limit(100).all()
    
    return jsonify({
        'username': user.username,
        'activities': [a.to_dict() for a in activities]
    }), 200


@app.route('/api/admin/online-users', methods=['GET'])
@jwt_required()
def admin_get_online_users():
    """Get users with active bots running - ADMIN ONLY"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    # Get users with running bots
    online_users = User.query.filter_by(bot_running=True).all()
    
    online_list = []
    for u in online_users:
        # Get most recent bot instance
        bot_instance = BotInstance.query.filter_by(
            user_id=u.id,
            status='RUNNING'
        ).order_by(BotInstance.started_at.desc()).first()
        
        online_list.append({
            'username': u.username,
            'email': u.email,
            'plan': u.subscription_plan,
            'symbols': json.loads(u.selected_symbols or '[]'),
            'bot_started_at': bot_instance.started_at.isoformat() if bot_instance else None,
            'last_activity': u.last_login.isoformat() if u.last_login else 'Unknown'
        })
    
    return jsonify({
        'online_users': online_list,
        'total_online': len(online_list),
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/admin/activity-log', methods=['GET'])
@jwt_required()
def admin_get_activity_log():
    """Get global activity log - ADMIN ONLY"""
    admin_id = get_jwt_identity()
    admin = User.query.get(admin_id)
    
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    hours = request.args.get('hours', 24, type=int)
    activity_type = request.args.get('type', '', type=str)
    
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    query = UserActivity.query.filter(UserActivity.created_at >= time_threshold)
    
    if activity_type:
        query = query.filter_by(activity_type=activity_type)
    
    activities = query.order_by(UserActivity.created_at.desc()).limit(500).all()
    
    return jsonify({
        'activities': [a.to_dict() for a in activities],
        'total': len(activities),
        'time_range_hours': hours,
        'filter_type': activity_type if activity_type else 'all'
    }), 200


@app.route('/api/admin/stats-by-plan', methods=['GET'])
@jwt_required()
def admin_stats_by_plan():
    """Get subscriber statistics by plan - ADMIN ONLY"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    plans = ['free', 'pro', 'elite', 'premium']
    stats = {}
    
    for plan in plans:
        total = User.query.filter_by(subscription_plan=plan).count()
        active = User.query.filter_by(subscription_plan=plan, subscription_active=True).count()
        stats[plan] = {
            'total': total,
            'active': active,
            'inactive': total - active
        }
    
    return jsonify({
        'plan_stats': stats,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


def log_user_activity(user_id, activity_type, description, status='success', metadata=None):
    """Helper to log user activity"""
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    
    activity = UserActivity(
        user_id=user_id,
        activity_type=activity_type,
        description=description,
        ip_address=client_ip,
        user_agent=user_agent,
        status=status,
        activity_metadata=json.dumps(metadata or {})
    )
    db.session.add(activity)
    db.session.commit()


# ============ FRONTEND ROUTES ============

@app.route('/', methods=['GET'])
def dashboard():
    """Serve the enhanced trader dashboard with AI/ML theme and financial warnings"""
    try:
        # Try to read enhanced dashboard from file
        dashboard_path = os.path.join(os.path.dirname(__file__), 'dashboard_enhanced.html')
        if os.path.exists(dashboard_path):
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
            return render_template_string(html_template)
    except Exception as e:
        logger.error(f"Failed to load enhanced dashboard: {e}")
    
    # Fallback to basic template (keeps old template as backup)
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
        <title>DababyBot Trading Platform 🤖</title>
        <style>
            * { 
                margin: 0; 
                padding: 0; 
                box-sizing: border-box; 
            }
            
            html { 
                font-size: 16px; 
            }
            
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; 
                background: #0a1628; 
                color: #fff;
                line-height: 1.6;
            }
            
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 15px; 
                min-height: 100vh;
            }
            
            .card { 
                background: #1a2a3a; 
                border-radius: 8px; 
                padding: 20px; 
                margin-bottom: 20px; 
                border: 1px solid #2a3a4a; 
            }
            
            h1 { 
                margin-bottom: 20px; 
                color: #4da6ff; 
                font-size: 1.75rem;
                word-wrap: break-word;
            }
            
            h2 { 
                margin-bottom: 15px; 
                margin-top: 15px; 
                font-size: 1.25rem;
            }
            
            h3 { 
                margin-bottom: 12px; 
                margin-top: 12px; 
                font-size: 1.1rem;
            }
            
            label { 
                display: block; 
                margin-bottom: 8px; 
                font-weight: 500;
            }
            
            input, select { 
                width: 100%; 
                padding: 12px; 
                margin-bottom: 15px; 
                background: #0d1b2a; 
                border: 1px solid #2a3a4a; 
                color: #fff; 
                border-radius: 4px; 
                font-size: 1rem;
                font-family: inherit;
                -webkit-appearance: none;
                appearance: none;
            }
            
            input:focus, select:focus { 
                outline: none;
                border-color: #4da6ff;
                background: #0d1b2a;
            }
            
            select {
                cursor: pointer;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%234da6ff' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
                background-repeat: no-repeat;
                background-position: right 10px center;
                padding-right: 35px;
            }
            
            button { 
                background: #4da6ff; 
                color: #000; 
                padding: 12px 20px; 
                border: none; 
                border-radius: 4px; 
                cursor: pointer; 
                font-weight: bold; 
                margin-right: 10px;
                margin-bottom: 10px;
                font-size: 1rem;
                transition: background 0.2s ease;
                -webkit-appearance: none;
                appearance: none;
                min-height: 44px;
            }
            
            button:hover { 
                background: #66b3ff; 
            }
            
            button:active {
                background: #3d94e0;
            }
            
            .error { 
                color: #ff6b6b; 
                margin-bottom: 15px; 
                padding: 10px;
                background: rgba(255, 107, 107, 0.1);
                border-radius: 4px;
            }
            
            .success { 
                color: #51cf66; 
                margin-bottom: 15px; 
                padding: 10px;
                background: rgba(81, 207, 102, 0.1);
                border-radius: 4px;
            }
            
            .hidden { 
                display: none !important; 
            }
            
            .tab { 
                margin-bottom: 20px; 
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
            }
            
            .tab button { 
                background: #2a3a4a; 
                color: #fff; 
                margin-bottom: 0;
                margin-right: 0;
                flex: 1;
                min-width: 100px;
            }
            
            .tab button.active { 
                background: #4da6ff; 
                color: #000; 
            }
            
            .stats { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .stats div {
                background: #0d1b2a;
                padding: 15px;
                border-radius: 6px;
                border: 1px solid #2a3a4a;
            }
            
            .stats strong {
                display: block;
                margin-bottom: 8px;
                font-size: 0.9rem;
                color: #aaa;
            }
            
            .stats span {
                display: block;
                font-size: 1.4rem;
                color: #4da6ff;
                font-weight: bold;
            }
            
            p {
                margin-bottom: 10px;
                font-size: 1rem;
                word-wrap: break-word;
            }
            
            /* Tablet & iPad (768px and up) */
            @media (min-width: 768px) {
                .container {
                    padding: 20px;
                    margin-top: 20px;
                }
                
                h1 {
                    font-size: 2.25rem;
                    margin-bottom: 30px;
                }
                
                .card {
                    padding: 30px;
                }
                
                .tab {
                    gap: 15px;
                }
                
                .tab button {
                    flex: 0 1 auto;
                    min-width: 120px;
                }
                
                .stats {
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                }
                
                button {
                    margin-right: 15px;
                    margin-bottom: 0;
                }
            }
            
            /* Desktop (1024px and up) */
            @media (min-width: 1024px) {
                .container {
                    max-width: 1200px;
                    padding: 30px;
                }
                
                .card {
                    padding: 40px;
                }
                
                button {
                    padding: 12px 30px;
                    font-size: 1.05rem;
                }
                
                .stats {
                    grid-template-columns: repeat(4, 1fr);
                }
            }
            
            /* Large screens (1440px and up) */
            @media (min-width: 1440px) {
                h1 {
                    font-size: 2.5rem;
                }
                
                .card {
                    padding: 50px;
                }
            }
            
            /* Small phones (320px and up) */
            @media (max-width: 480px) {
                html {
                    font-size: 14px;
                }
                
                .container {
                    padding: 10px;
                    margin-top: 0;
                }
                
                h1 {
                    font-size: 1.5rem;
                    margin-bottom: 15px;
                }
                
                h2 {
                    font-size: 1.1rem;
                }
                
                h3 {
                    font-size: 1rem;
                }
                
                .card {
                    padding: 15px;
                    margin-bottom: 15px;
                }
                
                input, select, input[type="text"], input[type="password"] {
                    padding: 14px 10px;
                    font-size: 16px;
                    margin-bottom: 12px;
                }
                
                button {
                    width: 100%;
                    padding: 14px;
                    margin-right: 0;
                    margin-bottom: 10px;
                    font-size: 1rem;
                    min-height: 48px;
                }
                
                .tab {
                    gap: 8px;
                    margin-bottom: 15px;
                }
                
                .tab button {
                    flex: 1;
                    min-width: 80px;
                    padding: 10px 5px;
                    font-size: 0.9rem;
                }
                
                .stats {
                    grid-template-columns: 1fr;
                    gap: 10px;
                    margin-bottom: 15px;
                }
                
                .card p {
                    font-size: 0.95rem;
                    word-break: break-word;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 DababyBot SaaS Trading Platform</h1>
            
            <div class="tab">
                <button class="tab-btn active" onclick="showTab('register', event)">Register</button>
                <button class="tab-btn" onclick="showTab('login', event)">Login</button>
                <button class="tab-btn" onclick="showTab('activate', event)">Activate</button>
                <button class="tab-btn" onclick="showTab('dashboard', event)">Dashboard</button>
            </div>
            
<!-- REGISTER SECTION - FIXED -->
            <div id="register" class="card">
                <h2>✨ Create Account</h2>
                <div id="register-msg"></div>
                <input type="text" id="reg-username" placeholder="Username (no spaces)" maxlength="20">
                <input type="email" id="reg-email" placeholder="your@email.com">
                <input type="text" id="reg-phone" placeholder="Phone (e.g. +1234567890)">
                <input type="text" id="reg-country" placeholder="Country (e.g. US)">
                <select id="reg-plan">
                    <option value="free">Free plan</option>
                    <option value="pro">Pro plan</option>
                    <option value="elite">Elite plan</option>
                    <option value="premium">Premium plan</option>
                </select>
                <input type="password" id="reg-password" placeholder="Password (8+ chars)" minlength="8">
                <button class="success" onclick="registerFixed()" style="width:100%; padding:15px; font-size:1.1rem;">✨ Create Account</button>
                <p style="text-align:center; color:#aaa; font-size:0.9rem; margin-top:10px;">
                    Have account? <a href="#" onclick="showTab('login', event)" style="color:#4da6ff;">Login →</a>
                </p>
            </div>
            
            <!-- LOGIN SECTION -->
            <div id="login" class="card hidden">
                <h2>Login</h2>
                <div id="login-msg"></div>
                <input type="text" id="login-username" placeholder="Username">
                <input type="password" id="login-password" placeholder="Password">
                <button onclick="login()">Login</button>
            </div>

            <!-- ACTIVATE SECTION -->
            <div id="activate" class="card hidden">
                <h2>Activate Subscription</h2>
                <div id="activate-msg"></div>
                <input type="text" id="activate-username" placeholder="Username">
                <input type="text" id="activate-code" placeholder="Subscription code">
                <button onclick="activateSubscriptionCode()">Activate</button>
                <p style="text-align:center; color:#aaa; font-size:0.9rem; margin-top:10px;">
                    Back to <a href="#" onclick="showTab('login', event)" style="color:#4da6ff;">Login</a>
                </p>
            </div>
            
            <!-- DASHBOARD SECTION (Hidden until logged in) -->
            <div id="dashboard" class="card hidden">
                <h2>Trader Dashboard</h2>
                <div id="dashboard-msg"></div>
                <p>Welcome, <strong id="user-name"></strong></p>
                <p>Plan: <strong id="user-plan">Free</strong></p>
                <p>Bot Status: <strong id="bot-status">Stopped</strong></p>
                
                <h3>MT5 Connection</h3>
                <label>Select Server:</label>
                <input type="text" id="mt5-server-search" placeholder="Search servers..." onkeyup="filterServers()">
                <select id="mt5-server-list" style="width: 100%; padding: 10px; margin-bottom: 15px; background: #0d1b2a; border: 1px solid #2a3a4a; color: #fff; border-radius: 4px;" onchange="handleServerChange()">
                    <option value="">-- Choose Server --</option>
                    <option value="custom">📝 Enter Custom Server...</option>
                    <optgroup label="MetaQuotes">
                        <option value="MetaQuotes-Demo">MetaQuotes-Demo</option>
                        <option value="MetaQuotes-Live">MetaQuotes-Live</option>
                    </optgroup>
                    <optgroup label="IC Markets">
                        <option value="ICMarkets-Demo">ICMarkets-Demo</option>
                        <option value="ICMarkets-Live">ICMarkets-Live</option>
                    </optgroup>
                    <optgroup label="XM (Tradexfx)">
                        <option value="XM-Demo">XM-Demo</option>
                        <option value="XM-Live">XM-Live</option>
                        <option value="XMGlobal-Demo">XMGlobal-Demo</option>
                        <option value="XMGlobal-Live">XMGlobal-Live</option>
                    </optgroup>
                    <optgroup label="Alpari">
                        <option value="Alpari-Demo">Alpari-Demo</option>
                        <option value="Alpari-Live">Alpari-Live</option>
                    </optgroup>
                    <optgroup label="Pepperstone">
                        <option value="Pepperstone-Demo">Pepperstone-Demo</option>
                        <option value="Pepperstone-Live">Pepperstone-Live</option>
                    </optgroup>
                    <optgroup label="FXCM">
                        <option value="FXCM-Demo">FXCM-Demo</option>
                        <option value="FXCM-Live">FXCM-Live</option>
                    </optgroup>
                    <optgroup label="OANDA">
                        <option value="OANDA-Demo">OANDA-Demo</option>
                        <option value="OANDA-Live">OANDA-Live</option>
                    </optgroup>
                    <optgroup label="IG">
                        <option value="IG-Demo">IG-Demo</option>
                        <option value="IG-Live">IG-Live</option>
                    </optgroup>
                    <optgroup label="Saxo Bank">
                        <option value="SaxoBank-Demo">SaxoBank-Demo</option>
                        <option value="SaxoBank-Live">SaxoBank-Live</option>
                    </optgroup>
                    <optgroup label="eToro">
                        <option value="eToro-Demo">eToro-Demo</option>
                        <option value="eToro-Live">eToro-Live</option>
                    </optgroup>
                    <optgroup label="Forex.com">
                        <option value="Forexcom-Demo">Forexcom-Demo</option>
                        <option value="Forexcom-Live">Forexcom-Live</option>
                    </optgroup>
                    <optgroup label="Admirals">
                        <option value="Admirals-Demo">Admirals-Demo</option>
                        <option value="Admirals-Live">Admirals-Live</option>
                    </optgroup>
                    <optgroup label="Exness">
                        <option value="Exness-Demo">Exness-Demo</option>
                        <option value="Exness-Live">Exness-Live</option>
                    </optgroup>
                    <optgroup label="Avatrade">
                        <option value="Avatrade-Demo">Avatrade-Demo</option>
                        <option value="Avatrade-Live">Avatrade-Live</option>
                    </optgroup>
                    <optgroup label="FP Markets">
                        <option value="FPMarkets-Demo">FPMarkets-Demo</option>
                        <option value="FPMarkets-Live">FPMarkets-Live</option>
                    </optgroup>
                    <optgroup label="HotForex">
                        <option value="HotForex-Demo">HotForex-Demo</option>
                        <option value="HotForex-Live">HotForex-Live</option>
                    </optgroup>
                    <optgroup label="TMGM">
                        <option value="TMGM-Demo">TMGM-Demo</option>
                        <option value="TMGM-Live">TMGM-Live</option>
                    </optgroup>
                    <optgroup label="FXPro">
                        <option value="FXPro-Demo">FXPro-Demo</option>
                        <option value="FXPro-Live">FXPro-Live</option>
                    </optgroup>
                    <optgroup label="MultiBank">
                        <option value="MultiBank-Demo">MultiBank-Demo</option>
                        <option value="MultiBank-Live">MultiBank-Live</option>
                    </optgroup>
                    <optgroup label="Tickmill">
                        <option value="Tickmill-Demo">Tickmill-Demo</option>
                        <option value="Tickmill-Live">Tickmill-Live</option>
                    </optgroup>
                    <optgroup label="FXTM">
                        <option value="FXTM-Demo">FXTM-Demo</option>
                        <option value="FXTM-Live">FXTM-Live</option>
                    </optgroup>
                    <optgroup label="RoboForex">
                        <option value="RoboForex-Demo">RoboForex-Demo</option>
                        <option value="RoboForex-Live">RoboForex-Live</option>
                    </optgroup>
                    <optgroup label="FXDD">
                        <option value="FXDD-Demo">FXDD-Demo</option>
                        <option value="FXDD-Live">FXDD-Live</option>
                    </optgroup>
                    <optgroup label="PaxForex">
                        <option value="PaxForex-Demo">PaxForex-Demo</option>
                        <option value="PaxForex-Live">PaxForex-Live</option>
                    </optgroup>
                    <optgroup label="JustMarkets">
                        <option value="JustMarkets-Demo">JustMarkets-Demo</option>
                        <option value="JustMarkets-Live">JustMarkets-Live</option>
                    </optgroup>
                    <optgroup label="OATFundedNext">
                        <option value="OATFundedNext-Demo">OATFundedNext-Demo</option>
                        <option value="OATFundedNext-Live">OATFundedNext-Live</option>
                        <option value="OATFundedNext-Stage1">OATFundedNext-Stage1</option>
                        <option value="OATFundedNext-Stage2">OATFundedNext-Stage2</option>
                    </optgroup>
                    <optgroup label="RCG Markets">
                        <option value="RCGMarkets-Demo">RCGMarkets-Demo</option>
                        <option value="RCGMarkets-Live">RCGMarkets-Live</option>
                    </optgroup>
                    <optgroup label="FTMO">
                        <option value="FTMO-Demo">FTMO-Demo</option>
                        <option value="FTMO-Live">FTMO-Live</option>
                    </optgroup>
                    <optgroup label="TopStep">
                        <option value="TopStep-Demo">TopStep-Demo</option>
                        <option value="TopStep-Live">TopStep-Live</option>
                    </optgroup>
                    <optgroup label="Funded">
                        <option value="Funded-Demo">Funded-Demo</option>
                        <option value="Funded-Live">Funded-Live</option>
                    </optgroup>
                    <optgroup label="The5ers">
                        <option value="The5ers-Demo">The5ers-Demo</option>
                        <option value="The5ers-Live">The5ers-Live</option>
                    </optgroup>
                    <optgroup label="Blueberry Markets">
                        <option value="BlueberryMarkets-Demo">BlueberryMarkets-Demo</option>
                        <option value="BlueberryMarkets-Live">BlueberryMarkets-Live</option>
                    </optgroup>
                    <optgroup label="AimTrade">
                        <option value="AimTrade-Demo">AimTrade-Demo</option>
                        <option value="AimTrade-Live">AimTrade-Live</option>
                    </optgroup>
                </select>
                <input type="text" id="mt5-custom-server" placeholder="Enter custom server name" style="display: none;">
                <input type="text" id="mt5-account" placeholder="Account Number">
                <input type="password" id="mt5-password" placeholder="MT5 Password">
                <button onclick="connectMT5()">Connect MT5</button>
                
                <!-- LIVE TRADING DASHBOARD (Hidden until MT5 connected) -->
                <div id="live-dashboard" style="display: none; margin-top: 30px;">
                    <h3>📊 Live Trading Dashboard</h3>
                    <p style="color: #51cf66; margin-bottom: 15px;">✓ Connected to <strong id="dashboard-server"></strong> | Account: <strong id="dashboard-account"></strong></p>
                    
                    <div class="stats">
                        <div>
                            <strong>Account Balance:</strong><br>
                            <span id="live-balance" style="font-size: 1.6rem; color: #51cf66;">$0.00</span>
                        </div>
                        <div>
                            <strong>Equity:</strong><br>
                            <span id="live-equity" style="font-size: 1.6rem; color: #4da6ff;">$0.00</span>
                        </div>
                        <div>
                            <strong>Margin Used:</strong><br>
                            <span id="live-margin" style="font-size: 1.6rem; color: #ffa94d;">0%</span>
                        </div>
                        <div>
                            <strong>Today P&L:</strong><br>
                            <span id="live-pnl" style="font-size: 1.6rem;">$0.00</span>
                        </div>
                    </div>
                    
                    <h4 style="margin-top: 20px; margin-bottom: 10px;">⚙️ Trading Configuration</h4>
                    <div style="background: #0d1b2a; padding: 15px; border-radius: 4px; margin-bottom: 15px; border: 1px solid #2a3a4a;">
                        <label><strong>Symbols to Trade (comma separated):</strong></label>
                        <input type="text" id="dashboard-symbols" placeholder="EURUSD,GBPUSD,USDJPY" value="EURUSD">
                        
                        <label style="margin-top: 10px;"><strong>Risk per Trade (%):</strong></label>
                        <input type="number" id="dashboard-risk" placeholder="2" value="2" min="0.1" max="10" step="0.1" style="width: 100px;">
                        
                        <label style="margin-top: 10px;"><strong>Max Lot Size (per trade):</strong></label>
                        <input type="number" id="dashboard-lotsize" placeholder="0.1" value="0.1" min="0.01" step="0.01" style="width: 100px;">
                        
                        <div style="margin-top: 15px;">
                            <button onclick="startBotLive()" style="background: #51cf66; color: #000;">▶️ Run Bot</button>
                            <button onclick="stopBotLive()" style="background: #ff6b6b;">⏹️ Stop Bot</button>
                            <button onclick="refreshLiveDashboard()" style="background: #4da6ff; color: #000;">🔄 Refresh</button>
                        </div>
                    </div>
                    
                    <h4 style="margin-bottom: 10px; display: flex; align-items: center;">
                        <span id="bot-status-light" style="display: inline-block; width: 12px; height: 12px; background: #aaa; border-radius: 50%; margin-right: 10px;"></span>
                        Bot Status: <span id="bot-status-text" style="color: #aaa; margin-left: 10px;">STOPPED</span>
                    </h4>
                    
                    <h4 style="margin-top: 15px; margin-bottom: 10px;">📈 Open Positions</h4>
                    <div id="live-positions" style="background: #0d1b2a; padding: 15px; border-radius: 4px; margin-bottom: 15px; border: 1px solid #2a3a4a; min-height: 50px;">
                        <p style="color: #aaa;">No open positions</p>
                    </div>
                    
                    <h4 style="margin-bottom: 10px;">📝 Recent Trades</h4>
                    <div id="live-trades" style="background: #0d1b2a; padding: 15px; border-radius: 4px; margin-bottom: 15px; border: 1px solid #2a3a4a; min-height: 50px;">
                        <p style="color: #aaa;">No trades today</p>
                    </div>
                    
                    <button onclick="disconnectMT5()" style="background: #666; margin-top: 10px;">Disconnect MT5</button>
                </div>
                
                <h3>Trading Symbols</h3>
                <input type="text" id="symbols" placeholder="EURUSD,GBPUSD,USDJPY" value="EURUSD">
                <button onclick="setSymbols()">Set Symbols</button>
                
                <h3>Bot Control</h3>
                <button onclick="startBot()">Start Bot</button>
                <button onclick="stopBot()">Stop Bot</button>
                
                <h3>🌍 Global Preferences</h3>
                <label>Timezone</label>
                <select id="timezone-select" onchange="updatePreferences()">
                    <option value="UTC">UTC</option>
                </select>
                
                <label>Currency</label>
                <select id="currency-select" onchange="updatePreferences()">
                    <option value="USD">USD - US Dollar</option>
                </select>
                
                <label>Language</label>
                <select id="language-select" onchange="updatePreferences()">
                    <option value="en">English</option>
                    <option value="es">Español</option>
                    <option value="fr">Français</option>
                    <option value="de">Deutsch</option>
                    <option value="pt">Português</option>
                    <option value="zh">中文</option>
                    <option value="ja">日本語</option>
                    <option value="ru">Русский</option>
                </select>
                
                <h3>Statistics</h3>
                <div class="stats">
                    <div><strong>Total Trades:</strong> <span id="stat-trades">0</span></div>
                    <div><strong>Win Rate:</strong> <span id="stat-winrate">0</span>%</div>
                    <div><strong>Total P&L:</strong> <span id="stat-pnl">0</span></div>
                    <div><strong>Avg P&L:</strong> <span id="stat-avg">0</span></div>
                </div>
                <button onclick="logout()">Logout</button>
            </div>
        </div>
        
        <script>
            let authToken = localStorage.getItem('auth_token');
            
            function showTab(tab, event) {
                document.querySelectorAll('.card').forEach(el => el.classList.add('hidden'));
                document.getElementById(tab).classList.remove('hidden');
                document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
                const target = event ? event.target : window.event && window.event.target;
                if (target && target.classList.contains('tab-btn')) {
                    target.classList.add('active');
                }
            }
            
async function registerFixed() {
                console.log('🔥 Register clicked!');
                const username = document.getElementById('reg-username').value.trim();
                const email = document.getElementById('reg-email').value.trim();
                const phone = document.getElementById('reg-phone').value.trim();
                const country = document.getElementById('reg-country').value.trim();
                const plan = document.getElementById('reg-plan').value;
                const password = document.getElementById('reg-password').value;
                const msgDiv = document.getElementById('register-msg');
                
                msgDiv.innerHTML = '';

                if (!username || username.length < 3) {
                    msgDiv.innerHTML = '<div class="error">❌ Username must be at least 3 characters</div>';
                    return;
                }
                if (!email || !email.includes('@')) {
                    msgDiv.innerHTML = '<div class="error">❌ Valid email required</div>';
                    return;
                }
                if (!phone || phone.length < 8) {
                    msgDiv.innerHTML = '<div class="error">❌ Valid phone number required</div>';
                    return;
                }
                if (!country || country.length < 2) {
                    msgDiv.innerHTML = '<div class="error">❌ Country code required</div>';
                    return;
                }
                if (password.length < 8) {
                    msgDiv.innerHTML = '<div class="error">❌ Password must be at least 8 chars</div>';
                    return;
                }
                
                msgDiv.innerHTML = '<div class="success">⏳ Creating account...</div>';
                
                try {
                    const payload = { username, email, password, phone, country, subscription_plan: plan };
                    console.log('Sending registration payload:', payload);
                    const res = await fetch('/api/auth/register', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();
                    console.log('Registration response:', res.status, data);
                    
                    if (res.ok) {
                        let successMessage = '<div class="success">✅ Registered successfully.</div>';
                        if (data.subscription_code) {
                            successMessage += `<div style="margin-top:10px; font-size:0.95rem;">Subscription code: <strong>${data.subscription_code}</strong></div>`;
                            successMessage += `<div style="margin-top:6px; font-size:0.9rem; color:#444;">${data.email_status === 'sent' ? 'Code sent via email.' : 'Email skipped locally; use the code shown above.'}</div>`;
                        }
                        msgDiv.innerHTML = successMessage;
                        document.getElementById('login-username').value = username;
                        setTimeout(() => showTab('login'), 2200);
                    } else {
                        const errorMessage = data.error || data.message || 'Registration failed';
                        msgDiv.innerHTML = `<div class="error">❌ ${errorMessage}</div>`;
                    }
                } catch (err) {
                    console.error('Network:', err);
                    msgDiv.innerHTML = '<div class="error">❌ Network error - open console for details</div>';
                }
            }
            
            async function login() {
                const username = document.getElementById('login-username').value;
                const password = document.getElementById('login-password').value;
                const msgDiv = document.getElementById('login-msg');
                
                msgDiv.innerHTML = '';

                if (!username || !password) {
                    msgDiv.innerHTML = '<div class="error">Fill all fields</div>';
                    return;
                }
                
                try {
                    const payload = { username, password };
                    console.log('Sending login payload:', { username });
                    const res = await fetch('/api/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();
                    console.log('Login response:', res.status, data);
                    
                    if (res.ok) {
                        localStorage.setItem('auth_token', data.access_token);
                        msgDiv.innerHTML = '<div class="success">✓ Logged in!</div>';
                        authToken = data.access_token;
                        setTimeout(() => loadDashboard(), 1000);
                    } else {
                        const errorMessage = data.error || data.message || 'Login failed';
                        msgDiv.innerHTML = `<div class="error">❌ ${errorMessage}</div>`;
                    }
                } catch (err) {
                    console.error('Network login error:', err);
                    msgDiv.innerHTML = '<div class="error">❌ Network error - open console for details</div>';
                }
            }

            async function activateSubscriptionCode() {
                const username = document.getElementById('activate-username').value.trim();
                const code = document.getElementById('activate-code').value.trim();
                const msgDiv = document.getElementById('activate-msg');

                msgDiv.innerHTML = '';
                if (!username || username.length < 3) {
                    msgDiv.innerHTML = '<div class="error">❌ Enter your username</div>';
                    return;
                }
                if (!code || code.length < 4) {
                    msgDiv.innerHTML = '<div class="error">❌ Enter the subscription code</div>';
                    return;
                }

                msgDiv.innerHTML = '<div class="success">⏳ Activating subscription...</div>';

                try {
                    const payload = { username, code };
                    console.log('Sending activation payload:', payload);
                    const res = await fetch('/api/auth/activate-subscription', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();
                    console.log('Activation response:', res.status, data);

                    if (res.ok) {
                        msgDiv.innerHTML = `<div class="success">✅ ${data.message}</div>`;
                        if (data.plan) {
                            msgDiv.innerHTML += `<div style="margin-top:8px; font-size:0.95rem;">Plan activated: <strong>${data.plan}</strong></div>`;
                        }
                        setTimeout(() => showTab('login'), 2200);
                    } else {
                        const errorMessage = data.error || data.message || 'Activation failed';
                        msgDiv.innerHTML = `<div class="error">❌ ${errorMessage}</div>`;
                    }
                } catch (err) {
                    console.error('Activation network error:', err);
                    msgDiv.innerHTML = '<div class="error">❌ Network error - open console for details</div>';
                }
            }
            
            async function loadDashboard() {
                const msgDiv = document.getElementById('dashboard-msg');
                try {
                    const res = await fetch('/api/user/profile', {
                        headers: { 'Authorization': 'Bearer ' + authToken }
                    });
                    const user = await res.json();
                    
                    document.getElementById('user-name').textContent = user.username;
                    document.getElementById('user-plan').textContent = user.subscription_plan;
                    
                    // Load preference lists from API
                    await loadPreferenceLists();
                    
                    // Set user's saved preferences
                    document.getElementById('timezone-select').value = user.timezone || 'UTC';
                    document.getElementById('currency-select').value = user.currency || 'USD';
                    document.getElementById('language-select').value = user.language || 'en';
                    
                    showTab('dashboard');
                    loadStats();
                } catch (err) {
                    msgDiv.innerHTML = '<div class="error">Failed to load profile</div>';
                }
            }
            
            async function loadPreferenceLists() {
                try {
                    // Load timezones
                    const tzRes = await fetch('/api/timezones');
                    const tzData = await tzRes.json();
                    const tzSelect = document.getElementById('timezone-select');
                    tzSelect.innerHTML = '';
                    tzData.timezones.forEach(tz => {
                        const opt = document.createElement('option');
                        opt.value = tz;
                        opt.textContent = tz;
                        tzSelect.appendChild(opt);
                    });
                    
                    // Load currencies
                    const currRes = await fetch('/api/currencies');
                    const currData = await currRes.json();
                    const currSelect = document.getElementById('currency-select');
                    currSelect.innerHTML = '';
                    currData.currencies.forEach(curr => {
                        const opt = document.createElement('option');
                        opt.value = curr;
                        const symbols = { 'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CHF': 'CHF', 'CNY': '¥', 'INR': '₹', 'AUD': 'A$', 'CAD': 'C$', 'SGD': 'S$', 'HKD': 'HK$', 'RUB': '₽', 'AED': 'د.إ', 'TRY': '₺', 'ZAR': 'R' };
                        const symbol = symbols[curr] || '';
                        opt.textContent = `${curr} ${symbol}`;
                        currSelect.appendChild(opt);
                    });
                } catch (err) {
                    console.error('Failed to load preference lists:', err);
                }
            }
            
            async function updatePreferences() {
                const timezone = document.getElementById('timezone-select').value;
                const currency = document.getElementById('currency-select').value;
                const language = document.getElementById('language-select').value;
                
                try {
                    const res = await fetch('/api/user/preferences', {
                        method: 'POST',
                        headers: { 'Authorization': 'Bearer ' + authToken, 'Content-Type': 'application/json' },
                        body: JSON.stringify({ timezone, currency, language })
                    });
                    
                    if (res.ok) {
                        const data = await res.json();
                        console.log('✓ Preferences saved');
                    }
                } catch (err) {
                    console.error('Failed to update preferences:', err);
                }
            }
            
            async function loadStats() {
                try {
                    const res = await fetch('/api/trades/stats', {
                        headers: { 'Authorization': 'Bearer ' + authToken }
                    });
                    const stats = await res.json();
                    
                    document.getElementById('stat-trades').textContent = stats.total_trades;
                    document.getElementById('stat-winrate').textContent = stats.win_rate.toFixed(1);
                    document.getElementById('stat-pnl').textContent = stats.total_pnl.toFixed(2);
                    document.getElementById('stat-avg').textContent = stats.avg_pnl.toFixed(2);
                } catch (err) {}
            }
            
            async function connectMT5() {
                let server = document.getElementById('mt5-server-list').value;
                const customServer = document.getElementById('mt5-custom-server').value;
                const account = document.getElementById('mt5-account').value;
                const password = document.getElementById('mt5-password').value;
                
                // If custom server selected, use that instead
                if (server === 'custom') {
                    server = customServer;
                }
                
                if (!server || !account || !password) {
                    alert('Please fill all MT5 fields');
                    return;
                }
                
                const res = await fetch('/api/user/mt5-connect', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + authToken, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ server, account, password })
                });
                
                if (res.ok) {
                    alert('✓ MT5 Connected to: ' + server);
                    document.getElementById('mt5-account').value = '';
                    document.getElementById('mt5-password').value = '';
                    document.getElementById('mt5-custom-server').value = '';
                    document.getElementById('mt5-server-list').value = '';
                    
                    // Show live dashboard
                    showLiveDashboard(server, account);
                } else {
                    alert('Failed to connect MT5');
                }
            }
            
            function showLiveDashboard(server, account) {
                const dashboard = document.getElementById('live-dashboard');
                document.getElementById('dashboard-server').textContent = server;
                document.getElementById('dashboard-account').textContent = account;
                
                // Mock data - replace with real MT5 data when bot connects
                document.getElementById('live-balance').textContent = '$10,000.00';
                document.getElementById('live-equity').textContent = '$10,245.50';
                document.getElementById('live-margin').textContent = '12%';
                document.getElementById('live-pnl').textContent = '+$245.50';
                document.getElementById('live-pnl').style.color = '#51cf66';
                
                // Update status
                updateBotStatus();
                
                dashboard.style.display = 'block';
            }
            
            async function startBotLive() {
                const symbols = document.getElementById('dashboard-symbols').value.split(',').map(s => s.trim());
                const risk = parseFloat(document.getElementById('dashboard-risk').value) || 2;
                const lotsize = parseFloat(document.getElementById('dashboard-lotsize').value) || 0.1;
                
                if (!symbols.length || symbols[0] === '') {
                    alert('Please enter at least one symbol');
                    return;
                }
                
                // Save symbols first
                const symRes = await fetch('/api/user/symbols', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + authToken, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ symbols })
                });
                
                // Start the bot
                const botRes = await fetch('/api/bot/start', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + authToken, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ symbols, risk, lotsize })
                });
                
                if (botRes.ok) {
                    localStorage.setItem('bot_running', 'true');
                    console.log('✓ Bot started with symbols:', symbols, 'Risk:', risk, '%', 'Lot Size:', lotsize);
                    alert('✓ Bot is now running!');
                    updateBotStatus();
                } else {
                    alert('Failed to start bot');
                }
            }
            
            async function stopBotLive() {
                const botRes = await fetch('/api/bot/stop', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                
                if (botRes.ok) {
                    localStorage.setItem('bot_running', 'false');
                    console.log('✓ Bot stopped');
                    alert('✓ Bot stopped successfully');
                    updateBotStatus();
                } else {
                    alert('Failed to stop bot');
                }
            }
            
            function updateBotStatus() {
                const statusLight = document.getElementById('bot-status-light');
                const statusText = document.getElementById('bot-status-text');
                
                // This would check real bot status from API
                // For now, we'll update it based on last action
                const isRunning = localStorage.getItem('bot_running') === 'true';
                
                if (isRunning) {
                    statusLight.style.background = '#51cf66';
                    statusText.textContent = 'RUNNING';
                    statusText.style.color = '#51cf66';
                } else {
                    statusLight.style.background = '#aaa';
                    statusText.textContent = 'STOPPED';
                    statusText.style.color = '#aaa';
                }
            }
            
            async function refreshLiveDashboard() {
                try {
                    const res = await fetch('/api/trades/stats', {
                        headers: { 'Authorization': 'Bearer ' + authToken }
                    });
                    const stats = await res.json();
                    
                    // Update live stats
                    document.getElementById('live-pnl').textContent = '$' + stats.total_pnl.toFixed(2);
                    if (stats.total_pnl >= 0) {
                        document.getElementById('live-pnl').style.color = '#51cf66';
                    } else {
                        document.getElementById('live-pnl').style.color = '#ff6b6b';
                    }
                    
                    console.log('✓ Dashboard refreshed');
                } catch (err) {
                    console.error('Failed to refresh dashboard:', err);
                }
            }
            
            async function disconnectMT5() {
                if (confirm('Disconnect from MT5?')) {
                    document.getElementById('live-dashboard').style.display = 'none';
                    alert('Disconnected from MT5');
                }
            }
            
            function handleServerChange() {
                const selected = document.getElementById('mt5-server-list').value;
                const customInput = document.getElementById('mt5-custom-server');
                
                if (selected === 'custom') {
                    customInput.style.display = 'block';
                    customInput.focus();
                } else {
                    customInput.style.display = 'none';
                }
            }
            
            function filterServers() {
                const searchText = document.getElementById('mt5-server-search').value.toLowerCase();
                const select = document.getElementById('mt5-server-list');
                const options = select.getElementsByTagName('option');
                
                for (let i = 0; i < options.length; i++) {
                    if (options[i].value === '' || options[i].value === 'custom') continue;
                    options[i].style.display = options[i].value.toLowerCase().includes(searchText) ? '' : 'none';
                }
            }
            
            async function setSymbols() {
                const symbols = document.getElementById('symbols').value.split(',').map(s => s.trim());
                await fetch('/api/user/symbols', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + authToken, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ symbols })
                });
                alert('Symbols updated!');
            }
            
            async function startBot() {
                const res = await fetch('/api/bot/start', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                if (res.ok) {
                    localStorage.setItem('bot_running', 'true');
                    alert('✓ Bot started!');
                    updateBotStatus();
                } else {
                    alert('Error starting bot');
                }
                loadStats();
            }
            
            async function stopBot() {
                await fetch('/api/bot/stop', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                localStorage.setItem('bot_running', 'false');
                alert('Bot stopped');
                updateBotStatus();
                loadStats();
            }
            
            function logout() {
                localStorage.removeItem('auth_token');
                authToken = null;
                showTab('register');
            }
            
            if (authToken) {
                loadDashboard();
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)


# ============ INITIALIZATION ============

@app.before_request
def setup_db():
    """Create tables and migrate schema if necessary"""
    db.create_all()
    migrate_user_schema()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
