"""
Trading Strategy Engine - EA-Like Automated Bot System
Handles automatic trade execution based on user-defined rules
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import MetaTrader5 as mt5

logger = logging.getLogger(__name__)


@dataclass
class StrategyRule:
    """Single trading rule"""
    name: str
    indicator: str  # 'rsi', 'macd', 'sma_cross', 'price_level', 'custom'
    condition: str  # '>', '<', '==', 'cross_above', 'cross_below'
    value: float
    symbol: Optional[str] = None


@dataclass
class RiskManagement:
    """Risk management settings"""
    position_size: float  # Lot size (0.01, 0.1, 1.0, etc.)
    stop_loss_pips: float  # Distance in pips
    take_profit_pips: float  # Distance in pips
    max_daily_loss: Optional[float] = None  # Max daily loss in $
    max_concurrent_trades: int = 1  # Max open positions


@dataclass
class TradingStrategy:
    """Complete trading strategy (like an EA)"""
    strategy_id: str
    user_id: str
    name: str  # "EURUSD Morning Bot", "GBPUSD Scalper", etc.
    symbol: str  # "EURUSD"
    is_active: bool  # On/Off toggle
    entry_rules: List[StrategyRule]  # All must be TRUE to enter
    exit_rules: List[StrategyRule]  # ANY can be TRUE to exit
    risk_management: RiskManagement
    created_at: str
    last_modified: str
    status: str  # "idle", "waiting_entry", "in_trade", "error"
    last_trade_id: Optional[str] = None


class StrategyEvaluator:
    """Evaluates if strategy conditions are met"""
    
    def __init__(self, mt5_connection):
        self.mt5 = mt5_connection
        
    def evaluate_entry_conditions(self, strategy: TradingStrategy, current_data: Dict) -> bool:
        """
        Check if ALL entry rules are met
        Returns: True if entry signal triggered, False otherwise
        """
        if not strategy.is_active:
            return False
        
        try:
            for rule in strategy.entry_rules:
                if not self._evaluate_rule(rule, current_data):
                    return False  # ALL rules must be true
            return True
        except Exception as e:
            logger.error(f"Error evaluating entry conditions: {e}")
            return False
    
    def evaluate_exit_conditions(self, strategy: TradingStrategy, current_data: Dict) -> bool:
        """
        Check if ANY exit rule is met
        Returns: True if exit signal triggered, False otherwise
        """
        try:
            for rule in strategy.exit_rules:
                if self._evaluate_rule(rule, current_data):
                    return True  # ANY rule triggers exit
            return False
        except Exception as e:
            logger.error(f"Error evaluating exit conditions: {e}")
            return False
    
    def _evaluate_rule(self, rule: StrategyRule, data: Dict) -> bool:
        """Evaluate single rule"""
        
        if rule.indicator == "rsi":
            rsi_value = data.get("rsi")
            if rsi_value is None:
                return False
            
            if rule.condition == ">":
                return rsi_value > rule.value
            elif rule.condition == "<":
                return rsi_value < rule.value
            elif rule.condition == "==":
                return abs(rsi_value - rule.value) < 2
        
        elif rule.indicator == "macd":
            macd = data.get("macd")
            macd_signal = data.get("macd_signal")
            if macd is None or macd_signal is None:
                return False
            
            if rule.condition == "cross_above":
                return macd > macd_signal
            elif rule.condition == "cross_below":
                return macd < macd_signal
        
        elif rule.indicator == "sma_cross":
            # Format: "sma_fast:50,sma_slow:200"
            parts = rule.value.split(",")
            sma_fast = data.get("sma_fast")
            sma_slow = data.get("sma_slow")
            
            if sma_fast is None or sma_slow is None:
                return False
            
            if rule.condition == "cross_above":
                return sma_fast > sma_slow
            elif rule.condition == "cross_below":
                return sma_fast < sma_slow
        
        elif rule.indicator == "price_level":
            current_price = data.get("close")
            if current_price is None:
                return False
            
            if rule.condition == ">":
                return current_price > rule.value
            elif rule.condition == "<":
                return current_price < rule.value
        
        elif rule.indicator == "custom":
            # User-defined logic - extend here
            return data.get("custom_signal", False)
        
        return False


class StrategyExecutor:
    """Executes trades based on strategy signals"""
    
    def __init__(self, mt5_connection):
        self.mt5 = mt5_connection
        self.open_trades = {}  # {trade_id: trade_data}
    
    def execute_entry(self, strategy: TradingStrategy, current_price: float) -> Optional[Dict]:
        """
        Execute entry trade
        Returns: Trade dict with ticket, entry_price, sl, tp, or None if failed
        """
        try:
            risk = strategy.risk_management
            
            # Calculate stop loss and take profit
            stop_loss = current_price - (risk.stop_loss_pips * 0.0001)  # Assuming 4 decimal places
            take_profit = current_price + (risk.take_profit_pips * 0.0001)
            
            # Prepare order
            order_type = mt5.ORDER_TYPE_BUY if strategy.entry_rules[0].condition == ">" else mt5.ORDER_TYPE_SELL
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": strategy.symbol,
                "volume": risk.position_size,
                "type": order_type,
                "price": current_price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": 20,
                "magic": int(strategy.strategy_id.split("_")[1]),  # Strategy ID as magic number
                "comment": f"EA:{strategy.name}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = self.mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order send failed: {result.comment}")
                return None
            
            trade_data = {
                "ticket": result.order,
                "strategy_id": strategy.strategy_id,
                "symbol": strategy.symbol,
                "entry_price": current_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "position_size": risk.position_size,
                "entry_time": datetime.now().isoformat(),
                "status": "open"
            }
            
            self.open_trades[str(result.order)] = trade_data
            logger.info(f"Entry executed: {strategy.name} BUY {strategy.symbol} @ {current_price}")
            return trade_data
            
        except Exception as e:
            logger.error(f"Entry execution error: {e}")
            return None
    
    def execute_exit(self, ticket: int, exit_price: float, reason: str) -> Optional[Dict]:
        """
        Close existing trade
        Returns: Trade closing result dict
        """
        try:
            # Get current position
            position = self.mt5.positions_get(ticket=ticket)
            if not position:
                return None
            
            pos = position[0]
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,
                "position": ticket,
                "price": exit_price,
                "deviation": 20,
                "comment": f"Exit: {reason}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = self.mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Exit failed: {result.comment}")
                return None
            
            profit = (exit_price - pos.price_open) * pos.volume * (100000 if "JPY" in pos.symbol else 10000)
            
            exit_data = {
                "ticket": ticket,
                "exit_price": exit_price,
                "profit": profit,
                "exit_reason": reason,
                "exit_time": datetime.now().isoformat(),
                "status": "closed"
            }
            
            if str(ticket) in self.open_trades:
                del self.open_trades[str(ticket)]
            
            logger.info(f"Exit executed: {pos.symbol} CLOSE @ {exit_price}, P&L: {profit}")
            return exit_data
            
        except Exception as e:
            logger.error(f"Exit execution error: {e}")
            return None


class MarketDataCollector:
    """Collects real-time market data for strategy evaluation"""
    
    def __init__(self, mt5_connection):
        self.mt5 = mt5_connection
        self.last_candles = {}  # Cache for indicators
    
    def get_current_market_data(self, symbol: str, timeframe: int = mt5.TIMEFRAME_M15) -> Optional[Dict]:
        """
        Fetch real-time market data including indicators
        Returns: Dict with price, RSI, MACD, SMA, etc.
        """
        try:
            # Get current tick
            tick = self.mt5.symbol_info_tick(symbol)
            if not tick:
                return None
            
            # Get last candles for indicators
            rates = self.mt5.copy_rates_from_pos(symbol, timeframe, 0, 200)
            if rates is None or len(rates) < 50:
                return None
            
            # Calculate indicators
            close_prices = [float(r['close']) for r in rates]
            
            data = {
                "symbol": symbol,
                "close": float(tick.last),
                "bid": float(tick.bid),
                "ask": float(tick.ask),
                "timestamp": tick.time,
                
                # Technical indicators
                "rsi": self._calculate_rsi(close_prices),
                "macd": self._calculate_macd(close_prices)[0],
                "macd_signal": self._calculate_macd(close_prices)[1],
                "sma_fast": self._calculate_sma(close_prices, 50),
                "sma_slow": self._calculate_sma(close_prices, 200),
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Error collecting market data: {e}")
            return None
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        if len(prices) < period:
            return 50
        
        gains = [max(prices[i] - prices[i-1], 0) for i in range(1, len(prices))]
        losses = [max(prices[i-1] - prices[i], 0) for i in range(1, len(prices))]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100 if avg_gain > 0 else 50
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: List[float]) -> Tuple[float, float]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        ema12 = self._calculate_ema(prices, 12)
        ema26 = self._calculate_ema(prices, 26)
        macd_line = ema12 - ema26
        
        macd_values = [ema12 - ema26 for ema12, ema26 in zip(
            self._calculate_ema(prices, 12),
            self._calculate_ema(prices, 26)
        )]
        signal_line = self._calculate_ema(macd_values, 9)
        
        return macd_line, signal_line
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA (Exponential Moving Average)"""
        if len(prices) < period:
            return sum(prices) / len(prices)
        
        k = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = price * k + ema * (1 - k)
        
        return ema
    
    def _calculate_sma(self, prices: List[float], period: int) -> float:
        """Calculate SMA (Simple Moving Average)"""
        if len(prices) < period:
            return sum(prices) / len(prices)
        return sum(prices[-period:]) / period


class StrategyManager:
    """Manages strategy lifecycle"""
    
    def __init__(self, mt5_connection):
        self.mt5 = mt5_connection
        self.strategies: Dict[str, TradingStrategy] = {}
        self.evaluator = StrategyEvaluator(mt5_connection)
        self.executor = StrategyExecutor(mt5_connection)
        self.data_collector = MarketDataCollector(mt5_connection)
    
    def add_strategy(self, strategy: TradingStrategy):
        """Register new strategy"""
        self.strategies[strategy.strategy_id] = strategy
        strategy.status = "idle"
        logger.info(f"Strategy added: {strategy.name}")
    
    def activate_strategy(self, strategy_id: str):
        """Turn strategy ON"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].is_active = True
            logger.info(f"Strategy activated: {strategy_id}")
    
    def deactivate_strategy(self, strategy_id: str):
        """Turn strategy OFF"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].is_active = False
            logger.info(f"Strategy deactivated: {strategy_id}")
    
    def update_strategy(self, strategy_id: str, updates: Dict):
        """Modify strategy parameters (while it's running!)"""
        if strategy_id in self.strategies:
            strategy = self.strategies[strategy_id]
            strategy.last_modified = datetime.now().isoformat()
            
            if "entry_rules" in updates:
                strategy.entry_rules = updates["entry_rules"]
            if "exit_rules" in updates:
                strategy.exit_rules = updates["exit_rules"]
            if "risk_management" in updates:
                strategy.risk_management = updates["risk_management"]
            
            logger.info(f"Strategy updated: {strategy_id}")
    
    def process_all_strategies(self) -> List[Dict]:
        """
        Main loop - Check all active strategies and execute trades
        Call this repeatedly (every tick/candle)
        """
        results = []
        
        for strategy_id, strategy in self.strategies.items():
            if not strategy.is_active:
                continue
            
            try:
                # Get current market data
                data = self.data_collector.get_current_market_data(strategy.symbol)
                if not data:
                    continue
                
                # Check entry signals
                if strategy.status == "idle":
                    if self.evaluator.evaluate_entry_conditions(strategy, data):
                        trade = self.executor.execute_entry(strategy, data["close"])
                        if trade:
                            strategy.status = "in_trade"
                            strategy.last_trade_id = str(trade["ticket"])
                            results.append({
                                "event": "entry",
                                "strategy": strategy.name,
                                "trade": trade
                            })
                
                # Check exit signals
                elif strategy.status == "in_trade":
                    if self.evaluator.evaluate_exit_conditions(strategy, data):
                        if strategy.last_trade_id:
                            ticket = int(strategy.last_trade_id)
                            exit_data = self.executor.execute_exit(ticket, data["close"], "Strategy signal")
                            if exit_data:
                                strategy.status = "idle"
                                results.append({
                                    "event": "exit",
                                    "strategy": strategy.name,
                                    "trade": exit_data
                                })
            
            except Exception as e:
                logger.error(f"Error processing strategy {strategy_id}: {e}")
                strategy.status = "error"
        
        return results
    
    def get_strategy_status(self, strategy_id: str) -> Optional[Dict]:
        """Get current strategy status"""
        if strategy_id not in self.strategies:
            return None
        
        strategy = self.strategies[strategy_id]
        return {
            "strategy_id": strategy.strategy_id,
            "name": strategy.name,
            "symbol": strategy.symbol,
            "is_active": strategy.is_active,
            "status": strategy.status,
            "last_trade_id": strategy.last_trade_id,
            "last_modified": strategy.last_modified,
            "position_size": strategy.risk_management.position_size,
            "sl_pips": strategy.risk_management.stop_loss_pips,
            "tp_pips": strategy.risk_management.take_profit_pips,
        }
    
    def get_all_strategies(self, user_id: str) -> List[Dict]:
        """Get all strategies for user"""
        user_strategies = [
            asdict(s) for s in self.strategies.values()
            if s.user_id == user_id
        ]
        return user_strategies
