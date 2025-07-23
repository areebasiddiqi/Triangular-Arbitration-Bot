"""
Simple Dashboard for Triangular Arbitrage Bot
Provides real-time monitoring and basic controls
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
import os
from typing import Dict, List
from triangular_arbitrage_bot import TriangularArbitrageBot
from arbitrage_utils import ProfitTracker, MarketDataAnalyzer
import logging

# Configure logging for dashboard
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ArbitrageDashboard:
    """Simple text-based dashboard for monitoring the bot"""
    
    def __init__(self):
        self.bot = None
        self.profit_tracker = ProfitTracker()
        self.market_analyzer = MarketDataAnalyzer()
        self.running = False
        self.last_opportunities = []
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_header(self):
        """Display dashboard header"""
        print("=" * 80)
        print("🚀 TRIANGULAR ARBITRAGE BOT DASHBOARD 🚀")
        print("=" * 80)
        print(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Status: {'🟢 RUNNING' if self.running else '🔴 STOPPED'}")
        print("-" * 80)
    
    def display_performance_metrics(self):
        """Display performance metrics"""
        metrics = self.profit_tracker.get_performance_metrics(7)
        daily_summary = self.profit_tracker.get_daily_summary()
        
        print("📊 PERFORMANCE METRICS (Last 7 Days)")
        print("-" * 40)
        print(f"Total Profit: ${metrics['total_profit']:.2f}")
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Successful Trades: {metrics['successful_trades']}")
        print(f"Success Rate: {metrics['success_rate']:.1f}%")
        print(f"Avg Profit/Trade: ${metrics['avg_profit_per_trade']:.2f}")
        print()
        
        print("📅 TODAY'S SUMMARY")
        print("-" * 20)
        print(f"Today's Profit: ${daily_summary['total_profit']:.2f}")
        print(f"Today's Trades: {daily_summary['trades_count']}")
        print(f"Successful: {daily_summary['successful_trades']}")
        print()
    
    def display_recent_opportunities(self):
        """Display recent arbitrage opportunities"""
        print("🎯 RECENT OPPORTUNITIES")
        print("-" * 50)
        
        if not self.last_opportunities:
            print("No recent opportunities found.")
        else:
            for i, opp in enumerate(self.last_opportunities[:5]):
                status = "✅" if opp.get('executed', False) else "⏳"
                print(f"{status} {opp['path']} | Profit: {opp['profit']:.4f}% | {opp['exchange']}")
        print()
    
    def display_market_status(self):
        """Display market status information"""
        print("📈 MARKET STATUS")
        print("-" * 20)
        
        # This would be populated with real market data
        print("BTC/USDT: $43,250.00 (↗ +2.1%)")
        print("ETH/USDT: $2,580.00 (↗ +1.8%)")
        print("BNB/USDT: $315.50 (↘ -0.5%)")
        print()
    
    def display_bot_config(self):
        """Display current bot configuration"""
        if self.bot:
            config = self.bot.config
            print("⚙️ BOT CONFIGURATION")
            print("-" * 25)
            print(f"Min Profit Threshold: {config.get('min_profit_threshold', 0.5)}%")
            print(f"Max Trade Amount: ${config.get('max_trade_amount', 100)}")
            print(f"Scan Interval: {config.get('scan_interval', 5)}s")
            print(f"Trading Enabled: {'Yes' if config.get('enable_trading', False) else 'No'}")
            print(f"Exchanges: {', '.join(config.get('exchanges', {}).keys())}")
            print()
    
    def display_controls(self):
        """Display available controls"""
        print("🎮 CONTROLS")
        print("-" * 15)
        print("S - Start/Stop Bot")
        print("T - Toggle Trading")
        print("C - Clear Logs")
        print("R - Reset Stats")
        print("Q - Quit Dashboard")
        print("=" * 80)
    
    async def update_opportunities(self):
        """Update opportunities data (mock for now)"""
        # In a real implementation, this would fetch from the bot
        mock_opportunities = [
            {
                'path': 'USDT → BTC → ETH → USDT',
                'profit': 0.75,
                'exchange': 'Binance',
                'executed': False,
                'timestamp': datetime.now()
            },
            {
                'path': 'BTC → ETH → BNB → BTC',
                'profit': 0.45,
                'exchange': 'Binance',
                'executed': True,
                'timestamp': datetime.now() - timedelta(minutes=2)
            }
        ]
        
        self.last_opportunities = mock_opportunities
    
    async def run_dashboard(self):
        """Main dashboard loop"""
        print("Starting Arbitrage Bot Dashboard...")
        
        try:
            # Initialize bot
            self.bot = TriangularArbitrageBot()
            self.profit_tracker.load_from_file()
            
            while True:
                self.clear_screen()
                self.display_header()
                self.display_performance_metrics()
                self.display_recent_opportunities()
                self.display_market_status()
                self.display_bot_config()
                self.display_controls()
                
                # Update data
                await self.update_opportunities()
                
                # Check for user input (non-blocking)
                # Note: This is a simplified version. In production, you'd use proper async input handling
                await asyncio.sleep(2)
                
        except KeyboardInterrupt:
            print("\nDashboard stopped by user.")
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
        finally:
            if self.bot:
                await self.bot.stop()

class SimpleArbitrageMonitor:
    """Simplified monitoring class for command-line usage"""
    
    def __init__(self):
        self.opportunities_found = 0
        self.trades_executed = 0
        self.total_profit = 0.0
        self.start_time = datetime.now()
    
    def log_opportunity(self, opportunity):
        """Log a found opportunity"""
        self.opportunities_found += 1
        
        print(f"\n🎯 Opportunity #{self.opportunities_found}")
        print(f"Path: {' → '.join(opportunity.path)}")
        print(f"Profit: {opportunity.profit_percentage:.4f}%")
        print(f"Exchange: {opportunity.exchange}")
        print(f"Time: {opportunity.timestamp.strftime('%H:%M:%S')}")
        print("-" * 50)
    
    def log_trade_execution(self, opportunity, success: bool, actual_profit: float = 0):
        """Log trade execution"""
        if success:
            self.trades_executed += 1
            self.total_profit += actual_profit
            
            print(f"\n✅ Trade Executed Successfully!")
            print(f"Expected Profit: {opportunity.profit_percentage:.4f}%")
            print(f"Actual Profit: ${actual_profit:.2f}")
        else:
            print(f"\n❌ Trade Execution Failed")
        
        print("-" * 50)
    
    def display_summary(self):
        """Display session summary"""
        runtime = datetime.now() - self.start_time
        
        print(f"\n📊 SESSION SUMMARY")
        print(f"Runtime: {runtime}")
        print(f"Opportunities Found: {self.opportunities_found}")
        print(f"Trades Executed: {self.trades_executed}")
        print(f"Total Profit: ${self.total_profit:.2f}")
        
        if self.opportunities_found > 0:
            success_rate = (self.trades_executed / self.opportunities_found) * 100
            print(f"Success Rate: {success_rate:.1f}%")

async def run_simple_monitor():
    """Run a simple monitoring session"""
    monitor = SimpleArbitrageMonitor()
    bot = TriangularArbitrageBot()
    
    print("🚀 Starting Simple Arbitrage Monitor...")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Start monitoring (this is a simplified version)
        start_time = time.time()
        
        while True:
            # Simulate opportunity detection
            await asyncio.sleep(10)
            
            # In real implementation, this would come from the bot
            print(f"⏱️  Scanning... ({int(time.time() - start_time)}s elapsed)")
            
            # Mock opportunity for demonstration
            if int(time.time()) % 30 == 0:  # Every 30 seconds
                from triangular_arbitrage_bot import ArbitrageOpportunity
                mock_opp = ArbitrageOpportunity(
                    base_currency="USDT",
                    quote_currency="BTC",
                    intermediate_currency="ETH",
                    profit_percentage=0.65,
                    profit_amount=6.5,
                    path=["USDT", "BTC", "ETH", "USDT"],
                    prices={},
                    volumes={},
                    exchange="Binance",
                    timestamp=datetime.now()
                )
                monitor.log_opportunity(mock_opp)
    
    except KeyboardInterrupt:
        print("\n\nMonitor stopped by user.")
        monitor.display_summary()
    
    finally:
        await bot.stop()

def main():
    """Main function to choose between dashboard and simple monitor"""
    print("Triangular Arbitrage Bot Monitor")
    print("1. Full Dashboard")
    print("2. Simple Monitor")
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == "1":
        dashboard = ArbitrageDashboard()
        asyncio.run(dashboard.run_dashboard())
    elif choice == "2":
        asyncio.run(run_simple_monitor())
    else:
        print("Invalid choice. Starting simple monitor...")
        asyncio.run(run_simple_monitor())

if __name__ == "__main__":
    main()
