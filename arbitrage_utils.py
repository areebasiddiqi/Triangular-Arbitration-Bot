"""
Utility functions for the Triangular Arbitrage Bot
"""

import logging
import json
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import asdict

logger = logging.getLogger(__name__)

class ProfitTracker:
    """Track and analyze arbitrage profits"""
    
    def __init__(self):
        self.trades = []
        self.daily_profits = {}
        
    def add_trade(self, opportunity, executed: bool = False, actual_profit: float = 0):
        """Add a trade to the tracker"""
        trade_data = {
            'timestamp': datetime.now().isoformat(),
            'opportunity': asdict(opportunity),
            'executed': executed,
            'actual_profit': actual_profit,
            'expected_profit': opportunity.profit_percentage
        }
        self.trades.append(trade_data)
        
        # Update daily profits
        date_key = datetime.now().strftime('%Y-%m-%d')
        if date_key not in self.daily_profits:
            self.daily_profits[date_key] = {
                'total_profit': 0,
                'trades_count': 0,
                'successful_trades': 0
            }
        
        if executed:
            self.daily_profits[date_key]['total_profit'] += actual_profit
            self.daily_profits[date_key]['successful_trades'] += 1
        
        self.daily_profits[date_key]['trades_count'] += 1
    
    def get_daily_summary(self, date: str = None) -> Dict:
        """Get daily profit summary"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        return self.daily_profits.get(date, {
            'total_profit': 0,
            'trades_count': 0,
            'successful_trades': 0
        })
    
    def get_performance_metrics(self, days: int = 7) -> Dict:
        """Get performance metrics for the last N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        total_profit = 0
        total_trades = 0
        successful_trades = 0
        
        for date_str, data in self.daily_profits.items():
            date = datetime.strptime(date_str, '%Y-%m-%d')
            if start_date <= date <= end_date:
                total_profit += data['total_profit']
                total_trades += data['trades_count']
                successful_trades += data['successful_trades']
        
        success_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
        avg_profit_per_trade = total_profit / successful_trades if successful_trades > 0 else 0
        
        return {
            'period_days': days,
            'total_profit': total_profit,
            'total_trades': total_trades,
            'successful_trades': successful_trades,
            'success_rate': success_rate,
            'avg_profit_per_trade': avg_profit_per_trade
        }
    
    def save_to_file(self, filename: str = 'arbitrage_trades.json'):
        """Save trade data to file"""
        try:
            data = {
                'trades': self.trades,
                'daily_profits': self.daily_profits,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Trade data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving trade data: {e}")
    
    def load_from_file(self, filename: str = 'arbitrage_trades.json'):
        """Load trade data from file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.trades = data.get('trades', [])
            self.daily_profits = data.get('daily_profits', {})
            
            logger.info(f"Trade data loaded from {filename}")
            
        except FileNotFoundError:
            logger.info(f"No existing trade data file found: {filename}")
        except Exception as e:
            logger.error(f"Error loading trade data: {e}")

class RiskManager:
    """Manage trading risks and position sizing"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.daily_trade_count = 0
        self.daily_profit = 0
        self.last_trade_time = 0
        self.current_positions = {}
        
    def can_trade(self, opportunity) -> bool:
        """Check if we can execute a trade based on risk parameters"""
        try:
            # Check daily trade limit
            max_daily_trades = self.config.get('risk_management', {}).get('max_daily_trades', 50)
            if self.daily_trade_count >= max_daily_trades:
                logger.warning("Daily trade limit reached")
                return False
            
            # Check cooldown period
            cooldown = self.config.get('risk_management', {}).get('cooldown_period', 60)
            if time.time() - self.last_trade_time < cooldown:
                logger.warning("Cooldown period not met")
                return False
            
            # Check position size
            max_position = self.config.get('risk_management', {}).get('max_position_size', 1000)
            if opportunity.profit_amount > max_position:
                logger.warning("Position size too large")
                return False
            
            # Check minimum profit threshold
            min_profit = self.config.get('min_profit_threshold', 0.5)
            if opportunity.profit_percentage < min_profit:
                logger.warning("Profit below minimum threshold")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in risk check: {e}")
            return False
    
    def calculate_position_size(self, opportunity, available_balance: float) -> float:
        """Calculate optimal position size"""
        try:
            max_trade_amount = self.config.get('max_trade_amount', 100)
            max_position_size = self.config.get('risk_management', {}).get('max_position_size', 1000)
            
            # Use smaller of configured max or available balance
            position_size = min(max_trade_amount, available_balance * 0.1)  # Max 10% of balance
            position_size = min(position_size, max_position_size)
            
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0
    
    def update_trade_stats(self, executed: bool = False, profit: float = 0):
        """Update trade statistics"""
        if executed:
            self.daily_trade_count += 1
            self.daily_profit += profit
            self.last_trade_time = time.time()

class NotificationManager:
    """Handle notifications and alerts"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.notification_config = config.get('notifications', {})
        
    async def send_opportunity_alert(self, opportunity):
        """Send alert for profitable opportunity"""
        try:
            if not self.notification_config.get('enable_alerts', False):
                return
            
            min_profit = self.notification_config.get('min_profit_for_alert', 1.0)
            if opportunity.profit_percentage < min_profit:
                return
            
            message = self.format_opportunity_message(opportunity)
            
            # Send to webhook if configured
            webhook_url = self.notification_config.get('webhook_url')
            if webhook_url:
                await self.send_webhook_notification(webhook_url, message)
            
            # Log the alert
            logger.info(f"ALERT: {message}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def format_opportunity_message(self, opportunity) -> str:
        """Format opportunity data into a readable message"""
        return (
            f"🚀 Arbitrage Opportunity Found!\n"
            f"Path: {' → '.join(opportunity.path)}\n"
            f"Profit: {opportunity.profit_percentage:.4f}%\n"
            f"Exchange: {opportunity.exchange}\n"
            f"Time: {opportunity.timestamp.strftime('%H:%M:%S')}"
        )
    
    async def send_webhook_notification(self, webhook_url: str, message: str):
        """Send notification to webhook URL"""
        try:
            import aiohttp
            
            payload = {
                'text': message,
                'timestamp': datetime.now().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Webhook notification sent successfully")
                    else:
                        logger.warning(f"Webhook notification failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")

class MarketDataAnalyzer:
    """Analyze market data for better arbitrage detection"""
    
    def __init__(self):
        self.price_history = {}
        self.volatility_data = {}
        
    def add_price_data(self, symbol: str, price: float, timestamp: datetime = None):
        """Add price data for analysis"""
        if timestamp is None:
            timestamp = datetime.now()
        
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append({
            'price': price,
            'timestamp': timestamp
        })
        
        # Keep only last 100 data points
        if len(self.price_history[symbol]) > 100:
            self.price_history[symbol] = self.price_history[symbol][-100:]
    
    def calculate_volatility(self, symbol: str, window: int = 20) -> float:
        """Calculate price volatility for a symbol"""
        try:
            if symbol not in self.price_history or len(self.price_history[symbol]) < window:
                return 0.0
            
            prices = [data['price'] for data in self.price_history[symbol][-window:]]
            prices_series = pd.Series(prices)
            
            # Calculate returns
            returns = prices_series.pct_change().dropna()
            
            # Calculate volatility (standard deviation of returns)
            volatility = returns.std() * 100  # Convert to percentage
            
            self.volatility_data[symbol] = volatility
            return volatility
            
        except Exception as e:
            logger.error(f"Error calculating volatility for {symbol}: {e}")
            return 0.0
    
    def get_price_trend(self, symbol: str, window: int = 10) -> str:
        """Get price trend direction"""
        try:
            if symbol not in self.price_history or len(self.price_history[symbol]) < window:
                return "unknown"
            
            recent_prices = [data['price'] for data in self.price_history[symbol][-window:]]
            
            if len(recent_prices) < 2:
                return "unknown"
            
            # Simple trend calculation
            start_price = recent_prices[0]
            end_price = recent_prices[-1]
            
            change_percentage = ((end_price - start_price) / start_price) * 100
            
            if change_percentage > 1:
                return "uptrend"
            elif change_percentage < -1:
                return "downtrend"
            else:
                return "sideways"
                
        except Exception as e:
            logger.error(f"Error calculating trend for {symbol}: {e}")
            return "unknown"
    
    def is_market_suitable_for_arbitrage(self, symbols: List[str]) -> bool:
        """Check if market conditions are suitable for arbitrage"""
        try:
            # Check volatility levels
            high_volatility_count = 0
            
            for symbol in symbols:
                volatility = self.calculate_volatility(symbol)
                if volatility > 5.0:  # High volatility threshold
                    high_volatility_count += 1
            
            # If more than 50% of symbols have high volatility, market might be too risky
            if high_volatility_count / len(symbols) > 0.5:
                logger.warning("High market volatility detected - proceed with caution")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking market suitability: {e}")
            return True  # Default to allowing trades

def format_currency_amount(amount: float, currency: str) -> str:
    """Format currency amount for display"""
    if currency in ['BTC', 'ETH']:
        return f"{amount:.8f} {currency}"
    elif currency in ['USDT', 'USD']:
        return f"${amount:.2f}"
    else:
        return f"{amount:.6f} {currency}"

def calculate_fees(amount: float, fee_rate: float = 0.001) -> float:
    """Calculate trading fees"""
    return amount * fee_rate

def validate_trading_pair(pair: str) -> bool:
    """Validate trading pair format"""
    try:
        if '/' not in pair:
            return False
        
        base, quote = pair.split('/')
        
        if len(base) < 2 or len(quote) < 2:
            return False
        
        return True
        
    except Exception:
        return False
