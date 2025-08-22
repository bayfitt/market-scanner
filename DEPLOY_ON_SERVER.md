# 🚀 Server Deployment Script for Claude

## Quick Deploy (Copy-Paste All)

```bash
#!/bin/bash
set -e

echo "🚀 Deploying Market Scanner on Server..."

# 1. Setup environment
cd /root || cd /home/$(whoami)
mkdir -p market-scanner-deploy
cd market-scanner-deploy

# 2. Clone repository
echo "📥 Cloning repository..."
git clone https://github.com/bayfitt/market-scanner.git
cd market-scanner

# 3. Install dependencies
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Test basic functionality
echo "🧪 Testing basic functionality..."
python3 -c "
import sys
sys.path.insert(0, '.')
from market_scanner.utils import MarketData
from market_scanner.execution import MarketScanner
print('✅ Core imports successful')
"

# 5. Test CLI
echo "🔧 Testing CLI..."
python3 -m market_scanner.cli version
python3 -m market_scanner.cli validate

# 6. Quick functionality test
echo "⚡ Testing quick scan..."
python3 -m market_scanner.cli quick AAPL TSLA NVDA || echo "⚠️ Quick scan failed - continuing..."

# 7. Start API server
echo "🌐 Starting API server..."
nohup python3 -m market_scanner.cli api --host 0.0.0.0 --port 8888 > scanner.log 2>&1 &
API_PID=$!

# 8. Wait for startup
sleep 5

# 9. Test API
echo "📡 Testing API endpoints..."
curl -s http://localhost:8888/health || echo "⚠️ Health check failed"
curl -s http://localhost:8888/ || echo "⚠️ Root endpoint failed"

# 10. Test scan endpoint
echo "🎯 Testing scan endpoint..."
curl -s -X POST http://localhost:8888/quick-analysis \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "TSLA"]}' || echo "⚠️ Quick analysis failed"

echo ""
echo "✅ Deployment complete!"
echo "📊 API running on: http://$(hostname -I | awk '{print $1}'):8888"
echo "📋 Health check: curl http://$(hostname -I | awk '{print $1}'):8888/health"
echo "📖 API docs: http://$(hostname -I | awk '{print $1}'):8888/docs"
echo "📝 Logs: tail -f scanner.log"
echo "🔍 Process: ps aux | grep market_scanner"
echo ""
echo "🤖 Ready for Claude integration!"
```

## Individual Commands (If Issues)

### Environment Setup
```bash
cd /root
mkdir -p market-scanner-deploy
cd market-scanner-deploy
```

### Clone & Install
```bash
git clone https://github.com/bayfitt/market-scanner.git
cd market-scanner
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Test Core Functionality
```bash
# Test imports
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from market_scanner.utils import MarketData
    from market_scanner.execution import MarketScanner
    print('✅ Core imports successful')
except ImportError as e:
    print(f'❌ Import failed: {e}')
"

# Test CLI
python3 -m market_scanner.cli --help
python3 -m market_scanner.cli version
python3 -m market_scanner.cli validate
```

### Test Market Data
```bash
# Test with real symbols
python3 -c "
import sys
sys.path.insert(0, '.')
import asyncio
from market_scanner.execution import MarketScanner

async def test():
    scanner = MarketScanner()
    results = await scanner.quick_scan(['AAPL'])
    print(f'✅ Scan test: {len(results)} results')

asyncio.run(test())
"
```

### Start API Server
```bash
# Start in background
nohup python3 -m market_scanner.cli api --host 0.0.0.0 --port 8888 > scanner.log 2>&1 &

# Check if running
ps aux | grep market_scanner
tail -f scanner.log
```

### Test API Endpoints
```bash
# Health check
curl -s http://localhost:8888/health | python3 -m json.tool

# Quick analysis
curl -s -X POST http://localhost:8888/quick-analysis \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "TSLA"]}' | python3 -m json.tool

# Full scan
curl -s -X POST http://localhost:8888/scan \
  -H "Content-Type: application/json" \
  -d '{"timeframe": "1h", "max_results": 3}' | python3 -m json.tool
```

## Troubleshooting

### If Dependencies Fail
```bash
# Manual install of core packages
pip install pandas numpy requests yfinance python-dateutil scipy
pip install fastapi uvicorn click rich python-dotenv aiohttp websockets pydantic
```

### If Import Errors
```bash
# Check Python path
python3 -c "import sys; print('\\n'.join(sys.path))"

# Add current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### If API Fails to Start
```bash
# Check what's using port 8888
netstat -tulpn | grep 8888
lsof -i :8888

# Try different port
python3 -m market_scanner.cli api --host 0.0.0.0 --port 9999
```

### If Network Issues
```bash
# Test internet connectivity
curl -s https://query1.finance.yahoo.com/v8/finance/chart/AAPL | head -100

# Test DNS
nslookup query1.finance.yahoo.com
```

## Success Indicators

✅ **All Good When:**
- `curl http://localhost:8888/health` returns `{"status": "healthy"}`
- `POST /scan` returns symbol candidates
- Logs show no errors: `tail scanner.log`
- Process is running: `ps aux | grep market_scanner`

## Access Points

Once deployed:
- **API Base**: `http://SERVER_IP:8888`
- **Health**: `http://SERVER_IP:8888/health`
- **Docs**: `http://SERVER_IP:8888/docs`
- **Logs**: `tail -f ~/market-scanner-deploy/market-scanner/scanner.log`

Ready to rock! 🚀