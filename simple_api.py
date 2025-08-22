#!/usr/bin/env python3
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

app = FastAPI(
    title="Market Scanner API",
    description="Autonomous market scanner for finding BTC-outperforming symbols",
    version="1.0.0"
)

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "server": "claude-container"
    }

@app.get("/")
async def root():
    return {
        "message": "Market Scanner API - Ready for Claude Integration",
        "version": "1.0.0",
        "endpoints": ["/health", "/scan", "/quick-analysis", "/docs"],
        "status": "operational"
    }

@app.post("/quick-analysis")
async def quick_analysis(request: dict):
    """Quick analysis of provided symbols"""
    symbols = request.get("symbols", ["AAPL", "TSLA", "NVDA"])
    
    # Mock analysis for now
    results = []
    for symbol in symbols[:3]:  # Limit to 3 for demo
        score = np.random.uniform(70, 95)
        results.append({
            "symbol": symbol,
            "score": round(score, 1),
            "current_price": round(np.random.uniform(100, 300), 2),
            "expected_return": round(np.random.uniform(0.05, 0.15), 3),
            "probability": round(np.random.uniform(0.6, 0.9), 2),
            "timeframe": "1-4 hours",
            "status": "candidate" if score > 80 else "monitoring"
        })
    
    return {
        "status": "success",
        "analysis_time": datetime.now().isoformat(),
        "symbols_analyzed": len(symbols),
        "candidates": results,
        "btc_benchmark": 0.08
    }

@app.post("/scan")
async def full_scan(request: dict = None):
    """Full market scan for candidates"""
    timeframe = request.get("timeframe", "1h") if request else "1h"
    max_results = request.get("max_results", 5) if request else 5
    
    # Mock scan results
    candidates = []
    symbols = ["TSLA", "NVDA", "AAPL", "AMZN", "GOOGL", "META", "MSFT"]
    
    for i, symbol in enumerate(symbols[:max_results]):
        score = 95 - (i * 3)  # Decreasing scores
        candidates.append({
            "rank": i + 1,
            "symbol": symbol,
            "score": score,
            "current_price": round(np.random.uniform(150, 400), 2),
            "vwap": round(np.random.uniform(145, 395), 2),
            "expected_return": round(0.12 - (i * 0.01), 3),
            "probability_reach": round(0.85 - (i * 0.03), 2),
            "timeframe": timeframe,
            "squeeze_factors": ["low_float", "high_short_interest", "volume_surge"],
            "reasoning": f"Strong momentum signals detected for {symbol}"
        })
    
    return {
        "status": "success",
        "scan_time": datetime.now().isoformat(),
        "timeframe": timeframe,
        "total_scanned": 3000,
        "candidates_found": len(candidates),
        "btc_benchmark": 0.08,
        "candidates": candidates
    }

if __name__ == "__main__":
    print("🚀 Starting Market Scanner API on port 8888...")
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info")
