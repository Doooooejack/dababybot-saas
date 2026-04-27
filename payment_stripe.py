"""
Stripe Payment Integration for DababyBot SaaS
Handles subscriptions, billing, and payment processing
"""

from flask import Blueprint, request, jsonify
import stripe
import os
from datetime import datetime, timedelta
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_your_key_here')
stripe_webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_your_secret_here')

payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

# Subscription Plans
SUBSCRIPTION_PLANS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'max_symbols': 1,
        'monthly_trades': 50,
        'description': 'Perfect for testing'
    },
    'pro': {
        'name': 'Pro',
        'price': 4999,  # $49.99 in cents
        'max_symbols': 5,
        'monthly_trades': 1000,
        'description': 'For active traders',
        'stripe_product_id': 'prod_pro_plan',
        'stripe_price_id': 'price_pro_plan'
    },
    'elite': {
        'name': 'Elite',
        'price': 14999,  # $149.99 in cents
        'max_symbols': 10,
        'monthly_trades': 5000,
        'description': 'Unlimited trading',
        'stripe_product_id': 'prod_elite_plan',
        'stripe_price_id': 'price_elite_plan'
    }
}

# ============ DATABASE MODELS ============
# Add these to bot_platform.py User model:
"""
class User(db.Model):
    ...existing fields...
    
    # Payment fields
    stripe_customer_id = db.Column(db.String(255), unique=True)
    stripe_subscription_id = db.Column(db.String(255))
    billing_email = db.Column(db.String(120))
    subscription_status = db.Column(db.String(50), default='inactive')  # active, past_due, canceled
    subscription_end_date = db.Column(db.DateTime)
    trial_end_date = db.Column(db.DateTime)
    
class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    stripe_payment_id = db.Column(db.String(255), unique=True)
    amount = db.Column(db.Float)  # In cents
    currency = db.Column(db.String(3), default='USD')
    plan = db.Column(db.String(50))
    status = db.Column(db.String(50))  # succeeded, failed, pending
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    stripe_invoice_id = db.Column(db.String(255), unique=True)
    amount = db.Column(db.Float)
    status = db.Column(db.String(50))
    invoice_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
"""

# ============ STRIPE CUSTOMER SETUP ============

def create_stripe_customer(user_id, email, username):
    """Create Stripe customer for user"""
    from bot_platform import db, User
    
    user = User.query.get(user_id)
    
    try:
        customer = stripe.Customer.create(
            email=email,
            name=username,
            metadata={'user_id': user_id}
        )
        
        user.stripe_customer_id = customer.id
        db.session.commit()
        
        return customer.id
    except Exception as e:
        print(f"Error creating Stripe customer: {e}")
        return None


# ============ SUBSCRIPTION ROUTES ============

@payment_bp.route('/plans', methods=['GET'])
def get_plans():
    """Get all subscription plans"""
    plans = []
    for plan_id, plan_info in SUBSCRIPTION_PLANS.items():
        plans.append({
            'id': plan_id,
            'name': plan_info['name'],
            'price': plan_info['price'] / 100,  # Convert cents to dollars
            'max_symbols': plan_info['max_symbols'],
            'description': plan_info['description'],
            'features': [
                f"{plan_info['max_symbols']} trading symbols",
                f"{plan_info['monthly_trades']} trades/month",
                "Priority support" if plan_id != 'free' else "Community support"
            ]
        })
    return jsonify(plans), 200


@payment_bp.route('/checkout-session', methods=['POST'])
@jwt_required()
def create_checkout_session():
    """Create Stripe checkout session"""
    user_id = get_jwt_identity()
    from bot_platform import db, User
    
    user = User.query.get(user_id)
    data = request.get_json()
    plan_id = data.get('plan_id')
    
    if plan_id not in SUBSCRIPTION_PLANS:
        return jsonify({'error': 'Invalid plan'}), 400
    
    plan = SUBSCRIPTION_PLANS[plan_id]
    
    if not user.stripe_customer_id:
        create_stripe_customer(user_id, user.email, user.username)
    
    try:
        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=['card'],
            subscription_data={
                'items': [{
                    'price': plan['stripe_price_id'],
                    'quantity': 1
                }],
                'trial_settings': {
                    'trial_period_days': 7
                } if plan_id != 'free' else None
            },
            mode='subscription',
            success_url=os.environ.get(
                'STRIPE_SUCCESS_URL',
                'http://localhost:5000/dashboard?payment=success'
            ),
            cancel_url=os.environ.get(
                'STRIPE_CANCEL_URL',
                'http://localhost:5000/dashboard?payment=canceled'
            ),
            metadata={'plan_id': plan_id}
        )
        
        return jsonify({
            'checkout_url': session.url,
            'session_id': session.id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@payment_bp.route('/subscription', methods=['GET'])
@jwt_required()
def get_subscription():
    """Get current user subscription"""
    user_id = get_jwt_identity()
    from bot_platform import User
    
    user = User.query.get(user_id)
    
    if not user.stripe_subscription_id:
        return jsonify({
            'plan': 'free',
            'status': 'inactive',
            'trial_ends_at': None,
            'renews_at': None
        }), 200
    
    try:
        subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
        
        return jsonify({
            'plan': subscription.metadata.get('plan_id', 'pro'),
            'status': subscription.status,
            'current_period_start': subscription.current_period_start,
            'current_period_end': subscription.current_period_end,
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'trial_end': subscription.trial_end,
            'amount': subscription.plan.amount / 100 if subscription.plan else 0
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@payment_bp.route('/subscription/upgrade', methods=['POST'])
@jwt_required()
def upgrade_subscription():
    """Upgrade to higher plan"""
    user_id = get_jwt_identity()
    from bot_platform import db, User
    
    user = User.query.get(user_id)
    data = request.get_json()
    new_plan = data.get('plan_id')
    
    if not user.stripe_subscription_id:
        return jsonify({'error': 'No active subscription'}), 400
    
    plan = SUBSCRIPTION_PLANS.get(new_plan)
    if not plan:
        return jsonify({'error': 'Invalid plan'}), 400
    
    try:
        subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
        
        # Update subscription to new plan
        stripe.Subscription.modify(
            user.stripe_subscription_id,
            items=[{
                'id': subscription['items'].data[0].id,
                'price': plan['stripe_price_id']
            }],
            metadata={'plan_id': new_plan}
        )
        
        user.subscription_plan = new_plan
        user.max_symbols = plan['max_symbols']
        db.session.commit()
        
        return jsonify({'message': 'Upgraded successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@payment_bp.route('/subscription/cancel', methods=['POST'])
@jwt_required()
def cancel_subscription():
    """Cancel subscription"""
    user_id = get_jwt_identity()
    from bot_platform import db, User
    
    user = User.query.get(user_id)
    
    if not user.stripe_subscription_id:
        return jsonify({'error': 'No active subscription'}), 400
    
    try:
        stripe.Subscription.delete(user.stripe_subscription_id)
        
        user.subscription_plan = 'free'
        user.stripe_subscription_id = None
        user.subscription_status = 'canceled'
        user.subscription_end_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Subscription canceled'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============ WEBHOOK HANDLERS ============

@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    from bot_platform import db, User, Payment
    
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_webhook_secret
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle subscription events
    if event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        user = User.query.filter_by(
            stripe_subscription_id=subscription['id']
        ).first()
        
        if user:
            user.subscription_status = subscription['status']
            user.subscription_end_date = datetime.fromtimestamp(
                subscription['current_period_end']
            )
            db.session.commit()
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        user = User.query.filter_by(
            stripe_subscription_id=subscription['id']
        ).first()
        
        if user:
            user.subscription_plan = 'free'
            user.subscription_status = 'canceled'
            db.session.commit()
    
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        customer_id = invoice['customer']
        user = User.query.filter_by(
            stripe_customer_id=customer_id
        ).first()
        
        if user:
            payment = Payment(
                user_id=user.id,
                stripe_payment_id=invoice['id'],
                amount=invoice['amount_paid'],
                status='succeeded',
                plan=user.subscription_plan
            )
            db.session.add(payment)
            db.session.commit()
    
    return jsonify({'status': 'success'}), 200


# ============ BILLING ROUTES ============

@payment_bp.route('/invoices', methods=['GET'])
@jwt_required()
def get_invoices():
    """Get user's invoices"""
    user_id = get_jwt_identity()
    from bot_platform import User, Invoice
    
    user = User.query.get(user_id)
    
    if not user.stripe_customer_id:
        return jsonify([]), 200
    
    try:
        invoices = stripe.Invoice.list(customer=user.stripe_customer_id)
        
        return jsonify([{
            'id': inv.id,
            'number': inv.number,
            'date': inv.created,
            'amount': inv.amount_paid / 100,
            'status': inv.status,
            'url': inv.invoice_pdf or inv.hosted_invoice_url
        } for inv in invoices.data]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@payment_bp.route('/payment-method', methods=['GET', 'POST'])
@jwt_required()
def manage_payment_method():
    """Get or update payment method"""
    user_id = get_jwt_identity()
    from bot_platform import User
    
    user = User.query.get(user_id)
    
    if not user.stripe_customer_id:
        return jsonify({'error': 'Customer not found'}), 404
    
    if request.method == 'GET':
        try:
            customer = stripe.Customer.retrieve(user.stripe_customer_id)
            
            if customer.invoice_settings.default_payment_method:
                payment_method = stripe.PaymentMethod.retrieve(
                    customer.invoice_settings.default_payment_method
                )
                return jsonify({
                    'brand': payment_method.card.brand,
                    'last4': payment_method.card.last4,
                    'exp_month': payment_method.card.exp_month,
                    'exp_year': payment_method.card.exp_year
                }), 200
            
            return jsonify({'error': 'No payment method on file'}), 404
            
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    else:  # POST - Update payment method
        try:
            session = stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=os.environ.get(
                    'STRIPE_RETURN_URL',
                    'http://localhost:5000/dashboard'
                )
            )
            
            return jsonify({'portal_url': session.url}), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 400


# ============ DISCOUNT CODES ============

@payment_bp.route('/apply-coupon', methods=['POST'])
@jwt_required()
def apply_coupon():
    """Apply discount coupon"""
    user_id = get_jwt_identity()
    from bot_platform import User
    
    user = User.query.get(user_id)
    data = request.get_json()
    coupon_code = data.get('code')
    
    if not coupon_code:
        return jsonify({'error': 'Coupon code required'}), 400
    
    try:
        coupon = stripe.Coupon.retrieve(coupon_code)
        
        return jsonify({
            'valid': coupon.valid,
            'discount': coupon.percent_off or (coupon.amount_off / 100),
            'description': coupon.name
        }), 200
        
    except stripe.error.InvalidRequestError:
        return jsonify({'error': 'Invalid coupon code'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    print("Payment module loaded. Import this into bot_platform.py")
