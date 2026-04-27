"""
Bot Manager - Manages multiple bot instances for different users
Handles starting, stopping, and monitoring bots
"""

import subprocess
import logging
import json
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class BotManager:
    """Manages bot processes for multiple users"""
    
    def __init__(self):
        self.instances = {}  # user_id -> process info
        self.instances_file = Path('bot_instances.json')
        self.bot_scripts_dir = Path('bot_scripts')
        self.bot_scripts_dir.mkdir(exist_ok=True)
        self.user_data_dir = Path('user_data')
        self.user_data_dir.mkdir(exist_ok=True)
        self.load_instances()
    
    def start_bot_for_user(self, user_id, user_config):
        """Start a bot instance for a user"""
        
        # Check if already running
        if user_id in self.instances:
            if self.instances[user_id].get('running'):
                logger.warning(f"Bot already running for {user_id}")
                return False
            # Remove stale instance
            del self.instances[user_id]
        
        try:
            # Create startup script for user
            script_path = self.bot_scripts_dir / f"{user_id}_bot.py"
            
            # Generate script content
            script_content = f'''import sys
import os
import json
sys.path.insert(0, '.')

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")

from bot_multi_user import BotInstance
import logging

logging.basicConfig(level=logging.INFO)

user_config = {json.dumps(user_config)}
bot = BotInstance("{user_id}", user_config)
bot.run_bot()
'''
            
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Start bot process
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            self.instances[user_id] = {
                'pid': process.pid,
                'running': True,
                'started_at': datetime.utcnow().isoformat(),
                'config': user_config,
                'process': process
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
            pid = instance.get('pid')
            
            if not pid:
                logger.warning(f"No PID for bot {user_id}")
                del self.instances[user_id]
                self.save_instances()
                return False
            
            # Kill process
            try:
                if 'process' in instance:
                    instance['process'].terminate()
                    try:
                        instance['process'].wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        instance['process'].kill()
                else:
                    os.kill(pid, 9)  # SIGKILL
            except ProcessLookupError:
                pass  # Process already dead
            
            instance['running'] = False
            instance['stopped_at'] = datetime.utcnow().isoformat()
            self.save_instances()
            logger.info(f"Stopped bot for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop bot for {user_id}: {e}")
            return False
    
    def restart_bot_for_user(self, user_id, user_config):
        """Restart bot for a user"""
        self.stop_bot_for_user(user_id)
        return self.start_bot_for_user(user_id, user_config)
    
    def is_bot_running(self, user_id):
        """Check if bot is running for user"""
        if user_id not in self.instances:
            return False
        
        instance = self.instances[user_id]
        if not instance.get('running'):
            return False
        
        # Verify process still exists
        pid = instance.get('pid')
        if pid:
            try:
                os.kill(pid, 0)  # Check if process exists
                return True
            except OSError:
                instance['running'] = False
                self.save_instances()
                return False
        
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
    
    def get_bot_trades(self, user_id):
        """Get trades recorded by user's bot"""
        try:
            trades_file = Path(f"user_data/{user_id}/trades.json")
            if trades_file.exists():
                with open(trades_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error getting trades for {user_id}: {e}")
        
        return []
    
    def get_all_running_bots(self):
        """Get all currently running bots"""
        running = {}
        for user_id, instance in self.instances.items():
            if self.is_bot_running(user_id):
                running[user_id] = {
                    'pid': instance.get('pid'),
                    'started_at': instance.get('started_at'),
                    'symbols': instance.get('config', {}).get('symbols', [])
                }
        return running
    
    def stop_all_bots(self):
        """Stop all running bots"""
        logger.info("Stopping all bots...")
        for user_id in list(self.instances.keys()):
            if self.is_bot_running(user_id):
                self.stop_bot_for_user(user_id)
    
    def save_instances(self):
        """Save instances to file"""
        try:
            # Don't serialize process objects
            serializable = {}
            for uid, inst in self.instances.items():
                serializable[uid] = {k: v for k, v in inst.items() if k != 'process'}
            
            with open(self.instances_file, 'w') as f:
                json.dump(serializable, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving instances: {e}")
    
    def load_instances(self):
        """Load instances from file"""
        try:
            if self.instances_file.exists():
                with open(self.instances_file, 'r') as f:
                    self.instances = json.load(f)
        except Exception as e:
            logger.error(f"Error loading instances: {e}")
            self.instances = {}


# Global instance
import sys
bot_manager = BotManager()


if __name__ == '__main__':
    # Test bot manager
    import sys
    logging.basicConfig(level=logging.INFO)
    
    # Start test bots
    for i in range(2):
        config = {
            'mt5_server': 'MetaQuotes-Demo',
            'mt5_account': f'10000{i}',
            'mt5_password': 'password',
            'symbols': ['EURUSD', 'GBPUSD']
        }
        bot_manager.start_bot_for_user(f'test_user_{i}', config)
    
    print("Running bots:", bot_manager.get_all_running_bots())
    
    # Keep running
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\nShutting down...")
        bot_manager.stop_all_bots()
