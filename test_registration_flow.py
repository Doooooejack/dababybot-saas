#!/usr/bin/env python3
"""
Regression test for DababyBot SaaS registration and activation flow.
Run this to verify the subscription registration/activation works end-to-end.
"""

import os
import sys
import random
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_platform import app, db, User

def test_registration_activation_flow():
    """Test the complete registration -> activation flow"""
    print("🧪 Testing DababyBot SaaS registration/activation flow...")

    with app.app_context():
        # Ensure database is ready
        db.create_all()

        # Generate unique test user data
        test_id = random.randint(1000, 9999)
        username = f'testuser_{test_id}'
        email = f'{username}@example.com'
        phone = f'+100000{test_id}'
        password = 'TestPass123'

        # Test data for different plans
        test_cases = [
            {'plan': 'free', 'expected_max_symbols': 1, 'expected_active': True, 'expected_verified': True},
            {'plan': 'pro', 'expected_max_symbols': 1, 'expected_active': False, 'expected_verified': False},  # Default during registration
            {'plan': 'elite', 'expected_max_symbols': 1, 'expected_active': False, 'expected_verified': False},
            {'plan': 'premium', 'expected_max_symbols': 1, 'expected_active': False, 'expected_verified': False},
        ]

        client = app.test_client()

        for i, test_case in enumerate(test_cases):
            plan = test_case['plan']
            print(f"\n📋 Testing {plan.upper()} plan registration...")

            # Registration payload
            reg_payload = {
                'username': f'{username}_{plan}',
                'email': f'{username}_{plan}@example.com',
                'password': password,
                'phone': f'+1{234567890 + i}{test_id % 100}',  # Truly unique phone per plan
                'country': 'US',
                'subscription_plan': plan
            }

            # Register user
            reg_response = client.post('/api/auth/register', json=reg_payload)
            print(f"   Registration: {reg_response.status_code}")

            if reg_response.status_code != 201:
                print(f"   ❌ Registration failed: {reg_response.get_data(as_text=True)}")
                return False

            reg_data = reg_response.get_json()
            subscription_code = reg_data.get('subscription_code')

            # Verify response structure
            if plan == 'free':
                if subscription_code is not None:
                    print("   ❌ Free plan should not return subscription code")
                    return False
                if not reg_data.get('message', '').startswith('User registered successfully on the Free plan'):
                    print("   ❌ Free plan message incorrect")
                    return False
            else:
                if not subscription_code or len(str(subscription_code)) != 6:
                    print("   ❌ Paid plan should return 6-digit subscription code")
                    return False
                if not reg_data.get('message', '').startswith('User registered successfully. Subscription code has been sent to your email'):
                    print("   ❌ Paid plan message incorrect")
                    return False

            # Check database state after registration
            user = User.query.filter_by(username=f'{username}_{plan}').first()
            if not user:
                print("   ❌ User not found in database")
                return False

            if user.subscription_plan != plan:
                print(f"   ❌ Plan mismatch: expected {plan}, got {user.subscription_plan}")
                return False

            if user.subscription_active != test_case['expected_active']:
                print(f"   ❌ Active status mismatch: expected {test_case['expected_active']}, got {user.subscription_active}")
                return False

            if user.subscription_key_verified != test_case['expected_verified']:
                print(f"   ❌ Verified status mismatch: expected {test_case['expected_verified']}, got {user.subscription_key_verified}")
                return False

            if user.max_symbols != test_case['expected_max_symbols']:
                print(f"   ❌ Max symbols mismatch: expected {test_case['expected_max_symbols']}, got {user.max_symbols}")
                return False

            # Test activation for paid plans
            if plan != 'free':
                print(f"   Testing activation for {plan} plan...")

                activate_payload = {
                    'username': f'{username}_{plan}',
                    'code': str(subscription_code)
                }

                activate_response = client.post('/api/auth/activate-subscription', json=activate_payload)
                print(f"   Activation: {activate_response.status_code}")

                if activate_response.status_code != 200:
                    print(f"   ❌ Activation failed: {activate_response.get_data(as_text=True)}")
                    return False

                activate_data = activate_response.get_json()
                if activate_data.get('plan') != plan:
                    print(f"   ❌ Activation plan mismatch: expected {plan}, got {activate_data.get('plan')}")
                    return False

                # Refresh user from database
                db.session.refresh(user)

                if not user.subscription_active:
                    print("   ❌ User should be active after activation")
                    return False

                if not user.subscription_key_verified:
                    print("   ❌ User should be verified after activation")
                    return False

                # Refresh user from database
                db.session.refresh(user)

                if not user.subscription_active:
                    print("   ❌ User should be active after activation")
                    return False

                if not user.subscription_key_verified:
                    print("   ❌ User should be verified after activation")
                    return False

                # Check that max_symbols was updated correctly after activation
                expected_activated_symbols = {
                    'pro': 5,
                    'elite': 20,
                    'premium': 50
                }.get(plan, 1)
                
                if user.max_symbols != expected_activated_symbols:
                    print(f"   ❌ Max symbols after activation mismatch: expected {expected_activated_symbols}, got {user.max_symbols}")
                    return False

                print(f"   ✅ {plan.upper()} plan activation successful")

            print(f"   ✅ {plan.upper()} plan registration successful")

        print("\n🎉 All tests passed! Registration/activation flow is working correctly.")
        return True

if __name__ == '__main__':
    success = test_registration_activation_flow()
    sys.exit(0 if success else 1)