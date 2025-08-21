# 🤖 Claude Integration Guide

## Market Scanner API for Claude Code

The Market Scanner provides a **REST API** that Claude can call using the `mcp__http` tools or standard HTTP requests. This enables Claude to autonomously find trading opportunities and analyze markets.

## 🚀 Quick Start for Claude

### 1. Start the API Server
```bash
# Terminal 1: Start the API server
market-scanner api

# Or specify custom host/port
market-scanner api --host 0.0.0.0 --port 8888
```

### 2. API Endpoints for Claude

**Base URL**: `http://127.0.0.1:8888`

#### 🎯 Main Scan Endpoint
```http
POST /scan
Content-Type: application/json

{
  "symbols": ["TSLA", "NVDA", "PLTR"],  // Optional: custom symbols
  "timeframe": "1h",                    // "1h", "2h", "4h", "1d"  
  "min_score": 70,                      // Optional: minimum score
  "max_results": 3                      // Max candidates to return
}
```

**Response**: Returns top candidates guaranteed to outperform BTC
```json
{
  "scan_id": "scan_1703123456",
  "timestamp": "2024-01-15T14:30:00Z",
  "btc_benchmark": 0.025,
  "candidates": [
    {
      "rank": 1,
      "symbol": "TUYA", 
      "score": 87.0,
      "current_price": 2.15,
      "target_strike": 2.50,
      "expected_return": 0.163,
      "probability_reach": 0.68,
      "timeframe": "2-4 hours",
      "reasoning": "Strong squeeze setup with gamma wall at $2.50"
    }
  ]
}
```

#### ⚡ Quick Analysis
```http
POST /quick-analysis
Content-Type: application/json

{
  "symbols": ["TSLA", "NVDA"],
  "timeframe": "1h"
}
```

#### 📊 Performance Stats
```http
GET /performance?days=30
```

#### 🌌 Manage Symbol Universe
```http
POST /universe
Content-Type: application/json

{
  "action": "add",
  "symbols": ["TSLA", "NVDA"]
}
```

#### 📈 Bitcoin Benchmark
```http
GET /btc-benchmark?timeframe=1h
```

#### 📊 Market Data
```http
GET /market-data/TSLA
```

### 3. Example Claude Tool Calls

#### Using HTTPie (built into Claude Code)
```python
# Claude can make these calls:
http POST localhost:8888/scan symbols:='["TSLA","NVDA","PLTR"]' timeframe=1h

# Quick analysis
http POST localhost:8888/quick-analysis symbols:='["TSLA"]'

# Get performance stats
http GET localhost:8888/performance days==30
```

#### Using WebFetch tool
```python
# Claude can use WebFetch for GET requests
WebFetch(
    url="http://127.0.0.1:8888/btc-benchmark?timeframe=1h",
    prompt="Get the current Bitcoin benchmark for comparison"
)
```

## 🔧 Authentication (Optional)

Set API key for production use:
```bash
export MARKET_SCANNER_API_KEY="your_secret_key"
```

Then include in requests:
```http
Authorization: Bearer your_secret_key
```

## 🎯 Claude Workflow Examples

### 1. Find Trading Opportunities
```python
# 1. Run market scan
scan_result = http POST localhost:8888/scan timeframe=1h

# 2. Analyze top candidate
if scan_result.candidates:
    symbol = scan_result.candidates[0].symbol
    detail = http GET localhost:8888/market-data/{symbol}
    
# 3. Get BTC comparison
btc_bench = http GET localhost:8888/btc-benchmark timeframe=1h
```

### 2. Monitor Performance
```python
# Get recent performance
stats = http GET localhost:8888/performance days==7

# Check if strategy is working
if stats.overall_performance.win_rate > 0.6:
    print("Strategy performing well!")
```

### 3. Custom Symbol Analysis
```python
# Analyze specific symbols Claude is tracking
symbols_to_check = ["TSLA", "NVDA", "PLTR", "SOFI"]

analysis = http POST localhost:8888/quick-analysis symbols:=symbols_to_check timeframe=2h

for candidate in analysis.candidates:
    if candidate.score > 80:
        print(f"Strong signal: {candidate.symbol} - Score: {candidate.score}")
```

## 🚨 Error Handling

The API returns standard HTTP status codes:

- **200**: Success
- **400**: Bad request (invalid parameters)
- **404**: Resource not found
- **500**: Internal server error
- **503**: Service unavailable (components not ready)

Example error response:
```json
{
  "detail": "Scan failed: All FREE APIs failed for INVALID_SYMBOL"
}
```

## 📖 API Documentation

When the server is running, visit:
- **Swagger UI**: `http://127.0.0.1:8888/docs`
- **ReDoc**: `http://127.0.0.1:8888/redoc`

## 🔮 Future Execution Integration

The API includes placeholder endpoints for trade execution:

```http
POST /execute
Content-Type: application/json

{
  "symbol": "TSLA",
  "action": "buy", 
  "quantity": 100,
  "order_type": "market",
  "venue": "paper"
}
```

**Planned Integrations**:
- ✅ Paper Trading (built-in simulator)
- 🔄 Alpaca (paper and live)
- 🔄 Interactive Brokers TWS API
- 🔄 Charles Schwab Trader API
- 🔄 Coinbase Advanced Trade (crypto)

## 🛡️ Rate Limits & Performance

- **Yahoo Finance**: Unlimited (primary data source)
- **Alpha Vantage**: 500 requests/day (free tier)
- **Financial Modeling Prep**: 250 requests/day (free tier)
- **API Server**: No built-in rate limits (add nginx/CloudFlare if needed)

## 🎭 Claude Integration Patterns

### Pattern 1: Autonomous Scanning
```python
# Claude runs this every hour
def autonomous_scan():
    results = http POST localhost:8888/scan timeframe=1h
    
    for candidate in results.candidates[:2]:  # Top 2
        if candidate.score > 85:
            notify_user(f"🚀 High-confidence signal: {candidate.symbol}")
            
    return results
```

### Pattern 2: Event-Driven Analysis  
```python
# Claude monitors news/events and scans relevant symbols
def analyze_earnings_symbols(earnings_symbols):
    analysis = http POST localhost:8888/quick-analysis symbols:=earnings_symbols
    
    high_potential = [c for c in analysis.candidates if c.score > 75]
    return high_potential
```

### Pattern 3: Performance Monitoring
```python
# Claude tracks and reports on strategy performance
def weekly_performance_report():
    stats = http GET localhost:8888/performance days==7
    
    if stats.overall_performance.total_trades > 5:
        win_rate = stats.overall_performance.win_rate
        avg_return = stats.overall_performance.avg_return
        
        return f"📊 Week Summary: {win_rate:.1%} win rate, {avg_return:.2%} avg return"
```

## 🔍 Health Monitoring

Claude can monitor the scanner's health:

```http
GET /health
```

Returns component status:
```json
{
  "status": "healthy",
  "components": {
    "redis_connection": true,
    "data_feed": true, 
    "btc_benchmark": true,
    "symbol_universe": true
  }
}
```

## 🚀 Getting Started Script

Here's a complete Claude script to get started:

```python
# 1. Check if API is running
try:
    health = http GET localhost:8888/health
    print(f"✅ Scanner status: {health.status}")
except:
    print("❌ Start the API first: market-scanner api")
    exit()

# 2. Run a scan
print("🔍 Running market scan...")
results = http POST localhost:8888/scan timeframe=1h max_results==3

# 3. Display results
if results.candidates:
    print(f"🎯 Found {len(results.candidates)} candidates:")
    for c in results.candidates:
        print(f"  {c.rank}. {c.symbol} - Score: {c.score} - Expected: {c.expected_return:.1%}")
else:
    print("📭 No opportunities found")

# 4. Get BTC benchmark for context
btc = http GET localhost:8888/btc-benchmark timeframe=1h
print(f"📊 BTC benchmark: {btc.btc_expected_return:.2%}")
```

**Save this as a Claude Code tool and run it regularly for autonomous market monitoring!** 🤖📈