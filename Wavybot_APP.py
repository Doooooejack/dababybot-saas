@app.route('/api/auth/activate', methods=['POST'])
def activate_account():
    data = request.json
    username = data.get('username')
    code = data.get('code')
    if not username or not code:
        return jsonify({"error": "Username and activation code required"}), 400
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if user.is_active:
        return jsonify({"error": "Account already activated"}), 400
    if user.activation_code != code:
        return jsonify({"error": "Invalid activation code"}), 400
    user.is_active = True
    user.activation_code = None
    db.session.commit()
    return jsonify({"message": "Account activated successfully"}), 200
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sys
import os
import jwt
import datetime
from functools import wraps

# Ensure TRDBOT_MT5.py is importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import MetaTrader5 as mt5
from TRDBOT_MT5 import SYMBOLS, get_data, place_order, backtest_signals

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key'  # Change this!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wavybot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            user = User.query.get(data['user_id'])
        except Exception:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(user, *args, **kwargs)
    return decorated

# --- Replace @login_required with @token_required and add user param ---
@app.route("/symbols", methods=["GET"])
@token_required
def get_symbols(user):
    return jsonify({"symbols": SYMBOLS})

@app.route("/trade", methods=["POST"])
@token_required
def manual_trade(user):
    data = request.json
    symbol = data.get("symbol")
    direction = data.get("direction")
    if symbol not in SYMBOLS:
        return jsonify({"error": "Symbol not allowed"}), 400
    df = get_data(symbol)
    if df is None:
        return jsonify({"error": "No data for symbol"}), 400
    settings = TradingSettings.query.filter_by(user_id=user.id, symbol=symbol).first()
    if settings:
        place_order(
            direction, 
            symbol, 
            stop_loss_pips=settings.stop_loss,
            take_profit_pips=settings.take_profit,
            lot=settings.lot_size,
            risk_pct=settings.risk_percent
        )
    else:
        place_order(direction, symbol)
    return jsonify({"message": f"Manual {direction} trade sent for {symbol}."})

@app.route("/status", methods=["GET"])
@token_required
def status(user):
    open_positions = []
    for symbol in SYMBOLS:
        positions = mt5.positions_get(symbol=symbol)
        if positions:
            for pos in positions:
                open_positions.append({
                    "symbol": symbol,
                    "type": "buy" if pos.type == mt5.ORDER_TYPE_BUY else "sell",
                    "volume": pos.volume,
                    "price_open": pos.price_open,
                    "profit": pos.profit,
                    "ticket": pos.ticket
                })
    return jsonify({"open_positions": open_positions})

@app.route("/backtest", methods=["POST"])
@token_required
def backtest(user):
    data = request.json
    symbol = data.get("symbol")
    if symbol not in SYMBOLS:
        return jsonify({"error": "Symbol not allowed"}), 400
    df = get_data(symbol)
    if df is None:
        return jsonify({"error": "No data for symbol"}), 400
    import io
    import sys
    old_stdout = sys.stdout
    result = io.StringIO()
    sys.stdout = result
    backtest_signals(df, symbol)
    sys.stdout = old_stdout
    backtest_output = result.getvalue()
    return jsonify({"backtest_results": backtest_output})

@app.route("/settings", methods=["POST"])
@token_required
def update_trading_settings(user):
    data = request.json
    symbol = data.get("symbol")
    if symbol not in SYMBOLS:
        return jsonify({"error": "Symbol not allowed"}), 400
    settings = TradingSettings.query.filter_by(user_id=user.id, symbol=symbol).first()
    if not settings:
        settings = TradingSettings(user_id=user.id, symbol=symbol)
        db.session.add(settings)
    settings.lot_size = data.get("lot_size", settings.lot_size)
    settings.stop_loss = data.get("stop_loss", settings.stop_loss)
    settings.take_profit = data.get("take_profit", settings.take_profit)
    settings.risk_percent = data.get("risk_percent", settings.risk_percent)
    db.session.commit()
    return jsonify({"message": "Trading settings updated successfully"})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(32), unique=True, nullable=False)
    country = db.Column(db.String(64), nullable=False)
    password_hash = db.Column(db.String(128))
    mt5_login = db.Column(db.String(50), nullable=True)
    mt5_password = db.Column(db.String(128), nullable=True)
    mt5_server = db.Column(db.String(100), nullable=True)
    activation_code = db.Column(db.String(16), nullable=True)
    is_active = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Trading Settings Model
class TradingSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(10))
    lot_size = db.Column(db.Float, default=0.1)
    stop_loss = db.Column(db.Integer, default=30)
    take_profit = db.Column(db.Integer, default=90)
    risk_percent = db.Column(db.Float, default=0.01)

# Create tables
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Authentication Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    country = data.get('country')

    # Basic validation
    if not username or not email or not password or not phone or not country:
        return jsonify({"error": "All fields are required"}), 400

    # Email format validation
    import re
    email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(email_regex, email):
        return jsonify({"error": "Invalid email address"}), 400

    # Phone format validation (international)
    phone_regex = r"^\+?[1-9]\d{7,14}$"
    if not re.match(phone_regex, phone):
        return jsonify({"error": "Invalid phone number format"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400
    if User.query.filter_by(phone=phone).first():
        return jsonify({"error": "Phone number already exists"}), 400

    import random
    activation_code = str(random.randint(100000, 999999))

    new_user = User(
        username=username,
        email=email,
        phone=phone,
        country=country,
        is_active=False,
        activation_code=activation_code
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    # Send activation email
    try:
        from email.mime.text import MIMEText
        import smtplib
        EMAIL_FROM = "malikukuti@gmail.com"  # Update as needed
        EMAIL_PASSWORD = "qyyrpabxxtwygqto"  # Update as needed
        subject = "Activate your DababyBot Account"
        body = f"""
        <html>
        <body style='font-family:Segoe UI,Arial,sans-serif;'>
        <h2 style='color:#4da6ff;'>Welcome to DababyBot!</h2>
        <p>Hi <b>{username}</b>,</p>
        <p>Thank you for registering. Please use the activation code below to activate your account:</p>
        <div style='background:#f4f4f4;padding:18px 24px;border-radius:8px;font-size:1.3em;color:#222;letter-spacing:2px;width:max-content;margin:18px auto 18px auto;border-left:5px solid #4da6ff;'><b>{activation_code}</b></div>
        <p>If you did not request this, please ignore this email.</p>
        <p style='color:#aaa;font-size:0.95em;'>DababyBot Team</p>
        </body>
        </html>
        """
        msg = MIMEText(body, 'html')
        msg["Subject"] = subject
        msg["From"] = f"DababyBot <{EMAIL_FROM}>"
        msg["To"] = email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, [email], msg.as_string())
    except Exception as e:
        print("[EMAIL ERROR]", e)

    return jsonify({"message": "User registered successfully. Please check your email for your activation code."}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    
    if user and user.check_password(data.get('password')):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({"token": token})
    
    return jsonify({"error": "Invalid credentials"}), 401

# Trading Routes
@app.route("/symbols", methods=["GET"])
@login_required
def get_symbols():
    return jsonify({"symbols": SYMBOLS})

@app.route("/trade", methods=["POST"])
@login_required
def manual_trade():
    data = request.json
    symbol = data.get("symbol")
    direction = data.get("direction")

    if symbol not in SYMBOLS:
        return jsonify({"error": "Symbol not allowed"}), 400
    
    df = get_data(symbol)
    if df is None:
        return jsonify({"error": "No data for symbol"}), 400
    
    # Use user's trading settings if available
    settings = TradingSettings.query.filter_by(user_id=current_user.id, symbol=symbol).first()
    
    if settings:
        place_order(
            direction, 
            symbol, 
            stop_loss_pips=settings.stop_loss,
            take_profit_pips=settings.take_profit,
            lot=settings.lot_size,
            risk_pct=settings.risk_percent
        )
    else:
        place_order(direction, symbol)
    
    return jsonify({"message": f"Manual {direction} trade sent for {symbol}."})

@app.route("/status", methods=["GET"])
@login_required
def status():
    open_positions = []
    for symbol in SYMBOLS:
        positions = mt5.positions_get(symbol=symbol)
        if positions:
            for pos in positions:
                open_positions.append({
                    "symbol": symbol,
                    "type": "buy" if pos.type == mt5.ORDER_TYPE_BUY else "sell",
                    "volume": pos.volume,
                    "price_open": pos.price_open,
                    "profit": pos.profit,
                    "ticket": pos.ticket
                })
    return jsonify({"open_positions": open_positions})

@app.route("/backtest", methods=["POST"])
@login_required
def backtest():
    data = request.json
    symbol = data.get("symbol")
    
    if symbol not in SYMBOLS:
        return jsonify({"error": "Symbol not allowed"}), 400
    
    df = get_data(symbol)
    if df is None:
        return jsonify({"error": "No data for symbol"}), 400
    
    # Capture backtest results
    import io
    import sys
    
    old_stdout = sys.stdout
    result = io.StringIO()
    sys.stdout = result
    
    backtest_signals(df, symbol)
    
    sys.stdout = old_stdout
    backtest_output = result.getvalue()
    
    return jsonify({"backtest_results": backtest_output})

# Trading Settings Routes
@app.route("/settings", methods=["POST"])
@login_required
def update_trading_settings():
    data = request.json
    symbol = data.get("symbol")
    
    if symbol not in SYMBOLS:
        return jsonify({"error": "Symbol not allowed"}), 400
    
    settings = TradingSettings.query.filter_by(user_id=current_user.id, symbol=symbol).first()
    
    if not settings:
        settings = TradingSettings(user_id=current_user.id, symbol=symbol)
        db.session.add(settings)
    
    settings.lot_size = data.get("lot_size", settings.lot_size)
    settings.stop_loss = data.get("stop_loss", settings.stop_loss)
    settings.take_profit = data.get("take_profit", settings.take_profit)
    settings.risk_percent = data.get("risk_percent", settings.risk_percent)
    
    db.session.commit()
    
    return jsonify({"message": "Trading settings updated successfully"})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
