# Triangular Arbitrage Bot

A sophisticated Python-based triangular arbitrage bot for cryptocurrency trading across multiple exchanges, with primary support for Binance and extensible architecture for other exchanges.

## 🚀 Features

- **Multi-Exchange Support**: Binance, KuCoin, and easily extensible to other exchanges
- **Real-time Opportunity Detection**: Continuously scans for profitable triangular arbitrage opportunities
- **Risk Management**: Built-in position sizing, daily limits, and cooldown periods
- **Performance Tracking**: Comprehensive profit tracking and analytics
- **Safety First**: Sandbox mode by default, extensive error handling
- **Notifications**: Webhook alerts for profitable opportunities
- **Dashboard Monitoring**: Real-time monitoring interface
- **Configurable**: Highly customizable through JSON configuration

## 📋 Requirements

- Python 3.8+
- API keys for supported exchanges (optional for monitoring mode)
- Internet connection for real-time data

## 🛠️ Installation

1. **Clone or download the files to your directory**

2. **Install dependencies:**
```bash
pip install -r arbitrage_requirements.txt
```

3. **Configure your settings:**
   - Edit `arbitrage_config.json` with your exchange API credentials
   - Set your risk parameters and trading preferences
   - Configure notification settings

## ⚙️ Configuration

### Exchange Setup

Edit `arbitrage_config.json`:

```json
{
    "exchanges": {
        "binance": {
            "api_key": "your_binance_api_key",
            "secret": "your_binance_secret",
            "sandbox": true
        },
        "kucoin": {
            "api_key": "your_kucoin_api_key",
            "secret": "your_kucoin_secret", 
            "passphrase": "your_kucoin_passphrase",
            "sandbox": true
        }
    }
}
```

### Key Settings

- `min_profit_threshold`: Minimum profit percentage to consider (default: 0.5%)
- `max_trade_amount`: Maximum amount per trade in USDT (default: 100)
- `scan_interval`: Seconds between opportunity scans (default: 5)
- `enable_trading`: Set to `true` to enable actual trading (default: false)

### Risk Management

```json
"risk_management": {
    "max_position_size": 1000,
    "stop_loss_percentage": 2.0,
    "max_daily_trades": 50,
    "cooldown_period": 60
}
```

## 🚀 Usage

### 1. Basic Monitoring (Safe Mode)

```bash
python triangular_arbitrage_bot.py
```

This runs in monitoring mode only - no actual trades are executed.

### 2. Dashboard Interface

```bash
python arbitrage_dashboard.py
```

Choose option 1 for full dashboard or option 2 for simple monitoring.

### 3. Enable Live Trading

⚠️ **WARNING**: Only enable live trading after thorough testing!

1. Set `"enable_trading": true` in config
2. Set `"sandbox": false` for live trading
3. Ensure you have sufficient funds and proper API permissions

## 📊 How Triangular Arbitrage Works

Triangular arbitrage exploits price differences between three currencies on the same exchange:

```
Example Path: USDT → BTC → ETH → USDT

1. Buy BTC with USDT
2. Buy ETH with BTC  
3. Sell ETH for USDT

If the final USDT amount > initial USDT amount = Profit!
```

### Profit Calculation

The bot calculates profit by:
1. Finding all possible triangular paths
2. Computing the final amount after all three trades
3. Accounting for trading fees
4. Filtering opportunities above the minimum threshold

## 📁 File Structure

```
├── triangular_arbitrage_bot.py    # Main bot logic
├── arbitrage_utils.py             # Utility functions
├── arbitrage_dashboard.py         # Monitoring dashboard
├── arbitrage_config.json          # Configuration file
├── arbitrage_requirements.txt     # Python dependencies
└── README_ARBITRAGE.md           # This file
```

## 🔧 Advanced Features

### Custom Exchange Integration

To add a new exchange:

1. Add exchange config to `arbitrage_config.json`
2. Update `ExchangeManager.initialize_exchanges()`
3. Ensure the exchange is supported by ccxt library

### Notification Webhooks

Configure webhook notifications:

```json
"notifications": {
    "enable_alerts": true,
    "min_profit_for_alert": 1.0,
    "webhook_url": "https://your-webhook-url.com"
}
```

### Performance Analytics

The bot tracks:
- Daily/weekly profit summaries
- Trade success rates
- Average profit per trade
- Market volatility analysis

## ⚠️ Important Safety Notes

1. **Start with Sandbox Mode**: Always test with sandbox/testnet first
2. **Small Amounts**: Start with very small trade amounts
3. **Monitor Closely**: Watch the bot's performance carefully
4. **API Permissions**: Use trading-only API keys (no withdrawal permissions)
5. **Network Latency**: Arbitrage opportunities are time-sensitive
6. **Market Conditions**: Works best in stable market conditions

## 🐛 Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Check API keys and permissions
   - Verify network connectivity
   - Ensure exchange APIs are accessible

2. **No Opportunities Found**
   - Lower the `min_profit_threshold`
   - Check if trading pairs are active
   - Verify market conditions

3. **Trade Execution Failures**
   - Check account balances
   - Verify API trading permissions
   - Review exchange-specific requirements

### Logging

Check `arbitrage_bot.log` for detailed error information and bot activity.

## 📈 Performance Optimization

1. **Reduce Scan Interval**: For faster opportunity detection (increases API usage)
2. **Optimize Trading Pairs**: Focus on high-volume, liquid pairs
3. **Network Optimization**: Use VPS close to exchange servers
4. **Fee Optimization**: Consider exchange fee structures

## 🔒 Security Best Practices

1. **API Key Security**:
   - Never share API keys
   - Use IP restrictions
   - Regular key rotation

2. **Environment Variables**:
   ```bash
   export BINANCE_API_KEY="your_key"
   export BINANCE_SECRET="your_secret"
   ```

3. **Code Security**:
   - Keep dependencies updated
   - Regular security audits
   - Monitor for unusual activity

## 📚 Additional Resources

- [CCXT Documentation](https://github.com/ccxt/ccxt)
- [Binance API Documentation](https://binance-docs.github.io/apidocs/)
- [KuCoin API Documentation](https://docs.kucoin.com/)

## ⚖️ Legal Disclaimer

This software is for educational purposes only. Cryptocurrency trading involves substantial risk of loss. The authors are not responsible for any financial losses. Always comply with local regulations and exchange terms of service.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions or issues:
1. Check the troubleshooting section
2. Review the logs for error details
3. Ensure configuration is correct
4. Test with sandbox mode first

---

**Happy Trading! 🚀**

Remember: Only invest what you can afford to lose, and always test thoroughly before live trading.
