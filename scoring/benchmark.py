"""BTC benchmarking system - ensures candidates outperform Bitcoin"""

import asyncio
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional

from config import config
from utils import logger

class BTCBenchmark:
    """Handles Bitcoin benchmarking for candidate comparison"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
    
    async def get_expected_return(self, timeframe: str = "1h") -> float:
        """Get expected BTC return for the given timeframe"""
        cache_key = f"btc_return_{timeframe}"
        
        # Check cache
        if cache_key in self.cache:
            cached_time, cached_value = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_duration:
                return cached_value
        
        try:
            # Get BTC data
            btc_data = await self._fetch_btc_data()
            if not btc_data:
                return 0.02  # Default 2% expectation if data unavailable
            
            # Calculate expected return based on timeframe
            expected_return = self._calculate_expected_return(btc_data, timeframe)
            
            # Cache the result
            self.cache[cache_key] = (datetime.now(), expected_return)
            
            return expected_return
            
        except Exception as e:
            logger.error(f"Error calculating BTC benchmark: {e}")
            return 0.02  # Conservative default
    
    async def _fetch_btc_data(self) -> Optional[pd.DataFrame]:
        """Fetch recent BTC price data"""
        try:
            btc = yf.Ticker(config.BTC_SYMBOL)
            
            # Get 7 days of hourly data
            hist = btc.history(period="7d", interval="1h")
            
            if hist.empty:
                logger.warning("No BTC data available")
                return None
            
            return hist
            
        except Exception as e:
            logger.error(f"Error fetching BTC data: {e}")
            return None
    
    def _calculate_expected_return(self, btc_data: pd.DataFrame, timeframe: str) -> float:
        """Calculate expected BTC return based on historical volatility and momentum"""
        
        # Calculate returns
        btc_data['returns'] = btc_data['Close'].pct_change()
        
        # Get timeframe-specific parameters
        periods = self._get_periods_for_timeframe(timeframe)
        
        if len(btc_data) < periods * 2:
            return 0.02  # Default if insufficient data
        
        # Calculate recent volatility (standard deviation of returns)
        recent_vol = btc_data['returns'].tail(periods * 4).std()
        
        # Calculate momentum (recent trend)
        recent_returns = btc_data['returns'].tail(periods)
        momentum = recent_returns.mean()
        
        # Calculate expected return based on momentum and volatility
        # In trending markets, expect momentum to continue
        # In volatile markets, expect larger moves
        
        base_expectation = momentum * periods  # Scale momentum to timeframe
        volatility_expectation = recent_vol * np.sqrt(periods)  # Scale volatility to timeframe
        
        # Conservative approach: use lower of momentum or volatility expectation
        expected_return = min(abs(base_expectation), volatility_expectation)
        
        # Apply directional bias if momentum is strong
        if abs(momentum) > recent_vol * 0.5:  # Strong momentum
            expected_return = abs(base_expectation)
        
        # Minimum expectation (market typically moves)
        expected_return = max(expected_return, 0.01)  # At least 1%
        
        # Maximum reasonable expectation for timeframe
        max_expectation = self._get_max_expectation_for_timeframe(timeframe)
        expected_return = min(expected_return, max_expectation)
        
        logger.debug(f"BTC {timeframe} expected return: {expected_return:.3f} "
                    f"(momentum: {momentum:.4f}, vol: {recent_vol:.4f})")
        
        return expected_return
    
    def _get_periods_for_timeframe(self, timeframe: str) -> int:
        """Get number of periods (hours) for the given timeframe"""
        timeframe_map = {
            "20m": 1,  # Less than 1 hour
            "1h": 1,
            "2h": 2,
            "4h": 4,
            "1d": 24
        }
        
        # Extract number and unit from timeframe string
        if "h" in timeframe:
            hours = int(timeframe.replace("h", ""))
            return hours
        elif "m" in timeframe:
            return 1  # Minutes mapped to 1 hour
        elif "d" in timeframe:
            days = int(timeframe.replace("d", ""))
            return days * 24
        else:
            return timeframe_map.get(timeframe, 1)
    
    def _get_max_expectation_for_timeframe(self, timeframe: str) -> float:
        """Get maximum reasonable expectation for timeframe"""
        max_expectations = {
            "20m": 0.03,   # 3% max in 20 minutes
            "1h": 0.05,    # 5% max in 1 hour
            "2h": 0.08,    # 8% max in 2 hours
            "4h": 0.12,    # 12% max in 4 hours
            "1d": 0.20     # 20% max in 1 day
        }
        
        periods = self._get_periods_for_timeframe(timeframe)
        
        if periods <= 1:
            return 0.05
        elif periods <= 2:
            return 0.08
        elif periods <= 4:
            return 0.12
        else:
            return 0.20
    
    async def compare_to_btc(self, expected_return: float, timeframe: str = "1h") -> Dict[str, float]:
        """Compare expected return to BTC benchmark"""
        btc_return = await self.get_expected_return(timeframe)
        
        outperformance = expected_return - btc_return
        outperformance_ratio = expected_return / btc_return if btc_return > 0 else float('inf')
        
        return {
            "expected_return": expected_return,
            "btc_return": btc_return,
            "outperformance": outperformance,
            "outperformance_ratio": outperformance_ratio,
            "beats_btc": expected_return > btc_return
        }
    
    def get_benchmark_summary(self, timeframe: str = "1h") -> str:
        """Get human-readable benchmark summary"""
        try:
            # Use cached value if available
            cache_key = f"btc_return_{timeframe}"
            if cache_key in self.cache:
                cached_time, btc_return = self.cache[cache_key]
                if (datetime.now() - cached_time).seconds < self.cache_duration:
                    return f"BTC {timeframe} benchmark: {btc_return:.1%}"
            
            return f"BTC {timeframe} benchmark: fetching..."
            
        except Exception as e:
            logger.error(f"Error getting benchmark summary: {e}")
            return "BTC benchmark: unavailable"