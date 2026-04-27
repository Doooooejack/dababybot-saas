# Integrate Existing Bot with DababyBot SaaS Platform

## Overview
This guide shows how to modify your existing trading bot to work with the SaaS platform, supporting multiple users with separate MT5 accounts.

---

## Step 1: Create Wrapper Bot Class

Create `bot_multi_user.py`:

```python
"""
Multi-User Bot Wrapper
Allows existing bot to run for multiple users independently
"""

import os
import json
import MetaTrader5 as mt5
from pathlib import Path
from datetime import datetime
import logging
import sys

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
        
    def connect_mt5(self):
        """Connect to MT5 with user credentials"""
        try:
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
            mt5.shutdown()
            self.mt5_connected = False
            logger.info(f"[{self.user_id}] MT5 disconnected")
        except Exception as e:
            logger.error(f"[{self.user_id}] MT5 disconnect error: {e}")
    
    def run_bot(self):
        """Run the trading bot for this user"""
        try:
            if not self.connect_mt5():
                return False
            
            self.bot_running = True
            logger.info(f"[{self.user_id}] Bot starting with symbols: {self.trading_symbols}")
            
            # Import your existing bot logic
            from your_existing_bot import TradingBot  # Adjust import
            
            bot = TradingBot(
                symbols=self.trading_symbols,
                config=self.config,
                user_data_dir=str(self.user_data_dir)
            )
            
            # Run bot main loop
            while self.bot_running:
                try:
                    bot.analyze_and_trade()
                    
                    # Update state file
                    self.save_state(bot)
                    
                except Exception as e:
                    logger.error(f"[{self.user_id}] Bot error: {e}")
                    self.save_error(str(e))
                
                # Sleep to avoid CPU overload
                import time
                time.sleep(60)  # Adjust based on your bot's needs
            
            logger.info(f"[{self.user_id}] Bot stopped")
            
        except Exception as e:
            logger.error(f"[{self.user_id}] Critical error: {e}")
        finally:
            self.disconnect_mt5()
    
    def stop_bot(self):
        """Stop the bot"""
        self.bot_running = False
        logger.info(f"[{self.user_id}] Stop signal sent")
    
    def save_state(self, bot):
        """Save bot state for user"""
        try:
            state = {
                'user_id': self.user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'open_trades': len(bot.open_trades) if hasattr(bot, 'open_trades') else 0,
                'balance': bot.balance if hasattr(bot, 'balance') else 0,
                'equity': bot.equity if hasattr(bot, 'equity') else 0,
            }
            
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
        
        return {'status': 'error'}
```

---

## Step 2: Create Multi-User Bot Manager

Create `bot_manager.py`:

```python
"""
Manages multiple bot instances for different users
"""

import subprocess
import logging
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class BotManager:
    """Manages bot processes for multiple users"""
    
    def __init__(self):
        self.instances = {}  # user_id -> process info
        self.instances_file = Path('bot_instances.json')
        self.load_instances()
    
    def start_bot_for_user(self, user_id, user_config):
        """Start a bot instance for a user"""
        
        # Check if already running
        if user_id in self.instances and self.instances[user_id]['running']:
            logger.warning(f"Bot already running for {user_id}")
            return False
        
        try:
            # Create startup script for user
            script_content = f"""
import sys
sys.path.insert(0, '.')
from bot_multi_user import BotInstance
import json
import os

user_config = {json.dumps(user_config)}
bot = BotInstance("{user_id}", user_config)
bot.run_bot()
"""
            
            script_path = Path(f"bot_scripts/{user_id}_bot.py")
            script_path.parent.mkdir(exist_ok=True)
            
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Start bot process
            process = subprocess.Popen(
                ['python', str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.instances[user_id] = {
                'pid': process.pid,
                'running': True,
                'started_at': datetime.utcnow().isoformat(),
                'config': user_config
            }
            
            self.save_instances()
            logger.info(f"Started bot for user {user_id} (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start bot for {user_id}: {e}")
            return False
    
    def stop_bot_for_user(self, user_id):
        """Stop bot for a user"""
        try:
            if user_id not in self.instances:
                logger.warning(f"No bot instance found for {user_id}")
                return False
            
            instance = self.instances[user_id]
            pid = instance['pid']
            
            # Kill process
            import os
            os.kill(pid, 9)  # SIGKILL
            
            instance['running'] = False
            self.save_instances()
            logger.info(f"Stopped bot for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop bot for {user_id}: {e}")
            return False
    
    def get_bot_stats(self, user_id):
        """Get stats for user's bot"""
        try:
            state_file = Path(f"user_data/{user_id}/bot_state.json")
            if state_file.exists():
                with open(state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error getting stats for {user_id}: {e}")
        
        return None
    
    def save_instances(self):
        """Save instances to file"""
        with open(self.instances_file, 'w') as f:
            json.dump(self.instances, f, indent=2)
    
    def load_instances(self):
        """Load instances from file"""
        if self.instances_file.exists():
            with open(self.instances_file, 'r') as f:
                self.instances = json.load(f)

# Global instance
bot_manager = BotManager()
```

---

## Step 3: Update SaaS Backend

Modify `bot_platform.py` to use bot manager:

```python
# Add to bot_platform.py imports
from bot_manager import bot_manager

# ===== UPDATE BOT CONTROL ENDPOINTS =====

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
    
    # Prepare user config
    user_config = {
        'mt5_server': user.mt5_server,
        'mt5_account': user.mt5_account,
        'mt5_password': user.mt5_password,
        'symbols': json.loads(user.selected_symbols or '[]')
    }
    
    # Start bot using manager
    if bot_manager.start_bot_for_user(user_id, user_config):
        user.bot_running = True
        db.session.commit()
        
        return jsonify({'message': 'Bot started'}), 200
    else:
        return jsonify({'error': 'Failed to start bot'}), 500


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
    
    # Stop bot using manager
    if bot_manager.stop_bot_for_user(user_id):
        user.bot_running = False
        db.session.commit()
        
        return jsonify({'message': 'Bot stopped'}), 200
    else:
        return jsonify({'error': 'Failed to stop bot'}), 500


@app.route('/api/bot/stats', methods=['GET'])
@jwt_required()
def bot_stats():
    """Get bot stats for user"""
    user_id = get_jwt_identity()
    
    stats = bot_manager.get_bot_stats(user_id)
    if stats:
        return jsonify(stats), 200
    
    return jsonify({'error': 'No stats available'}), 404
```

---

## Step 4: Integrate Trade Recording

Modify your bot to save trades with user context:

```python
# In your existing bot
def record_trade(self, symbol, direction, entry, exit, pnl, user_id):
    """Record trade to database"""
    from bot_platform import db, Trade
    
    trade = Trade(
        user_id=user_id,
        symbol=symbol,
        direction=direction,
        entry_price=entry,
        exit_price=exit,
        pnl=pnl,
        status='CLOSED'
    )
    
    db.session.add(trade)
    db.session.commit()
    logger.info(f"Trade recorded for user {user_id}: {symbol} {direction} {pnl}")
```

---

## Step 5: Testing

### Test Individual User Bot

```python
# test_bot.py
from bot_multi_user import BotInstance

user_config = {
    'mt5_server': 'MetaQuotes-Demo',
    'mt5_account': '12345',
    'mt5_password': 'password',
    'symbols': ['EURUSD', 'GBPUSD']
}

bot = BotInstance('test_user_123', user_config)
bot.run_bot()
```

### Test Bot Manager

```python
from bot_manager import bot_manager

# Start bot for user 1
bot_manager.start_bot_for_user('user_1', user_config)

# Get stats
stats = bot_manager.get_bot_stats('user_1')
print(stats)

# Stop bot
bot_manager.stop_bot_for_user('user_1')
```

---

## Step 6: Docker Support

Update `Dockerfile` to include bot runner:

```dockerfile
# At end of Dockerfile
RUN mkdir -p /app/user_data /app/bot_scripts

# Run platform + bot manager
CMD ["sh", "-c", "python bot_platform.py & sleep 2 && python -m bot_manager"]
```

Or use supervisor for multiple processes:

```ini
# supervisor.conf
[program:platform]
command=/app/venv/bin/python /app/bot_platform.py
autostart=true

[program:bot_manager]
command=/app/venv/bin/python -c "from bot_manager import bot_manager; import time; time.sleep(999999)"
autostart=true
```

---

## Step 7: Monitoring

Add monitoring endpoints:

```python
@app.route('/api/admin/bots/status')
@jwt_required()
def get_all_bots_status():
    """Get status of all running bots"""
    from bot_manager import bot_manager
    
    return jsonify(bot_manager.instances), 200
```

---

## Migration Checklist

- [ ] Copy `bot_multi_user.py` to your project
- [ ] Copy `bot_manager.py` to your project
- [ ] Update `bot_platform.py` with new endpoints
- [ ] Modify existing bot to support `user_id` parameter
- [ ] Add trade recording function
- [ ] Test with single user first
- [ ] Test with multiple concurrent users
- [ ] Deploy to cloud
- [ ] Monitor bot instances

---

## Key Changes Summary

| Before | After |
|--------|-------|
| Single bot instance | Multiple instances (one per user) |
| One MT5 account | Multiple MT5 accounts |
| Global trade file | Per-user trade files |
| Manual start/stop | API-based start/stop |
| No user isolation | Full user isolation |

---

## Troubleshooting

### Bot doesn't start
- Check MT5 credentials
- Verify symbols are valid
- Check logs in `user_data/{user_id}/error.log`

### Multiple users interfering
- Ensure each user has separate data directory
- Check MT5 connections are isolated
- Verify trade recording passes user_id

### Memory leaks
- Add periodic cleanup of old log files
- Implement max limit on concurrent bots
- Monitor process memory usage

---

## Next Steps

1. Integrate bot wrapper
2. Test with 2-3 users
3. Deploy to cloud
4. Monitor performance
5. Scale to production

Your SaaS platform is now fully integrated! 🚀
