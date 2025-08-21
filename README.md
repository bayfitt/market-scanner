# 🚀 Market Scanner

**Autonomous Market Scanner** - Find symbols guaranteed to outperform Bitcoin using advanced technical analysis, options flow, and squeeze detection.

## 🆓 100% FREE to Use

This scanner uses **ONLY FREE APIs** - no paid subscriptions required:

- **Yahoo Finance**: Primary data source (FREE, unlimited)
- **Alpha Vantage**: Backup source (FREE - 500 requests/day)  
- **Financial Modeling Prep**: Backup source (FREE - 250 requests/day)

### Optional Free API Keys (Recommended for Better Performance)

1. **Alpha Vantage** (FREE): Get your key at https://www.alphavantage.co/support/#api-key
   ```bash
   export ALPHA_VANTAGE_KEY="your_free_key_here"
   ```

2. **Financial Modeling Prep** (FREE): Get your key at https://financialmodelingprep.com/developer/docs
   ```bash
   export FMP_KEY="your_free_key_here"
   ```

**Note**: The scanner works perfectly without any API keys using Yahoo Finance as the primary data source.

## ⚡ Quick Start (One Command)

```bash
# Download and run the scanner
./market-scanner scan
```

## 🎯 What It Does

The scanner analyzes thousands of stocks in real-time and finds the **top 3 candidates** most likely to outperform Bitcoin based on:

1. **🔥 Ignition Signals**: VWAP momentum, band expansion, timing
2. **🎯 Options Pressure**: Gamma walls, dealer positioning, put/call ratios  
3. **⛽ Squeeze Fuel**: Float size, short interest, volume surges
4. **📊 BTC Benchmark**: Only returns symbols with higher expected returns than Bitcoin

## 🖥️ Usage

### One-Button Scan
```bash
market-scanner scan
```

### Quick Analysis of Specific Symbols
```bash
market-scanner quick TSLA NVDA PLTR
```

### Continuous Monitoring
```bash
market-scanner watch --interval 5
```

### Performance Tracking
```bash
market-scanner stats --days 30
```

## 📋 Sample Output

```
🚀 Market Scanner Results
┌──────┬────────┬───────┬──────────┬──────────┬──────────┬────────┬──────────────┐
│ Rank │ Symbol │ Score │ Price    │ Target   │ Return   │ Prob   │ Timeframe    │
├──────┼────────┼───────┼──────────┼──────────┼──────────┼────────┼──────────────┤
│ 1    │ TUYA   │ 87    │ $2.15    │ $2.50    │ 16.3%    │ 68%    │ 2-4 hours    │
│ 2    │ SOFI   │ 82    │ $8.45    │ $9.50    │ 12.4%    │ 72%    │ 1-2 hours    │  
│ 3    │ PLTR   │ 78    │ $23.10   │ $25.00   │ 8.2%     │ 65%    │ 4+ hours     │
└──────┴────────┴───────┴──────────┴──────────┴──────────┴────────┴──────────────┘
```

## 🛠️ Installation Options

### Option 1: Download Binary (Easiest)
```bash
# Download the pre-built macOS binary
curl -L -o market-scanner https://github.com/your-repo/releases/latest/download/market-scanner-macos
chmod +x market-scanner
./market-scanner scan
```

### Option 2: Install from Source
```bash
git clone https://github.com/your-repo/market-scanner
cd market-scanner
pip install -r requirements.txt
python -m market_scanner.cli scan
```

## ⚙️ Configuration

### Basic Setup (No Configuration Needed)
The scanner works out-of-the-box with default settings.

### Advanced Configuration
Create a `.env` file or set environment variables:

```bash
# Optional free API keys for better performance
export ALPHA_VANTAGE_KEY="your_free_key"
export FMP_KEY="your_free_key"

# Scanner settings
export MIN_SCORE_THRESHOLD=70
export MIN_PROBABILITY_THRESHOLD=0.65
export MAX_SYMBOLS_PER_SCAN=3
```

### Custom Symbol Universe
```bash
# Add symbols to scan universe
market-scanner universe --add TSLA
market-scanner universe --add NVDA,AMD,PLTR

# Load symbols from CSV
market-scanner universe --load my-watchlist.csv

# View current universe
market-scanner universe --list
```

## 🧠 How It Works

### Signal Processing Pipeline

1. **Data Ingestion**: Real-time market data from free APIs
2. **Technical Analysis**: VWAP momentum, Bollinger Bands, volume analysis
3. **Options Flow**: Gamma wall detection, dealer positioning analysis
4. **Squeeze Detection**: Float analysis, short interest, borrow costs
5. **Composite Scoring**: Weighted algorithm combining all signals
6. **BTC Benchmarking**: Filter out symbols that won't beat Bitcoin
7. **Ranking**: Return top 3 highest-probability opportunities

### Key Algorithms

- **Ignition Engine**: Detects momentum breakouts and optimal entry timing
- **Pressure Engine**: Analyzes options flow for directional bias and targets  
- **Fuel Engine**: Quantifies short squeeze potential and volume factors
- **Composite Scorer**: Combines signals with probability weighting
- **BTC Benchmark**: Ensures expected returns exceed Bitcoin's expected return

## 📊 Performance Tracking

The scanner automatically tracks performance and learns from outcomes:

```bash
# View performance stats
market-scanner stats

# Export detailed report
market-scanner stats --export report.json --days 30
```

## 🚨 Risk Disclaimer

This tool is for **educational and research purposes only**. 

- Past performance does not guarantee future results
- All trading involves substantial risk of loss
- Do your own research and risk management
- Never risk more than you can afford to lose
- The scanner provides analysis, not financial advice

## 🔧 Troubleshooting

### Common Issues

**"No candidates found"**
- Market conditions may not favor any symbols
- Try adjusting thresholds: `--min-score 60` 
- Check with specific symbols: `market-scanner quick TSLA NVDA`

**"API limit reached"**
- Yahoo Finance (primary) has no limits
- Get free API keys for Alpha Vantage and FMP for better redundancy
- Wait for API limits to reset (daily)

**"Redis connection failed"**
- Install Redis: `brew install redis`
- Start Redis: `brew services start redis`
- Or disable caching by setting `REDIS_URL=""`

### Validation
```bash
# Test all components
market-scanner validate
```

## 🏗️ Development

### Building from Source
```bash
git clone https://github.com/your-repo/market-scanner
cd market-scanner
pip install -r requirements-build.txt
python setup.py install
```

### Creating Binary
```bash
# Build macOS binary
python scripts/build_binary.py
```

## 📄 License

MIT License - free for personal and commercial use.

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## 📞 Support

- Issues: https://github.com/your-repo/market-scanner/issues
- Documentation: https://github.com/your-repo/market-scanner/wiki

---

**Built with ❤️ for traders who want to consistently outperform Bitcoin** 🚀