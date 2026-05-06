"""
DababyBot Client - Connects local Windows bot to cloud relay
Allows trading from non-Windows machines while keeping bot on Windows

Usage:
    1. User configures MT5 in web dashboard
    2. Windows bot runs this client
    3. Bot connects to cloud relay with credentials
    4. Dashboard sends trades → relay → bot → MT5
    5. Bot sends results back → relay → dashboard
"""

import json
import logging
import os
import time
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

class BotRelayClient:
    """
    Client for local Windows bot to connect to cloud relay
    Establishes persistent connection to cloud platform
    """
    
    def __init__(self, cloud_url, user_id, mt5_account, mt5_server, auth_token):
        """
        Initialize bot relay client
        
        Args:
            cloud_url: Cloud relay server URL (e.g., https://render-app.onrender.com)
            user_id: User ID from JWT token
            mt5_account: MT5 account number
            mt5_server: MT5 server name
            auth_token: JWT token for authentication
        """
        self.cloud_url = cloud_url
        self.user_id = user_id
        self.mt5_account = mt5_account
        self.mt5_server = mt5_server
        self.auth_token = auth_token
        self.is_connected = False
        self.connection_retry_count = 0
        self.max_retries = 10
        self.retry_delay = 5  # seconds
        
        logger.info(f"🤖 BotRelayClient initialized for user {user_id}, account {mt5_account}")
    
    def connect_to_relay(self):
        """Establish connection to cloud relay"""
        import requests
        
        endpoint = f"{self.cloud_url}/api/relay/bot-register"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'account': self.mt5_account,
            'server': self.mt5_server,
            'bot_started_at': datetime.utcnow().isoformat(),
            'bot_version': '1.0'
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                self.is_connected = True
                self.connection_retry_count = 0
                logger.info(f"✅ RELAY CONNECTED: {result.get('message', 'Connected successfully')}")
                return True
            else:
                logger.warning(f"❌ Relay connection failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Relay connection error: {str(e)}")
            return False
    
    def register_with_relay(self):
        """Register this bot instance with cloud relay"""
        if self.is_connected:
            logger.info(f"✅ Bot already registered with relay for user {self.user_id}")
            return True
        
        return self.connect_to_relay()
    
    def check_for_trades(self):
        """Poll cloud for pending trades (non-blocking)"""
        import requests
        
        if not self.is_connected:
            return []
        
        endpoint = f"{self.cloud_url}/api/relay/pending-trades"
        headers = {
            'Authorization': f'Bearer {self.auth_token}'
        }
        
        try:
            response = requests.get(endpoint, headers=headers, timeout=5)
            if response.status_code == 200:
                trades = response.json().get('trades', [])
                if trades:
                    logger.info(f"📥 Received {len(trades)} pending trade(s) from relay")
                return trades
            else:
                return []
        except Exception as e:
            logger.warning(f"⚠️ Couldn't check for trades: {str(e)}")
            return []
    
    def send_trade_result(self, trade_id, success, result_data):
        """Send trade execution result back to relay"""
        import requests
        
        if not self.is_connected:
            logger.warning(f"⚠️ Not connected to relay, skipping trade result for {trade_id}")
            return False
        
        endpoint = f"{self.cloud_url}/api/relay/trade-result"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'trade_id': trade_id,
            'success': success,
            'result': result_data,
            'executed_at': datetime.utcnow().isoformat()
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ Trade result sent: {trade_id}")
                return True
            else:
                logger.warning(f"❌ Couldn't send trade result: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Trade result send error: {str(e)}")
            return False
    
    def heartbeat(self):
        """Send periodic heartbeat to keep relay connection alive"""
        import requests
        
        endpoint = f"{self.cloud_url}/api/relay/heartbeat"
        headers = {
            'Authorization': f'Bearer {self.auth_token}'
        }
        
        try:
            response = requests.post(endpoint, headers=headers, timeout=5)
            if response.status_code == 200:
                return True
            else:
                logger.warning(f"⚠️ Heartbeat failed: {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Heartbeat error: {str(e)}")
            return False
    
    def start_heartbeat_thread(self, interval=30):
        """Start periodic heartbeat to keep connection alive"""
        def heartbeat_loop():
            while self.is_connected:
                try:
                    self.heartbeat()
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Heartbeat thread error: {str(e)}")
                    time.sleep(5)
        
        thread = threading.Thread(target=heartbeat_loop, daemon=True, name="BotHeartbeat")
        thread.start()
        logger.info(f"❤️ Heartbeat thread started (interval: {interval}s)")
        return thread
    
    def disconnect(self):
        """Disconnect from relay"""
        import requests
        
        if not self.is_connected:
            return True
        
        endpoint = f"{self.cloud_url}/api/relay/bot-unregister"
        headers = {
            'Authorization': f'Bearer {self.auth_token}'
        }
        
        try:
            response = requests.post(endpoint, headers=headers, timeout=5)
            self.is_connected = False
            logger.info("✅ Disconnected from relay")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Disconnect error: {str(e)}")
            self.is_connected = False
            return False


def create_relay_client(cloud_url, user_id, mt5_account, mt5_server, auth_token):
    """Factory function to create and initialize a relay client"""
    client = BotRelayClient(
        cloud_url=cloud_url,
        user_id=user_id,
        mt5_account=mt5_account,
        mt5_server=mt5_server,
        auth_token=auth_token
    )
    
    # Connect to relay
    if client.connect_to_relay():
        # Start heartbeat to keep connection alive
        client.start_heartbeat_thread()
        return client
    else:
        logger.error("Failed to create relay client - couldn't connect")
        return None
