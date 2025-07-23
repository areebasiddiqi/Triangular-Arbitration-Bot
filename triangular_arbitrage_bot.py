"""
Triangular Arbitrage Bot for Cryptocurrency Trading
Supports Binance and other exchanges for triangular arbitrage opportunities
"""

import asyncio
import logging
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
import ccxt
import ccxt.async_support as ccxt_async
from datetime import datetime
import json
import os
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arbitrage_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ArbitrageOpportunity:
    """Data class for arbitrage opportunities"""
    base_currency: str
    quote_currency: str
    intermediate_currency: str
    profit_percentage: float
    profit_amount: float
    path: List[str]
    prices: Dict[str, float]
    volumes: Dict[str, float]
    exchange: str
    timestamp: datetime

@dataclass
class TradingPair:
    """Data class for trading pairs"""
    symbol: str
    base: str
    quote: str
    price: float
    volume: float
    bid: float
    ask: float

class ExchangeManager:
    """Manages multiple exchange connections"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.exchanges = {}
        self.async_exchanges = {}
        self.initialize_exchanges()
    
    def initialize_exchanges(self):
        """Initialize exchange connections"""
        try:
            # Binance
            if 'binance' in self.config['exchanges']:
                binance_config = self.config['exchanges']['binance']
                self.exchanges['binance'] = ccxt.binance({
                    'apiKey': binance_config.get('api_key', ''),
                    'secret': binance_config.get('secret', ''),
                    'sandbox': binance_config.get('sandbox', True),
                    'enableRateLimit': True,
                })
                
                self.async_exchanges['binance'] = ccxt_async.binance({
                    'apiKey': binance_config.get('api_key', ''),
                    'secret': binance_config.get('secret', ''),
                    'sandbox': binance_config.get('sandbox', True),
                    'enableRateLimit': True,
                })
            
            # Add more exchanges as needed
            if 'kucoin' in self.config['exchanges']:
                kucoin_config = self.config['exchanges']['kucoin']
                self.exchanges['kucoin'] = ccxt.kucoin({
                    'apiKey': kucoin_config.get('api_key', ''),
                    'secret': kucoin_config.get('secret', ''),
                    'password': kucoin_config.get('passphrase', ''),
                    'sandbox': kucoin_config.get('sandbox', True),
                    'enableRateLimit': True,
                })
                
                self.async_exchanges['kucoin'] = ccxt_async.kucoin({
                    'apiKey': kucoin_config.get('api_key', ''),
                    'secret': kucoin_config.get('secret', ''),
                    'password': kucoin_config.get('passphrase', ''),
                    'sandbox': kucoin_config.get('sandbox', True),
                    'enableRateLimit': True,
                })
            
            logger.info(f"Initialized {len(self.exchanges)} exchanges")
            
        except Exception as e:
            logger.error(f"Error initializing exchanges: {e}")
            raise
    
    async def get_ticker(self, exchange_name: str, symbol: str) -> Optional[Dict]:
        """Get ticker data for a symbol from specific exchange"""
        try:
            exchange = self.async_exchanges.get(exchange_name)
            if not exchange:
                return None
            
            ticker = await exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.warning(f"Error fetching ticker {symbol} from {exchange_name}: {e}")
            return None
    
    async def get_order_book(self, exchange_name: str, symbol: str, limit: int = 5) -> Optional[Dict]:
        """Get order book for a symbol"""
        try:
            exchange = self.async_exchanges.get(exchange_name)
            if not exchange:
                return None
            
            order_book = await exchange.fetch_order_book(symbol, limit)
            return order_book
        except Exception as e:
            logger.warning(f"Error fetching order book {symbol} from {exchange_name}: {e}")
            return None
    
    async def close_all(self):
        """Close all async exchange connections"""
        for exchange in self.async_exchanges.values():
            await exchange.close()

class TriangularArbitrageBot:
    """Main triangular arbitrage bot class"""
    
    def __init__(self, config_file: str = 'arbitrage_config.json'):
        self.config = self.load_config(config_file)
        self.exchange_manager = ExchangeManager(self.config)
        self.min_profit_threshold = self.config.get('min_profit_threshold', 0.5)  # 0.5%
        self.max_trade_amount = self.config.get('max_trade_amount', 100)  # USDT
        self.trading_pairs = {}
        self.opportunities = []
        self.running = False
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default config
                default_config = {
                    "exchanges": {
                        "binance": {
                            "api_key": "",
                            "secret": "",
                            "sandbox": True
                        }
                    },
                    "trading_pairs": [
                        "BTC/USDT", "ETH/USDT", "BNB/USDT",
                        "BTC/ETH", "BTC/BNB", "ETH/BNB"
                    ],
                    "base_currencies": ["USDT", "BTC", "ETH"],
                    "min_profit_threshold": 0.5,
                    "max_trade_amount": 100,
                    "scan_interval": 5,
                    "enable_trading": False
                }
                
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=4)
                
                logger.info(f"Created default config file: {config_file}")
                return default_config
                
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    async def fetch_market_data(self, exchange_name: str) -> Dict[str, TradingPair]:
        """Fetch market data for all configured trading pairs"""
        market_data = {}
        
        try:
            tasks = []
            for symbol in self.config['trading_pairs']:
                task = self.exchange_manager.get_ticker(exchange_name, symbol)
                tasks.append((symbol, task))
            
            results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            for (symbol, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    logger.warning(f"Error fetching {symbol}: {result}")
                    continue
                
                if result:
                    base, quote = symbol.split('/')
                    trading_pair = TradingPair(
                        symbol=symbol,
                        base=base,
                        quote=quote,
                        price=float(result['last']),
                        volume=float(result['baseVolume']),
                        bid=float(result['bid']),
                        ask=float(result['ask'])
                    )
                    market_data[symbol] = trading_pair
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data from {exchange_name}: {e}")
            return {}
    
    def find_triangular_opportunities(self, market_data: Dict[str, TradingPair], exchange_name: str) -> List[ArbitrageOpportunity]:
        """Find triangular arbitrage opportunities"""
        opportunities = []
        
        try:
            base_currencies = self.config['base_currencies']
            
            for base_currency in base_currencies:
                # Find all possible triangular paths
                triangular_paths = self.generate_triangular_paths(base_currency, market_data)
                
                for path in triangular_paths:
                    opportunity = self.calculate_arbitrage_profit(path, market_data, exchange_name)
                    if opportunity and opportunity.profit_percentage >= self.min_profit_threshold:
                        opportunities.append(opportunity)
            
            # Sort by profit percentage (descending)
            opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
            return opportunities
            
        except Exception as e:
            logger.error(f"Error finding triangular opportunities: {e}")
            return []
    
    def generate_triangular_paths(self, base_currency: str, market_data: Dict[str, TradingPair]) -> List[List[str]]:
        """Generate all possible triangular arbitrage paths"""
        paths = []
        
        try:
            # Get all currencies that can be traded with base currency
            available_currencies = set()
            base_pairs = {}
            
            for symbol, pair in market_data.items():
                if pair.base == base_currency:
                    available_currencies.add(pair.quote)
                    base_pairs[pair.quote] = symbol
                elif pair.quote == base_currency:
                    available_currencies.add(pair.base)
                    base_pairs[pair.base] = symbol
            
            # Generate triangular paths
            for currency_a in available_currencies:
                for currency_b in available_currencies:
                    if currency_a != currency_b:
                        # Check if currency_a and currency_b can be traded
                        pair_ab = f"{currency_a}/{currency_b}"
                        pair_ba = f"{currency_b}/{currency_a}"
                        
                        if pair_ab in market_data or pair_ba in market_data:
                            # We have a triangular path: base -> currency_a -> currency_b -> base
                            path = [base_currency, currency_a, currency_b, base_currency]
                            paths.append(path)
            
            return paths
            
        except Exception as e:
            logger.error(f"Error generating triangular paths: {e}")
            return []
    
    def calculate_arbitrage_profit(self, path: List[str], market_data: Dict[str, TradingPair], exchange_name: str) -> Optional[ArbitrageOpportunity]:
        """Calculate profit for a triangular arbitrage path"""
        try:
            if len(path) != 4 or path[0] != path[3]:
                return None
            
            base_currency = path[0]
            currency_a = path[1]
            currency_b = path[2]
            
            # Get trading pairs for the path
            pair1 = f"{base_currency}/{currency_a}"
            pair1_reverse = f"{currency_a}/{base_currency}"
            pair2 = f"{currency_a}/{currency_b}"
            pair2_reverse = f"{currency_b}/{currency_a}"
            pair3 = f"{currency_b}/{base_currency}"
            pair3_reverse = f"{base_currency}/{currency_b}"
            
            # Find actual pairs in market data
            step1_pair = None
            step1_price = 0
            step1_reverse = False
            
            if pair1 in market_data:
                step1_pair = market_data[pair1]
                step1_price = step1_pair.ask  # We're buying currency_a with base_currency
            elif pair1_reverse in market_data:
                step1_pair = market_data[pair1_reverse]
                step1_price = 1 / step1_pair.bid  # We're selling base_currency for currency_a
                step1_reverse = True
            
            step2_pair = None
            step2_price = 0
            step2_reverse = False
            
            if pair2 in market_data:
                step2_pair = market_data[pair2]
                step2_price = step2_pair.ask  # We're buying currency_b with currency_a
            elif pair2_reverse in market_data:
                step2_pair = market_data[pair2_reverse]
                step2_price = 1 / step2_pair.bid  # We're selling currency_a for currency_b
                step2_reverse = True
            
            step3_pair = None
            step3_price = 0
            step3_reverse = False
            
            if pair3 in market_data:
                step3_pair = market_data[pair3]
                step3_price = step3_pair.bid  # We're selling currency_b for base_currency
            elif pair3_reverse in market_data:
                step3_pair = market_data[pair3_reverse]
                step3_price = 1 / step3_pair.ask  # We're buying base_currency with currency_b
                step3_reverse = True
            
            if not all([step1_pair, step2_pair, step3_pair]):
                return None
            
            # Calculate final amount after all three trades
            initial_amount = 100  # Start with 100 units of base currency
            
            # Step 1: base_currency -> currency_a
            amount_after_step1 = initial_amount / step1_price if step1_reverse else initial_amount * step1_price
            
            # Step 2: currency_a -> currency_b
            amount_after_step2 = amount_after_step1 / step2_price if step2_reverse else amount_after_step1 * step2_price
            
            # Step 3: currency_b -> base_currency
            final_amount = amount_after_step2 * step3_price if not step3_reverse else amount_after_step2 / step3_price
            
            # Calculate profit
            profit_amount = final_amount - initial_amount
            profit_percentage = (profit_amount / initial_amount) * 100
            
            if profit_percentage > 0:
                return ArbitrageOpportunity(
                    base_currency=base_currency,
                    quote_currency=currency_a,
                    intermediate_currency=currency_b,
                    profit_percentage=profit_percentage,
                    profit_amount=profit_amount,
                    path=path,
                    prices={
                        f"step1_{step1_pair.symbol}": step1_price,
                        f"step2_{step2_pair.symbol}": step2_price,
                        f"step3_{step3_pair.symbol}": step3_price
                    },
                    volumes={
                        step1_pair.symbol: step1_pair.volume,
                        step2_pair.symbol: step2_pair.volume,
                        step3_pair.symbol: step3_pair.volume
                    },
                    exchange=exchange_name,
                    timestamp=datetime.now()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating arbitrage profit: {e}")
            return None
    
    async def execute_arbitrage(self, opportunity: ArbitrageOpportunity) -> bool:
        """Execute triangular arbitrage trade"""
        if not self.config.get('enable_trading', False):
            logger.info("Trading is disabled in config. Skipping execution.")
            return False
        
        try:
            logger.info(f"Executing arbitrage opportunity: {opportunity.path}")
            logger.info(f"Expected profit: {opportunity.profit_percentage:.4f}%")
            
            # This is where you would implement the actual trading logic
            # For safety, this is just a simulation
            
            # Step 1: Buy intermediate currency with base currency
            # Step 2: Buy quote currency with intermediate currency  
            # Step 3: Sell quote currency for base currency
            
            # Simulate execution delay
            await asyncio.sleep(1)
            
            logger.info("Arbitrage execution completed (simulated)")
            return True
            
        except Exception as e:
            logger.error(f"Error executing arbitrage: {e}")
            return False
    
    async def scan_opportunities(self):
        """Main scanning loop for arbitrage opportunities"""
        logger.info("Starting arbitrage opportunity scanning...")
        
        while self.running:
            try:
                # Scan each exchange
                for exchange_name in self.exchange_manager.exchanges.keys():
                    logger.info(f"Scanning {exchange_name} for opportunities...")
                    
                    # Fetch market data
                    market_data = await self.fetch_market_data(exchange_name)
                    
                    if not market_data:
                        logger.warning(f"No market data from {exchange_name}")
                        continue
                    
                    # Find opportunities
                    opportunities = self.find_triangular_opportunities(market_data, exchange_name)
                    
                    if opportunities:
                        logger.info(f"Found {len(opportunities)} opportunities on {exchange_name}")
                        
                        for opportunity in opportunities[:3]:  # Show top 3
                            logger.info(
                                f"Opportunity: {' -> '.join(opportunity.path)} | "
                                f"Profit: {opportunity.profit_percentage:.4f}% | "
                                f"Exchange: {opportunity.exchange}"
                            )
                            
                            # Execute if profitable enough
                            if opportunity.profit_percentage >= self.min_profit_threshold * 2:  # Double threshold for execution
                                await self.execute_arbitrage(opportunity)
                    
                    else:
                        logger.info(f"No profitable opportunities found on {exchange_name}")
                
                # Wait before next scan
                await asyncio.sleep(self.config.get('scan_interval', 5))
                
            except Exception as e:
                logger.error(f"Error in scanning loop: {e}")
                await asyncio.sleep(5)
    
    async def start(self):
        """Start the arbitrage bot"""
        self.running = True
        logger.info("Triangular Arbitrage Bot started")
        
        try:
            await self.scan_opportunities()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the arbitrage bot"""
        self.running = False
        await self.exchange_manager.close_all()
        logger.info("Triangular Arbitrage Bot stopped")

async def main():
    """Main function to run the bot"""
    bot = TriangularArbitrageBot()
    
    try:
        await bot.start()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
