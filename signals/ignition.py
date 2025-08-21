"""Ignition timing signal engine - VWAP momentum and band analysis"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from ..utils import MarketData, calculate_ema, calculate_bollinger_bands, logger
from ..config import config

@dataclass
class IgnitionSignal:
    vwap_momentum: bool
    expansion_energy: bool  
    entry_timing: bool
    vwap_spread_slope: float
    band_expansion_ratio: float
    distance_from_extremes: float
    score: float

class IgnitionEngine:
    """Detects VWAP momentum and band expansion signals"""
    
    def __init__(self):
        self.historical_data = {}  # Cache for historical calculations
    
    def analyze(self, market_data: MarketData, historical_prices: Optional[pd.Series] = None) -> IgnitionSignal:
        """Analyze ignition timing signals for a symbol"""
        try:
            # If no historical data provided, create synthetic data for demo
            if historical_prices is None:
                historical_prices = self._generate_synthetic_history(market_data)
            
            # Calculate VWAP spread slope
            vwap_spread = self._calculate_vwap_spread(historical_prices, market_data.vwap)
            vwap_slope = self._calculate_slope(vwap_spread)
            
            # Calculate band expansion
            upper_band, sma, lower_band = calculate_bollinger_bands(historical_prices)
            current_expansion = upper_band.iloc[-1] - lower_band.iloc[-1]
            historical_avg_expansion = (upper_band - lower_band).rolling(20).mean().iloc[-1]
            expansion_ratio = current_expansion / historical_avg_expansion if historical_avg_expansion > 0 else 1.0
            
            # Calculate distance from extremes
            distance_from_extremes = min(
                abs(market_data.price - market_data.high) / market_data.price,
                abs(market_data.price - market_data.low) / market_data.price
            )
            
            # Generate signals
            vwap_momentum = vwap_slope > 0.001  # Positive VWAP momentum
            expansion_energy = expansion_ratio > 1.5  # Band expansion above average
            entry_timing = distance_from_extremes < config.MAX_DISTANCE_FROM_HOD_LOD
            
            # Calculate composite score (0-100)
            score = self._calculate_ignition_score(
                vwap_slope, expansion_ratio, distance_from_extremes,
                vwap_momentum, expansion_energy, entry_timing
            )
            
            return IgnitionSignal(
                vwap_momentum=vwap_momentum,
                expansion_energy=expansion_energy,
                entry_timing=entry_timing,
                vwap_spread_slope=vwap_slope,
                band_expansion_ratio=expansion_ratio,
                distance_from_extremes=distance_from_extremes,
                score=score
            )
            
        except Exception as e:
            logger.error(f"Error analyzing ignition signals for {market_data.symbol}: {e}")
            return IgnitionSignal(
                vwap_momentum=False, expansion_energy=False, entry_timing=False,
                vwap_spread_slope=0, band_expansion_ratio=1.0, distance_from_extremes=1.0,
                score=0
            )
    
    def _calculate_vwap_spread(self, prices: pd.Series, current_vwap: float) -> pd.Series:
        """Calculate spread between price and VWAP over time"""
        # For demonstration, create a spread series
        # In production, this would use real VWAP data
        synthetic_vwap = prices.rolling(20).mean()  # Approximate VWAP with SMA
        return (prices - synthetic_vwap) / synthetic_vwap
    
    def _calculate_slope(self, series: pd.Series, periods: int = 10) -> float:
        """Calculate slope of recent price movement"""
        if len(series) < periods:
            return 0.0
        
        recent_data = series.tail(periods)
        x = np.arange(len(recent_data))
        y = recent_data.values
        
        # Linear regression slope
        slope = np.polyfit(x, y, 1)[0]
        return slope
    
    def _generate_synthetic_history(self, market_data: MarketData, periods: int = 100) -> pd.Series:
        """Generate synthetic historical data for demonstration"""
        # Create realistic price movement around current price
        np.random.seed(hash(market_data.symbol) % 2**32)  # Deterministic randomness
        
        base_price = market_data.price * 0.95  # Start slightly below current
        returns = np.random.normal(0, 0.02, periods)  # 2% daily volatility
        prices = [base_price]
        
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(new_price)
        
        # Ensure current price is the last price
        prices[-1] = market_data.price
        
        return pd.Series(prices)
    
    def _calculate_ignition_score(self, vwap_slope: float, expansion_ratio: float, 
                                distance_from_extremes: float, vwap_momentum: bool,
                                expansion_energy: bool, entry_timing: bool) -> float:
        """Calculate composite ignition score"""
        score = 0.0
        
        # VWAP momentum component (0-40 points)
        if vwap_momentum:
            score += min(40, abs(vwap_slope) * 10000)  # Scale slope appropriately
        
        # Band expansion component (0-35 points)
        if expansion_energy:
            score += min(35, (expansion_ratio - 1) * 35)
        
        # Entry timing component (0-25 points)
        if entry_timing:
            timing_score = (config.MAX_DISTANCE_FROM_HOD_LOD - distance_from_extremes) / config.MAX_DISTANCE_FROM_HOD_LOD
            score += timing_score * 25
        
        return min(100, score)
    
    def get_ignition_reasoning(self, signal: IgnitionSignal) -> str:
        """Generate human-readable reasoning for the ignition signal"""
        reasons = []
        
        if signal.vwap_momentum:
            reasons.append(f"VWAP momentum positive (slope: {signal.vwap_spread_slope:.4f})")
        
        if signal.expansion_energy:
            reasons.append(f"Band expansion {signal.band_expansion_ratio:.1f}x average")
        
        if signal.entry_timing:
            reasons.append(f"Good entry timing ({signal.distance_from_extremes:.1%} from extremes)")
        
        if not reasons:
            reasons.append("Ignition signals not triggered")
        
        return "; ".join(reasons)