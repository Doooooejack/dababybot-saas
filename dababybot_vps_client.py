#!/usr/bin/env python3
"""
DABABYBOT VPS Client
Runs on dedicated Windows VPS for each user
Automatically connects to MT5 and runs trading bot 24/7
"""

import os
import sys
import time
import json
import logging
import requests
import MetaTrader5 as mt5
from datetime import datetime
import botMayl999990000th as bot

# Configuration
WEB_SERVICE_URL = os.getenv('WEB_SERVICE_URL', 'https://your-render-app.onrender.com')
VPS_USER_ID = os.getenv('VPS_USER_ID', 'user123')
API_KEY = os.getenv('API_KEY', 'your-api-key')

# Setup logging
logging.basicConfig(
    filename='dababybot_vps.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VPSClient:
    def __init__(self):
        self.web_service_url = WEB_SERVICE_URL
        self.vps_user_id = VPS_USER_ID
        self.api_key = API_KEY
        self.mt5_credentials = None
        self.bot_running = False

    def authenticate_with_web_service(self):
        """Authenticate with web service and get user config"""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            response = requests.get(
                f'{self.web_service_url}/api/vps/auth',
                headers=headers,
                params={'vps_user_id': self.vps_user_id}
            )

            if response.status_code == 200:
                data = response.json()
                self.mt5_credentials = data.get('mt5_credentials')
                logger.info("Successfully authenticated with web service")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def connect_mt5(self):
        """Connect to MT5 using stored credentials"""
        if not self.mt5_credentials:
            logger.error("No MT5 credentials available")
            return False

        try:
            # Initialize MT5
            if not mt5.initialize():
                logger.error("MT5 initialization failed")
                return False

            # Login to MT5 account
            login = self.mt5_credentials['account']
            password = self.mt5_credentials['password']
            server = self.mt5_credentials['server']

            authorized = mt5.login(login, password, server)
            if authorized:
                logger.info(f"Connected to MT5 account {login} on {server}")
                return True
            else:
                logger.error(f"MT5 login failed for account {login}")
                return False

        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            return False

    def start_trading_bot(self):
        """Start the trading bot"""
        try:
            logger.info("Starting DABABYBOT trading...")
            self.bot_running = True

            # Initialize bot with MT5 connection
            bot.initialize_mt5()

            while self.bot_running:
                try:
                    # Run main trading loop
                    bot.run_trading_cycle()

                    # Send heartbeat to web service
                    self.send_heartbeat()

                    # Wait before next cycle
                    time.sleep(60)  # 1 minute intervals

                except Exception as e:
                    logger.error(f"Trading cycle error: {e}")
                    time.sleep(30)  # Wait before retry

        except Exception as e:
            logger.error(f"Bot startup error: {e}")
            self.bot_running = False

    def send_heartbeat(self):
        """Send status update to web service"""
        try:
            account_info = mt5.account_info()
            if account_info:
                status_data = {
                    'vps_user_id': self.vps_user_id,
                    'balance': account_info.balance,
                    'equity': account_info.equity,
                    'margin': account_info.margin,
                    'margin_free': account_info.margin_free,
                    'timestamp': datetime.now().isoformat()
                }

                headers = {'Authorization': f'Bearer {self.api_key}'}
                response = requests.post(
                    f'{self.web_service_url}/api/vps/heartbeat',
                    json=status_data,
                    headers=headers
                )

                if response.status_code == 200:
                    logger.debug("Heartbeat sent successfully")
                else:
                    logger.warning(f"Heartbeat failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Heartbeat error: {e}")

    def stop_trading_bot(self):
        """Stop the trading bot"""
        logger.info("Stopping DABABYBOT trading...")
        self.bot_running = False

        try:
            mt5.shutdown()
            logger.info("MT5 connection closed")
        except Exception as e:
            logger.error(f"MT5 shutdown error: {e}")

    def run(self):
        """Main VPS client loop"""
        logger.info("DABABYBOT VPS Client starting...")

        while True:
            try:
                # Authenticate with web service
                if not self.authenticate_with_web_service():
                    logger.error("Failed to authenticate, retrying in 60 seconds...")
                    time.sleep(60)
                    continue

                # Connect to MT5
                if not self.connect_mt5():
                    logger.error("Failed to connect to MT5, retrying in 60 seconds...")
                    time.sleep(60)
                    continue

                # Start trading bot
                self.start_trading_bot()

            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                self.stop_trading_bot()
                break
            except Exception as e:
                logger.error(f"VPS client error: {e}")
                time.sleep(30)

        logger.info("DABABYBOT VPS Client stopped")

def main():
    client = VPSClient()
    client.run()

if __name__ == "__main__":
    main()