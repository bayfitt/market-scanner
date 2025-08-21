"""Squeeze fuel detection engine - float, short interest, volume analysis"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..utils import MarketData, logger
from ..config import config

@dataclass
class FundamentalData:
    symbol: str
    float_shares: int
    short_percent: float
    short_shares: int
    borrow_fee: float
    avg_volume: int
    market_cap: float
    insider_ownership: float

@dataclass
class FuelSignal:
    low_float: bool
    high_short_interest: bool
    high_borrow_cost: bool
    volume_surge: bool
    relative_volume: float
    short_squeeze_score: float
    fuel_factors: List[str]
    score: float

class FuelEngine:
    """Analyzes squeeze fuel metrics - float, short interest, volume"""
    
    def __init__(self):
        self.fundamental_cache = {}
    
    def analyze(self, market_data: MarketData, fundamental_data: Optional[FundamentalData] = None) -> FuelSignal:
        """Analyze squeeze fuel signals"""
        try:
            if fundamental_data is None:
                # Generate synthetic fundamental data for demonstration
                fundamental_data = self._generate_synthetic_fundamentals(market_data)
            
            # Check float size
            low_float = fundamental_data.float_shares < config.MAX_FLOAT_SIZE
            
            # Check short interest
            high_short_interest = fundamental_data.short_percent > 15.0
            
            # Check borrow cost
            high_borrow_cost = fundamental_data.borrow_fee > 50.0  # 50% annual rate
            
            # Check volume surge
            relative_volume = market_data.volume / fundamental_data.avg_volume if fundamental_data.avg_volume > 0 else 1.0
            volume_surge = relative_volume > config.MIN_VOLUME_MULTIPLE
            
            # Calculate short squeeze score
            squeeze_score = self._calculate_squeeze_score(fundamental_data, relative_volume)
            
            # Identify fuel factors
            fuel_factors = self._identify_fuel_factors(
                low_float, high_short_interest, high_borrow_cost, volume_surge, fundamental_data
            )
            
            # Calculate composite score
            score = self._calculate_fuel_score(
                low_float, high_short_interest, high_borrow_cost, volume_surge, 
                relative_volume, squeeze_score
            )
            
            return FuelSignal(
                low_float=low_float,
                high_short_interest=high_short_interest,
                high_borrow_cost=high_borrow_cost,
                volume_surge=volume_surge,
                relative_volume=relative_volume,
                short_squeeze_score=squeeze_score,
                fuel_factors=fuel_factors,
                score=score
            )
            
        except Exception as e:
            logger.error(f"Error analyzing fuel signals for {market_data.symbol}: {e}")
            return FuelSignal(
                low_float=False, high_short_interest=False, high_borrow_cost=False,
                volume_surge=False, relative_volume=1.0, short_squeeze_score=0,
                fuel_factors=[], score=0
            )
    
    def _generate_synthetic_fundamentals(self, market_data: MarketData) -> FundamentalData:
        """Generate synthetic fundamental data for demonstration"""
        np.random.seed(hash(market_data.symbol) % 2**32)
        
        # Generate realistic fundamental metrics
        base_float = np.random.uniform(5_000_000, 50_000_000)  # 5M-50M shares
        short_percent = np.random.uniform(5, 40)  # 5-40% short interest
        borrow_fee = np.random.uniform(10, 200)  # 10-200% annual borrow rate
        avg_volume = market_data.volume * np.random.uniform(0.5, 2.0)  # Random baseline volume
        market_cap = market_data.price * base_float
        insider_ownership = np.random.uniform(5, 50)  # 5-50% insider ownership
        
        return FundamentalData(
            symbol=market_data.symbol,
            float_shares=int(base_float),
            short_percent=short_percent,
            short_shares=int(base_float * short_percent / 100),
            borrow_fee=borrow_fee,
            avg_volume=int(avg_volume),
            market_cap=market_cap,
            insider_ownership=insider_ownership
        )
    
    def _calculate_squeeze_score(self, fundamental_data: FundamentalData, relative_volume: float) -> float:
        """Calculate proprietary short squeeze potential score"""
        score = 0.0
        
        # Float factor (smaller = better)
        if fundamental_data.float_shares < 5_000_000:
            score += 30  # Micro float
        elif fundamental_data.float_shares < 10_000_000:
            score += 25  # Small float
        elif fundamental_data.float_shares < 20_000_000:
            score += 15  # Medium float
        
        # Short interest factor
        if fundamental_data.short_percent > 30:
            score += 25  # Very high short interest
        elif fundamental_data.short_percent > 20:
            score += 20  # High short interest
        elif fundamental_data.short_percent > 15:
            score += 10  # Moderate short interest
        
        # Borrow cost factor
        if fundamental_data.borrow_fee > 100:
            score += 20  # Very expensive to short
        elif fundamental_data.borrow_fee > 50:
            score += 15  # Expensive to short
        elif fundamental_data.borrow_fee > 25:
            score += 5   # Moderately expensive
        
        # Volume factor
        if relative_volume > 5:
            score += 15  # Massive volume surge
        elif relative_volume > 3:
            score += 10  # Large volume surge
        elif relative_volume > 2:
            score += 5   # Moderate volume surge
        
        # Insider ownership bonus (harder to borrow shares)
        if fundamental_data.insider_ownership > 40:
            score += 10
        elif fundamental_data.insider_ownership > 30:
            score += 5
        
        return min(100, score)
    
    def _identify_fuel_factors(self, low_float: bool, high_short_interest: bool, 
                             high_borrow_cost: bool, volume_surge: bool, 
                             fundamental_data: FundamentalData) -> List[str]:
        """Identify and label squeeze fuel factors"""
        factors = []
        
        if low_float:
            if fundamental_data.float_shares < 5_000_000:
                factors.append("micro_float")
            elif fundamental_data.float_shares < 10_000_000:
                factors.append("small_float")
            else:
                factors.append("low_float")
        
        if high_short_interest:
            if fundamental_data.short_percent > 30:
                factors.append("extreme_short_interest")
            elif fundamental_data.short_percent > 20:
                factors.append("high_short_interest")
            else:
                factors.append("elevated_short_interest")
        
        if high_borrow_cost:
            if fundamental_data.borrow_fee > 100:
                factors.append("extreme_borrow_cost")
            else:
                factors.append("high_borrow_cost")
        
        if volume_surge:
            factors.append("volume_surge")
        
        # Additional factors
        if fundamental_data.insider_ownership > 40:
            factors.append("high_insider_ownership")
        
        if fundamental_data.float_shares < 5_000_000 and fundamental_data.short_percent > 25:
            factors.append("squeeze_setup")
        
        return factors
    
    def _calculate_fuel_score(self, low_float: bool, high_short_interest: bool,
                            high_borrow_cost: bool, volume_surge: bool,
                            relative_volume: float, squeeze_score: float) -> float:
        """Calculate composite fuel score"""
        score = 0.0
        
        # Float component (0-25 points)
        if low_float:
            score += 25
        
        # Short interest component (0-25 points)
        if high_short_interest:
            score += 25
        
        # Borrow cost component (0-20 points)
        if high_borrow_cost:
            score += 20
        
        # Volume component (0-20 points)
        if volume_surge:
            volume_score = min(20, (relative_volume - 2) * 5)  # Scale volume appropriately
            score += volume_score
        
        # Squeeze score bonus (0-10 points)
        score += min(10, squeeze_score / 10)
        
        return min(100, score)
    
    def get_fuel_reasoning(self, signal: FuelSignal, fundamental_data: Optional[FundamentalData] = None) -> str:
        """Generate human-readable reasoning for fuel signal"""
        reasons = []
        
        if signal.low_float and fundamental_data:
            reasons.append(f"Low float ({fundamental_data.float_shares:,} shares)")
        
        if signal.high_short_interest and fundamental_data:
            reasons.append(f"High short interest ({fundamental_data.short_percent:.1f}%)")
        
        if signal.high_borrow_cost and fundamental_data:
            reasons.append(f"High borrow cost ({fundamental_data.borrow_fee:.0f}% annual)")
        
        if signal.volume_surge:
            reasons.append(f"Volume surge ({signal.relative_volume:.1f}x average)")
        
        if signal.short_squeeze_score > 70:
            reasons.append(f"Strong squeeze setup (score: {signal.short_squeeze_score:.0f})")
        
        if signal.fuel_factors:
            factor_str = ", ".join(signal.fuel_factors)
            reasons.append(f"Fuel factors: {factor_str}")
        
        if not reasons:
            reasons.append("Limited squeeze fuel detected")
        
        return "; ".join(reasons)
    
    def estimate_squeeze_potential(self, signal: FuelSignal, fundamental_data: FundamentalData) -> Dict[str, float]:
        """Estimate potential price movement if squeeze occurs"""
        if signal.short_squeeze_score < 50:
            return {"low": 1.1, "medium": 1.2, "high": 1.3}
        
        # Base multipliers based on short interest
        base_multiplier = 1.0 + (fundamental_data.short_percent / 100)
        
        # Float factor - smaller float = higher potential
        if fundamental_data.float_shares < 5_000_000:
            float_multiplier = 1.5
        elif fundamental_data.float_shares < 10_000_000:
            float_multiplier = 1.3
        else:
            float_multiplier = 1.1
        
        # Volume factor
        volume_multiplier = 1.0 + min(0.5, (signal.relative_volume - 2) * 0.1)
        
        total_multiplier = base_multiplier * float_multiplier * volume_multiplier
        
        return {
            "low": total_multiplier * 0.8,
            "medium": total_multiplier,
            "high": total_multiplier * 1.5
        }