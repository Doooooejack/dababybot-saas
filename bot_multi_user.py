"""
Multi-User Bot Wrapper
Allows existing bot to run for multiple users independently
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class BotInstance:
    """Wrapper around existing bot for multi-user support"""
    
    def __init__(self, user_id, user_config):
        self.user_id = user_id
        self.config = user_config
        
        # User-specific paths
        self.user_data_dir = Path(f"user_data/{user_id}")
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # MT5 credentials
        self.mt5_server = user_config.get('mt5_server', 'MetaQuotes-Demo')
        self.mt5_account = user_config.get('mt5_account')
        self.mt5_password = user_config.get('mt5_password')
        
        # Trading symbols
        self.trading_symbols = user_config.get('symbols', [])
        
        # User-specific state file
        self.state_file = self.user_data_dir / 'bot_state.json'
        self.trades_file = self.user_data_dir / 'trades.json'
        
        self.mt5_connected = False
        self.bot_running = False
        
        logger.info(f"[{self.user_id}] Bot instance initialized")
    
    def connect_mt5(self):
        """Connect to MT5 with user credentials"""
        try:
            import MetaTrader5 as mt5
            
            if not mt5.initialize(
                login=int(self.mt5_account),
                server=self.mt5_server,
                password=self.mt5_password
            ):
                logger.error(f"[{self.user_id}] MT5 init failed: {mt5.last_error()}")
                return False
            
            logger.info(f"[{self.user_id}] Connected to MT5")
            self.mt5_connected = True
            return True
            
        except Exception as e:
            logger.error(f"[{self.user_id}] MT5 connection error: {e}")
            return False
    
    def disconnect_mt5(self):
        """Disconnect from MT5"""
        try:
            import MetaTrader5 as mt5
            mt5.shutdown()
            self.mt5_connected = False
            logger.info(f"[{self.user_id}] MT5 disconnected")
        except Exception as e:
            logger.error(f"[{self.user_id}] MT5 disconnect error: {e}")
    
    def run_bot(self):
        """Run the trading bot for this user"""
        try:
            if not self.connect_mt5():
                self.save_error("MT5 connection failed")
                return False
            
            self.bot_running = True
            logger.info(f"[{self.user_id}] Bot starting with symbols: {self.trading_symbols}")
            self.save_state({'status': 'running', 'symbols': self.trading_symbols})
            
            # Main bot loop
            iteration = 0
            while self.bot_running:
                try:
                    iteration += 1
                    current_time = datetime.utcnow().isoformat()
                    
                    # Simulate bot activity
                    state = {
                        'user_id': self.user_id,
                        'status': 'running',
                        'timestamp': current_time,
                        'iteration': iteration,
                        'symbols': self.trading_symbols,
                        'connected': self.mt5_connected
                    }
                    
                    self.save_state(state)
                    logger.debug(f"[{self.user_id}] Iteration {iteration}")
                    
                    # Sleep to avoid CPU overload
                    time.sleep(60)  # Run analysis every 60 seconds
                    
                except KeyboardInterrupt:
                    logger.info(f"[{self.user_id}] Bot interrupted")
                    break
                except Exception as e:
                    logger.error(f"[{self.user_id}] Bot error: {e}")
                    self.save_error(str(e))
                    time.sleep(5)  # Wait before retry
            
            logger.info(f"[{self.user_id}] Bot stopped")
            
        except Exception as e:
            logger.error(f"[{self.user_id}] Critical error: {e}")
            self.save_error(f"Critical: {e}")
        finally:
            self.disconnect_mt5()
    
    def stop_bot(self):
        """Stop the bot"""
        self.bot_running = False
        logger.info(f"[{self.user_id}] Stop signal sent")
    
    def save_state(self, state):
        """Save bot state for user"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logger.error(f"[{self.user_id}] State save error: {e}")
    
    def save_error(self, error_msg):
        """Log error to user's error log"""
        try:
            error_log = self.user_data_dir / 'error.log'
            with open(error_log, 'a') as f:
                f.write(f"{datetime.utcnow().isoformat()} - {error_msg}\n")
        except Exception as e:
            logger.error(f"[{self.user_id}] Error log failed: {e}")
    
    def get_stats(self):
        """Get bot stats for this user"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"[{self.user_id}] Stats error: {e}")
        
        return {'status': 'unknown', 'user_id': self.user_id}
    
    def record_trade(self, trade_data):
        """Record a trade"""
        try:
            # Initialize trades list if not exists
            trades = []
            if self.trades_file.exists():
                with open(self.trades_file, 'r') as f:
                    trades = json.load(f)
            
            # Add new trade
            trade = {
                **trade_data,
                'user_id': self.user_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            trades.append(trade)
            
            # Save
            with open(self.trades_file, 'w') as f:
                json.dump(trades, f)
            
            logger.info(f"[{self.user_id}] Trade recorded: {trade_data}")
            
        except Exception as e:
            logger.error(f"[{self.user_id}] Trade recording error: {e}")


if __name__ == '__main__':
    # Test run
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'mt5_server': 'MetaQuotes-Demo',
        'mt5_account': '12345',
        'mt5_password': 'password',
        'symbols': ['EURUSD', 'GBPUSD']
    }
    
    bot = BotInstance('test_user', config)
    bot.run_bot()
