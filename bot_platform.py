"""
DababyBot SaaS Platform - Multi-User Backend
Handles user authentication, separate bot instances, and API endpoints
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import threading
import os
import json
import uuid
from datetime import datetime, timedelta
from functools import wraps
import logging

# ============ SETUP ============
app = Flask(__name__)
CORS(app)

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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ DATABASE MODELS ============

class User(db.Model):
    """User account model"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # MT5 Credentials (encrypted in production)
    mt5_server = db.Column(db.String(100))
    mt5_account = db.Column(db.String(100))
    mt5_password = db.Column(db.String(255))  # Should be encrypted in production
    
    # Subscription
    subscription_plan = db.Column(db.String(50), default='free')  # free, pro, elite
    subscription_active = db.Column(db.Boolean, default=True)
    max_symbols = db.Column(db.Integer, default=1)  # Per plan
    
    # Bot Control
    bot_running = db.Column(db.Boolean, default=False)
    bot_pid = db.Column(db.Integer, nullable=True)
    selected_symbols = db.Column(db.String(500), default='')  # JSON string
    
    # Account Info
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_admin = db.Column(db.Boolean, default=False)
    
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


# ============ AUTHENTICATION ROUTES ============

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.get_json()
    
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    # Create user
    user = User(
        username=data['username'],
        email=data['email'],
        subscription_plan='free'
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Create access token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'User created successfully',
        'access_token': access_token,
        'user': user.to_dict()
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
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
    """Save user's MT5 credentials"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.mt5_server = data.get('server', 'MetaQuotes-Demo')
    user.mt5_account = data.get('account')
    user.mt5_password = data.get('password')  # Encrypt in production!
    
    db.session.commit()
    
    return jsonify({'message': 'MT5 credentials saved'}), 200


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


# ============ BOT CONTROL ROUTES ============

@app.route('/api/bot/start', methods=['POST'])
@jwt_required()
def start_bot():
    """Start trading bot for user"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.bot_running:
        return jsonify({'error': 'Bot already running'}), 400
    
    if not user.mt5_account:
        return jsonify({'error': 'MT5 credentials not configured'}), 400
    
    # TODO: Spawn bot instance for this user
    # For now, just mark as running
    user.bot_running = True
    
    instance = BotInstance(
        user_id=user.id,
        status='RUNNING'
    )
    db.session.add(instance)
    db.session.commit()
    
    logger.info(f"Bot started for user {user.username}")
    
    return jsonify({'message': 'Bot started', 'instance': instance.to_dict()}), 200


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
    
    user.bot_running = False
    db.session.commit()
    
    logger.info(f"Bot stopped for user {user.username}")
    
    return jsonify({'message': 'Bot stopped'}), 200


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


# ============ INITIALIZATION ============

@app.before_request
def setup_db():
    """Create tables if they don't exist"""
    db.create_all()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
