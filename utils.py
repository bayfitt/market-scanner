"""Utility functions for the market scanner"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class MarketData:
    symbol: str
    price: float
    volume: int
    vwap: float
    high: float
    low: float
    open: float
    timestamp: datetime
    
@dataclass
class OptionsData:
    symbol: str
    strikes: List[float]
    calls_volume: Dict[float, int]
    puts_volume: Dict[float, int]
    calls_oi: Dict[float, int]
    puts_oi: Dict[float, int]
    iv: Dict[float, float]
    timestamp: datetime

@dataclass
class ScanResult:
    symbol: str
    rank: int
    score: float
    current_price: float
    vwap: float
    target_strike: Optional[float]
    probability_reach: float
    expected_return: float
    timeframe: str
    entry_zone: Tuple[float, float]
    stop_loss: float
    squeeze_factors: List[str]
    reasoning: str

def setup_logging(log_level: str = "INFO", log_file: str = "market_scanner.log"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return prices.ewm(span=period).mean()

def calculate_vwap(prices: pd.Series, volumes: pd.Series) -> float:
    """Calculate Volume Weighted Average Price"""
    return (prices * volumes).sum() / volumes.sum()

def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands"""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def is_market_hours() -> bool:
    """Check if market is currently open (9:30 AM - 4:00 PM ET)"""
    now = datetime.now()
    # Simplified - would need proper timezone handling for production
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return market_open <= now <= market_close

def format_percentage(value: float) -> str:
    """Format decimal as percentage"""
    return f"{value * 100:.1f}%"

def format_currency(value: float) -> str:
    """Format value as currency"""
    return f"${value:.2f}"

def calculate_distance_from_extremes(price: float, high: float, low: float) -> float:
    """Calculate minimum distance from high/low as percentage"""
    distance_from_high = abs(price - high) / price
    distance_from_low = abs(price - low) / price
    return min(distance_from_high, distance_from_low)

def estimate_timeframe(probability: float, volatility: float) -> str:
    """Estimate timeframe for reaching target based on probability and volatility"""
    if probability > 0.8:
        return "20-60 minutes"
    elif probability > 0.7:
        return "1-2 hours"
    elif probability > 0.6:
        return "2-4 hours"
    else:
        return "4+ hours"

logger = setup_logging()