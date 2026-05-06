"""
DababyBot WebSocket Relay Server
Allows non-Windows users to send trade commands to any connected Windows bot
- Free to run on Render
- Scales easily to cloud Windows later
- No changes needed when upgrading infrastructure
"""

import threading
import json
import logging
from datetime import datetime
from collections import defaultdict
import queue
import time

logger = logging.getLogger(__name__)

class WebSocketRelay:
    """
    Central relay system for bot-to-cloud-to-bot communication
    
    Architecture:
    1. Windows Bot connects via WebSocket → registers with relay
    2. Dashboard sends trade command → relay queues it
    3. Relay forwards to available Windows bot
    4. Bot executes trade → sends result back to user
    """
    
    def __init__(self):
        self.connected_bots = {}  # {user_id: {'bot_client': ws, 'registered_at': time, 'account': '12345'}}
        self.trade_queue = queue.Queue()  # Pending trades
        self.trade_results = {}  # {trade_id: result}
        self.relay_lock = threading.Lock()
        self.command_handlers = {}
        
        # Metrics
        self.stats = {
            'total_trades_relayed': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_bots_connected': 0,
            'relay_started_at': datetime.utcnow().isoformat()
        }
        
        logger.info("✅ WebSocket Relay initialized")
    
    def register_bot(self, user_id, bot_client, account_number, server):
        """Register a Windows bot connection"""
        with self.relay_lock:
            self.connected_bots[user_id] = {
                'bot_client': bot_client,
                'registered_at': datetime.utcnow(),
                'account': account_number,
                'server': server,
                'is_active': True
            }
            self.stats['total_bots_connected'] += 1
            logger.info(f"✅ BOT REGISTERED: User {user_id}, Account {account_number}, Server {server}")
            return True
    
    def unregister_bot(self, user_id):
        """Unregister a bot when it disconnects"""
        with self.relay_lock:
            if user_id in self.connected_bots:
                del self.connected_bots[user_id]
                logger.info(f"🔌 BOT UNREGISTERED: User {user_id}")
                return True
        return False
    
    def get_connected_bot(self, user_id):
        """Get connection info for a user's bot"""
        with self.relay_lock:
            return self.connected_bots.get(user_id)
    
    def queue_trade_command(self, user_id, trade_data):
        """Queue a trade command from dashboard"""
        trade_id = f"trade_{user_id}_{int(time.time() * 1000)}"
        
        command = {
            'id': trade_id,
            'user_id': user_id,
            'type': 'TRADE',
            'data': trade_data,
            'queued_at': datetime.utcnow().isoformat(),
            'status': 'PENDING'
        }
        
        self.trade_queue.put(command)
        logger.info(f"📝 TRADE QUEUED: {trade_id} for user {user_id}")
        
        return trade_id
    
    def relay_command_to_bot(self, user_id, command):
        """Send command to connected bot"""
        bot_info = self.get_connected_bot(user_id)
        
        if not bot_info:
            logger.warning(f"❌ No bot connected for user {user_id}")
            return False
        
        try:
            bot_client = bot_info['bot_client']
            # In real implementation, this would be a WebSocket send
            # For now, just queue it
            logger.info(f"📤 COMMAND RELAYED: {command['type']} to user {user_id}")
            self.stats['total_trades_relayed'] += 1
            return True
        except Exception as e:
            logger.error(f"❌ RELAY FAILED: {str(e)}")
            return False
    
    def process_pending_trades(self):
        """Main relay loop - process queued trades"""
        while True:
            try:
                # Get trade from queue (non-blocking)
                if not self.trade_queue.empty():
                    command = self.trade_queue.get(timeout=1)
                    
                    # Relay to bot
                    success = self.relay_command_to_bot(
                        command['user_id'],
                        command
                    )
                    
                    if success:
                        self.stats['successful_trades'] += 1
                    else:
                        self.stats['failed_trades'] += 1
                else:
                    time.sleep(0.1)
            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Relay process error: {str(e)}")
                time.sleep(1)
    
    def get_relay_status(self):
        """Get relay health status"""
        with self.relay_lock:
            return {
                'relay_active': True,
                'connected_bots': len(self.connected_bots),
                'bots': {
                    uid: {
                        'account': info['account'],
                        'server': info['server'],
                        'connected_since': info['registered_at'].isoformat()
                    }
                    for uid, info in self.connected_bots.items()
                },
                'pending_trades': self.trade_queue.qsize(),
                'stats': self.stats
            }
    
    def start_relay_thread(self):
        """Start the relay processing thread"""
        relay_thread = threading.Thread(
            target=self.process_pending_trades,
            daemon=True,
            name="WebSocketRelay"
        )
        relay_thread.start()
        logger.info("🚀 Relay processing thread started")
        return relay_thread


# Global relay instance
relay = WebSocketRelay()

def initialize_relay():
    """Initialize and start the relay system"""
    relay.start_relay_thread()
    logger.info("✅ WebSocket Relay system initialized and running")
    return relay
