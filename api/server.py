"""REST API server for Claude integration and external access"""

import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os

from ..execution import MarketScanner, OutputFormatter
from ..tracking import PerformanceTracker
from ..utils import ScanResult, logger
from ..config import config

# Pydantic models for API requests/responses
class ScanRequest(BaseModel):
    symbols: Optional[List[str]] = Field(None, description="Custom symbols to scan")
    timeframe: str = Field("1h", description="Analysis timeframe")
    min_score: Optional[int] = Field(None, description="Minimum score threshold")
    max_results: Optional[int] = Field(3, description="Maximum results to return")

class ScanResponse(BaseModel):
    scan_id: str
    timestamp: datetime
    btc_benchmark: float
    total_symbols_analyzed: int
    candidates: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class QuickAnalysisRequest(BaseModel):
    symbols: List[str] = Field(..., description="Symbols to analyze")
    timeframe: str = Field("1h", description="Analysis timeframe")

class PerformanceRequest(BaseModel):
    days: int = Field(30, description="Number of days to analyze")

class UniverseRequest(BaseModel):
    action: str = Field(..., description="add, remove, or list")
    symbols: Optional[List[str]] = Field(None, description="Symbols for add/remove")

class ExecutionRequest(BaseModel):
    """For future execution integration"""
    symbol: str
    action: str  # "buy", "sell"
    quantity: float
    order_type: str = "market"
    venue: str = "paper"  # Start with paper trading

# Security
security = HTTPBearer(auto_error=False)

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple API key authentication"""
    if not credentials:
        return None  # Allow unauthenticated access for now
    
    expected_key = os.getenv("MARKET_SCANNER_API_KEY")
    if expected_key and credentials.credentials != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return credentials.credentials

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Market Scanner API",
        description="Autonomous Market Scanner - Find symbols guaranteed to outperform BTC",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware for web frontends
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Global instances
    scanner = MarketScanner()
    formatter = OutputFormatter()
    tracker = PerformanceTracker() if config.TRACK_PERFORMANCE else None
    
    @app.get("/", tags=["Health"])
    async def root():
        """Health check endpoint"""
        return {
            "service": "Market Scanner API",
            "status": "operational",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
    
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Detailed health check with component validation"""
        validation = await scanner.validate_setup()
        
        return {
            "status": "healthy" if all(validation.values()) else "degraded",
            "components": validation,
            "timestamp": datetime.now().isoformat()
        }
    
    @app.post("/scan", response_model=ScanResponse, tags=["Analysis"])
    async def run_scan(
        request: ScanRequest,
        background_tasks: BackgroundTasks,
        api_key: Optional[str] = Depends(verify_api_key)
    ):
        """🎯 Run a complete market scan - main endpoint for Claude"""
        try:
            # Override config if specified
            if request.min_score:
                original_threshold = config.MIN_SCORE_THRESHOLD
                config.MIN_SCORE_THRESHOLD = request.min_score
            
            # Run the scan
            results = await scanner.run_scan(
                timeframe=request.timeframe,
                custom_symbols=request.symbols
            )
            
            # Restore original config
            if request.min_score:
                config.MIN_SCORE_THRESHOLD = original_threshold
            
            # Limit results
            if request.max_results:
                results = results[:request.max_results]
            
            # Get BTC benchmark
            btc_return = await scanner.composer_scorer.btc_benchmark.get_expected_return(request.timeframe)
            
            # Convert results to API format
            candidates = []
            for result in results:
                candidate = {
                    "rank": result.rank,
                    "symbol": result.symbol,
                    "score": round(result.score, 1),
                    "current_price": round(result.current_price, 2),
                    "vwap": round(result.vwap, 2),
                    "target_strike": round(result.target_strike, 2) if result.target_strike else None,
                    "probability_reach": round(result.probability_reach, 3),
                    "expected_return": round(result.expected_return, 3),
                    "timeframe": result.timeframe,
                    "entry_zone": {
                        "low": round(result.entry_zone[0], 2),
                        "high": round(result.entry_zone[1], 2)
                    },
                    "stop_loss": round(result.stop_loss, 2),
                    "squeeze_factors": result.squeeze_factors,
                    "reasoning": result.reasoning
                }
                candidates.append(candidate)
            
            # Generate scan ID
            scan_id = f"scan_{int(datetime.now().timestamp())}"
            
            # Background task: log to tracker
            if tracker:
                background_tasks.add_task(
                    log_scan_to_tracker,
                    tracker, results, len(request.symbols) if request.symbols else 50,
                    btc_return, request.timeframe
                )
            
            return ScanResponse(
                scan_id=scan_id,
                timestamp=datetime.now(),
                btc_benchmark=btc_return,
                total_symbols_analyzed=len(request.symbols) if request.symbols else len(scanner.data_manager.universe.get_active_symbols()),
                candidates=candidates,
                metadata={
                    "timeframe": request.timeframe,
                    "min_score_used": request.min_score or config.MIN_SCORE_THRESHOLD,
                    "api_version": "1.0.0"
                }
            )
            
        except Exception as e:
            logger.error(f"Error in scan endpoint: {e}")
            raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
    
    @app.post("/quick-analysis", tags=["Analysis"])
    async def quick_analysis(
        request: QuickAnalysisRequest,
        api_key: Optional[str] = Depends(verify_api_key)
    ):
        """⚡ Quick analysis of specific symbols"""
        try:
            results = await scanner.quick_scan(request.symbols)
            
            if not results:
                return {
                    "message": "No opportunities found in specified symbols",
                    "symbols_analyzed": request.symbols,
                    "candidates": []
                }
            
            candidates = []
            for result in results:
                candidates.append({
                    "rank": result.rank,
                    "symbol": result.symbol,
                    "score": round(result.score, 1),
                    "current_price": round(result.current_price, 2),
                    "expected_return": round(result.expected_return, 3),
                    "probability": round(result.probability_reach, 3),
                    "timeframe": result.timeframe,
                    "reasoning": result.reasoning
                })
            
            return {
                "symbols_analyzed": request.symbols,
                "candidates": candidates,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in quick analysis: {e}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    @app.get("/performance", tags=["Analytics"])
    async def get_performance(
        days: int = 30,
        api_key: Optional[str] = Depends(verify_api_key)
    ):
        """📊 Get performance statistics"""
        if not tracker:
            raise HTTPException(status_code=503, detail="Performance tracking not enabled")
        
        try:
            stats = tracker.get_performance_stats(days)
            effectiveness = tracker.get_signal_effectiveness()
            recent_scans = tracker.get_recent_scans(10)
            
            return {
                "period_days": days,
                "overall_performance": stats,
                "signal_effectiveness": effectiveness,
                "recent_scans": recent_scans,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance: {e}")
            raise HTTPException(status_code=500, detail=f"Performance query failed: {str(e)}")
    
    @app.post("/universe", tags=["Configuration"])
    async def manage_universe(
        request: UniverseRequest,
        api_key: Optional[str] = Depends(verify_api_key)
    ):
        """🌌 Manage symbol universe"""
        try:
            universe_manager = scanner.data_manager.universe
            
            if request.action == "list":
                symbols = universe_manager.get_active_symbols()
                return {
                    "action": "list",
                    "universe_size": len(symbols),
                    "symbols": symbols
                }
            
            elif request.action == "add" and request.symbols:
                for symbol in request.symbols:
                    universe_manager.add_symbol(symbol.upper())
                return {
                    "action": "add",
                    "symbols_added": [s.upper() for s in request.symbols],
                    "message": f"Added {len(request.symbols)} symbols to universe"
                }
            
            elif request.action == "remove" and request.symbols:
                for symbol in request.symbols:
                    universe_manager.remove_symbol(symbol.upper())
                return {
                    "action": "remove", 
                    "symbols_removed": [s.upper() for s in request.symbols],
                    "message": f"Removed {len(request.symbols)} symbols from universe"
                }
            
            else:
                raise HTTPException(status_code=400, detail="Invalid action or missing symbols")
                
        except Exception as e:
            logger.error(f"Error managing universe: {e}")
            raise HTTPException(status_code=500, detail=f"Universe operation failed: {str(e)}")
    
    @app.get("/btc-benchmark", tags=["Analysis"])
    async def get_btc_benchmark(
        timeframe: str = "1h",
        api_key: Optional[str] = Depends(verify_api_key)
    ):
        """📈 Get current Bitcoin benchmark for comparison"""
        try:
            btc_return = await scanner.composer_scorer.btc_benchmark.get_expected_return(timeframe)
            
            return {
                "timeframe": timeframe,
                "btc_expected_return": btc_return,
                "btc_expected_return_pct": f"{btc_return:.2%}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting BTC benchmark: {e}")
            raise HTTPException(status_code=500, detail=f"BTC benchmark failed: {str(e)}")
    
    @app.get("/market-data/{symbol}", tags=["Data"])
    async def get_market_data(
        symbol: str,
        api_key: Optional[str] = Depends(verify_api_key)
    ):
        """📊 Get current market data for a symbol"""
        try:
            data = await scanner.data_manager.get_market_data(symbol.upper())
            
            if not data:
                raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
            
            return {
                "symbol": data.symbol,
                "price": data.price,
                "volume": data.volume,
                "vwap": data.vwap,
                "high": data.high,
                "low": data.low,
                "open": data.open,
                "timestamp": data.timestamp.isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=f"Market data query failed: {str(e)}")
    
    # Future execution endpoints (placeholder)
    @app.post("/execute", tags=["Execution"])
    async def execute_trade(
        request: ExecutionRequest,
        api_key: Optional[str] = Depends(verify_api_key)
    ):
        """🚨 Execute trade (PAPER TRADING ONLY for now)"""
        # This is a placeholder for future execution integration
        return {
            "status": "paper_trade_simulated",
            "message": "Execution capabilities coming soon - integrate with Alpaca/IBKR/Schwab",
            "request": request.dict(),
            "timestamp": datetime.now().isoformat()
        }
    
    return app

async def log_scan_to_tracker(tracker, results, total_symbols, btc_return, timeframe):
    """Background task to log scan results"""
    try:
        tracker.log_scan(results, total_symbols, btc_return, timeframe)
    except Exception as e:
        logger.error(f"Error logging scan to tracker: {e}")

def run_server(host: str = "127.0.0.1", port: int = 8888, reload: bool = False):
    """Run the API server"""
    app = create_app()
    
    print(f"🚀 Starting Market Scanner API on http://{host}:{port}")
    print(f"📖 API Documentation: http://{host}:{port}/docs")
    print(f"🔧 Health Check: http://{host}:{port}/health")
    
    uvicorn.run(
        "market_scanner.api.server:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    run_server(reload=True)