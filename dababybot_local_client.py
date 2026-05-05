"""
DABABYBOT Local Client - SaaS Architecture
Runs on user's Windows machine to handle MT5 connections and trading
Communicates with the cloud web service for user management and data sync
"""

import requests
import json
import time
import logging
from datetime import datetime
import MetaTrader5 as mt5
import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Try to import the main bot
try:
    from botMayl999990000th import run_live_trading_loop
    BOT_AVAILABLE = True
    print("✅ Main bot module imported successfully")
except ImportError as e:
    BOT_AVAILABLE = False
    print(f"❌ Bot module not available: {e}")

class DababyBotLocalClient:
    """Local client that connects to SaaS web service and runs MT5 trading"""

    def __init__(self, api_base_url="https://your-render-app.onrender.com", username=None, password=None):
        self.api_base_url = api_base_url.rstrip('/')
        self.username = username
        self.password = password
        self.auth_token = None
        self.mt5_connected = False
        self.bot_running = False

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('dababybot_local.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def authenticate(self):
        """Authenticate with the web service"""
        if not self.username or not self.password:
            self.logger.error("Username and password required for authentication")
            return False

        try:
            response = requests.post(
                f"{self.api_base_url}/api/auth/login",
                json={"username": self.username, "password": self.password},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.logger.info(f"✅ Authenticated successfully as {self.username}")
                return True
            else:
                self.logger.error(f"❌ Authentication failed: {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Authentication error: {e}")
            return False

    def get_mt5_credentials(self):
        """Get MT5 credentials from web service"""
        if not self.auth_token:
            self.logger.error("Not authenticated")
            return None

        try:
            response = requests.get(
                f"{self.api_base_url}/api/user/profile",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30
            )

            if response.status_code == 200:
                user_data = response.json()
                credentials = {
                    'account': user_data.get('mt5_account'),
                    'server': user_data.get('mt5_server'),
                    'password': user_data.get('mt5_password')
                }

                if all(credentials.values()):
                    self.logger.info("✅ MT5 credentials retrieved from web service")
                    return credentials
                else:
                    self.logger.error("❌ Incomplete MT5 credentials in web service")
                    return None
            else:
                self.logger.error(f"❌ Failed to get user profile: {response.text}")
                return None

        except Exception as e:
            self.logger.error(f"❌ Error getting MT5 credentials: {e}")
            return None

    def connect_mt5(self, account, server, password):
        """Connect to MT5 locally"""
        try:
            self.logger.info(f"🔗 Connecting to MT5: {account} @ {server}")

            if not mt5.initialize(login=int(account), server=server, password=password):
                error = mt5.last_error()
                self.logger.error(f"❌ MT5 connection failed: {error}")
                return False

            # Verify connection
            account_info = mt5.account_info()
            if account_info is None:
                self.logger.error("❌ Could not get MT5 account info")
                mt5.shutdown()
                return False

            self.logger.info(f"✅ MT5 connected successfully - Balance: ${account_info.balance}")
            self.mt5_connected = True
            return True

        except Exception as e:
            self.logger.error(f"❌ MT5 connection error: {e}")
            return False

    def sync_account_info(self):
        """Sync MT5 account info back to web service"""
        if not self.mt5_connected or not self.auth_token:
            return

        try:
            account_info = mt5.account_info()
            if account_info:
                data = {
                    'login': account_info.login,
                    'balance': account_info.balance,
                    'equity': account_info.equity,
                    'margin': account_info.margin,
                    'margin_free': account_info.margin_free,
                    'leverage': account_info.leverage
                }

                response = requests.post(
                    f"{self.api_base_url}/api/mt5/sync",
                    json=data,
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=30
                )

                if response.status_code == 200:
                    self.logger.info("✅ Account info synced to web service")
                else:
                    self.logger.warning(f"⚠️ Failed to sync account info: {response.text}")

        except Exception as e:
            self.logger.error(f"❌ Error syncing account info: {e}")

    def start_bot(self):
        """Start the trading bot"""
        if not self.mt5_connected:
            self.logger.error("❌ Cannot start bot - MT5 not connected")
            return False

        if not BOT_AVAILABLE:
            self.logger.error("❌ Bot module not available")
            return False

        try:
            self.logger.info("🚀 Starting DABABYBOT trading...")
            self.bot_running = True

            # Run the main trading loop
            run_live_trading_loop()

        except KeyboardInterrupt:
            self.logger.info("⏹️ Bot stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Bot error: {e}")
        finally:
            self.bot_running = False
            if self.mt5_connected:
                mt5.shutdown()
                self.mt5_connected = False

        return True

    def run(self):
        """Main client loop"""
        self.logger.info("🚀 Starting DABABYBOT Local Client...")
        self.logger.info(f"📡 Web Service: {self.api_base_url}")

        # Step 1: Authenticate with web service
        if not self.authenticate():
            self.logger.error("❌ Authentication failed - exiting")
            return

        # Step 2: Get MT5 credentials
        credentials = self.get_mt5_credentials()
        if not credentials:
            self.logger.error("❌ Could not get MT5 credentials - exiting")
            return

        # Step 3: Connect to MT5
        if not self.connect_mt5(credentials['account'], credentials['server'], credentials['password']):
            self.logger.error("❌ MT5 connection failed - exiting")
            return

        # Step 4: Sync initial account info
        self.sync_account_info()

        # Step 5: Start trading bot
        self.start_bot()

        self.logger.info("👋 DABABYBOT Local Client shutting down...")


def main():
    """Main entry point"""
    print("🤖 DABABYBOT Local Client - SaaS Architecture")
    print("=" * 50)

    # Get configuration
    api_url = input("Enter web service URL (e.g., https://your-app.onrender.com): ").strip()
    username = input("Enter your username: ").strip()
    password = input("Enter your password: ").strip()

    if not api_url or not username or not password:
        print("❌ All fields are required")
        return

    # Create and run client
    client = DababyBotLocalClient(api_url, username, password)
    client.run()


if __name__ == "__main__":
    main()