"""Configuration settings for the market scanner"""

import os
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ScannerConfig:
    # Data sources
    DEFAULT_SYMBOLS_FILE: str = "24h-stocks.csv"
    REDIS_URL: str = "redis://localhost:6379"
    
    # FREE API keys (all optional - app works without any keys)
    ALPHA_VANTAGE_KEY: str = os.getenv("ALPHA_VANTAGE_KEY", "")  # FREE: 500 requests/day
    FMP_KEY: str = os.getenv("FMP_KEY", "")  # FREE: 250 requests/day
    # Note: Yahoo Finance requires no API key and is unlimited for basic data
    
    # Scanning parameters
    MAX_SYMBOLS_PER_SCAN: int = 3
    MIN_PRICE: float = 2.0
    MAX_PRICE: float = 500.0
    MIN_VOLUME_MULTIPLE: float = 2.0
    MIN_SCORE_THRESHOLD: int = 70
    
    # Signal weights
    VWAP_MOMENTUM_WEIGHT: float = 25.0
    OPTIONS_PRESSURE_WEIGHT: float = 30.0
    VOLUME_WEIGHT: float = 20.0
    FLOAT_WEIGHT: float = 15.0
    TIMING_WEIGHT: float = 10.0
    
    # Risk controls
    MAX_DISTANCE_FROM_HOD_LOD: float = 0.20  # 20%
    MIN_PROBABILITY_THRESHOLD: float = 0.65  # 65%
    MIN_FLOAT_SIZE: int = 1_000_000  # 1M shares
    MAX_FLOAT_SIZE: int = 20_000_000  # 20M shares
    
    # BTC benchmark
    BTC_SYMBOL: str = "BTC-USD"
    BENCHMARK_TIMEFRAMES: List[str] = ["1h", "4h", "1d"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "market_scanner.log"
    
    # Performance tracking
    TRACK_PERFORMANCE: bool = True
    PERFORMANCE_DB: str = "performance.db"

# Global config instance
config = ScannerConfig()