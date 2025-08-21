"""Options pressure detection engine - gamma walls and dealer positioning"""

import numpy as np
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from scipy.stats import norm

from ..utils import MarketData, OptionsData, logger
from ..config import config

@dataclass
class GammaWall:
    strike: float
    gamma_value: float
    net_positioning: float  # Positive = dealers long, negative = dealers short
    distance_from_price: float
    probability_reach: float

@dataclass
class PressureSignal:
    target_strike: Optional[float]
    probability_reach: float
    dealer_flow: str  # "bullish", "bearish", "neutral"
    nearest_walls: List[GammaWall]
    max_pain: float
    put_call_ratio: float
    score: float

class PressureEngine:
    """Analyzes options flow and dealer positioning"""
    
    def __init__(self):
        pass
    
    def analyze(self, market_data: MarketData, options_data: Optional[OptionsData] = None) -> PressureSignal:
        """Analyze options pressure signals"""
        try:
            if options_data is None:
                # Generate synthetic options data for demonstration
                options_data = self._generate_synthetic_options(market_data)
            
            # Find gamma walls
            gamma_walls = self._find_gamma_walls(market_data, options_data)
            
            # Find nearest significant wall
            target_wall = self._find_target_wall(market_data.price, gamma_walls)
            
            # Calculate max pain
            max_pain = self._calculate_max_pain(market_data.price, options_data)
            
            # Calculate put/call ratio
            pcr = self._calculate_put_call_ratio(options_data)
            
            # Determine dealer flow bias
            dealer_flow = self._determine_dealer_flow(gamma_walls, pcr, market_data.price, max_pain)
            
            # Calculate probability of reaching target
            probability = 0.0
            target_strike = None
            if target_wall:
                target_strike = target_wall.strike
                probability = self._calculate_probability_reach(
                    market_data.price, target_wall.strike, options_data
                )
            
            # Calculate composite score
            score = self._calculate_pressure_score(probability, dealer_flow, pcr, gamma_walls)
            
            return PressureSignal(
                target_strike=target_strike,
                probability_reach=probability,
                dealer_flow=dealer_flow,
                nearest_walls=gamma_walls[:3],  # Top 3 walls
                max_pain=max_pain,
                put_call_ratio=pcr,
                score=score
            )
            
        except Exception as e:
            logger.error(f"Error analyzing pressure signals for {market_data.symbol}: {e}")
            return PressureSignal(
                target_strike=None, probability_reach=0, dealer_flow="neutral",
                nearest_walls=[], max_pain=market_data.price, put_call_ratio=1.0, score=0
            )
    
    def _generate_synthetic_options(self, market_data: MarketData) -> OptionsData:
        """Generate synthetic options data for demonstration"""
        current_price = market_data.price
        
        # Generate strikes around current price
        strikes = []
        for i in range(-10, 11):
            strike = round(current_price + (i * 0.5), 2)
            if strike > 0:
                strikes.append(strike)
        
        calls_volume = {}
        puts_volume = {}
        calls_oi = {}
        puts_oi = {}
        iv = {}
        
        np.random.seed(hash(market_data.symbol) % 2**32)
        
        for strike in strikes:
            # Higher volume/OI near the money
            distance = abs(strike - current_price) / current_price
            base_volume = max(10, int(1000 * np.exp(-distance * 10)))
            base_oi = max(50, int(5000 * np.exp(-distance * 8)))
            
            calls_volume[strike] = int(base_volume * np.random.uniform(0.5, 2.0))
            puts_volume[strike] = int(base_volume * np.random.uniform(0.5, 2.0))
            calls_oi[strike] = int(base_oi * np.random.uniform(0.5, 2.0))
            puts_oi[strike] = int(base_oi * np.random.uniform(0.5, 2.0))
            
            # IV smile
            base_iv = 0.3 + (distance * 2)  # Higher IV for OTM options
            iv[strike] = max(0.1, base_iv + np.random.uniform(-0.1, 0.1))
        
        return OptionsData(
            symbol=market_data.symbol,
            strikes=strikes,
            calls_volume=calls_volume,
            puts_volume=puts_volume,
            calls_oi=calls_oi,
            puts_oi=puts_oi,
            iv=iv,
            timestamp=market_data.timestamp
        )
    
    def _find_gamma_walls(self, market_data: MarketData, options_data: OptionsData) -> List[GammaWall]:
        """Find significant gamma walls"""
        walls = []
        current_price = market_data.price
        
        for strike in options_data.strikes:
            # Calculate total gamma exposure at this strike
            calls_oi = options_data.calls_oi.get(strike, 0)
            puts_oi = options_data.puts_oi.get(strike, 0)
            
            # Simplified gamma calculation (in reality, would use Black-Scholes)
            distance = abs(strike - current_price) / current_price
            gamma_factor = np.exp(-distance * 5)  # Gamma decreases with distance
            
            # Net dealer positioning (simplified)
            # Assumes dealers are short calls (positive gamma for stock) and long puts (negative gamma for stock)
            net_gamma = (calls_oi * gamma_factor) - (puts_oi * gamma_factor)
            
            if abs(net_gamma) > 1000:  # Significant gamma level
                probability = self._calculate_probability_reach(current_price, strike, options_data)
                
                wall = GammaWall(
                    strike=strike,
                    gamma_value=abs(net_gamma),
                    net_positioning=net_gamma,
                    distance_from_price=distance,
                    probability_reach=probability
                )
                walls.append(wall)
        
        # Sort by gamma value (most significant first)
        return sorted(walls, key=lambda w: w.gamma_value, reverse=True)
    
    def _find_target_wall(self, current_price: float, walls: List[GammaWall]) -> Optional[GammaWall]:
        """Find the most attractive target wall"""
        if not walls:
            return None
        
        # Find walls within reasonable distance and with good probability
        candidates = [
            wall for wall in walls 
            if wall.distance_from_price < 0.15 and wall.probability_reach > 0.3
        ]
        
        if not candidates:
            return walls[0] if walls else None
        
        # Return the one with best probability/gamma combination
        return max(candidates, key=lambda w: w.probability_reach * w.gamma_value)
    
    def _calculate_max_pain(self, current_price: float, options_data: OptionsData) -> float:
        """Calculate max pain level"""
        max_pain_levels = {}
        
        for strike in options_data.strikes:
            total_pain = 0
            
            # Pain for call holders
            if current_price > strike:
                total_pain += options_data.calls_oi.get(strike, 0) * (current_price - strike)
            
            # Pain for put holders
            if current_price < strike:
                total_pain += options_data.puts_oi.get(strike, 0) * (strike - current_price)
            
            max_pain_levels[strike] = total_pain
        
        # Return strike with minimum total pain
        if max_pain_levels:
            return min(max_pain_levels.keys(), key=lambda s: max_pain_levels[s])
        return current_price
    
    def _calculate_put_call_ratio(self, options_data: OptionsData) -> float:
        """Calculate put/call ratio"""
        total_call_volume = sum(options_data.calls_volume.values())
        total_put_volume = sum(options_data.puts_volume.values())
        
        if total_call_volume == 0:
            return float('inf') if total_put_volume > 0 else 1.0
        
        return total_put_volume / total_call_volume
    
    def _determine_dealer_flow(self, walls: List[GammaWall], pcr: float, 
                             current_price: float, max_pain: float) -> str:
        """Determine overall dealer flow bias"""
        if not walls:
            return "neutral"
        
        # Analyze strongest wall positioning
        strongest_wall = walls[0]
        
        # Bullish indicators
        bullish_score = 0
        if strongest_wall.net_positioning > 0 and strongest_wall.strike > current_price:
            bullish_score += 2
        if pcr < 0.8:  # Low put/call ratio
            bullish_score += 1
        if max_pain > current_price:
            bullish_score += 1
        
        # Bearish indicators  
        bearish_score = 0
        if strongest_wall.net_positioning < 0 and strongest_wall.strike < current_price:
            bearish_score += 2
        if pcr > 1.2:  # High put/call ratio
            bearish_score += 1
        if max_pain < current_price:
            bearish_score += 1
        
        if bullish_score > bearish_score + 1:
            return "bullish"
        elif bearish_score > bullish_score + 1:
            return "bearish"
        else:
            return "neutral"
    
    def _calculate_probability_reach(self, current_price: float, target_strike: float, 
                                   options_data: OptionsData) -> float:
        """Calculate probability of reaching target strike"""
        if target_strike == current_price:
            return 1.0
        
        # Get average IV for calculation
        avg_iv = np.mean(list(options_data.iv.values()))
        
        # Simplified probability calculation (1 day to expiry)
        time_to_expiry = 1.0 / 365  # 1 day
        
        # Black-Scholes probability approximation
        d2 = (np.log(current_price / target_strike) - 0.5 * avg_iv**2 * time_to_expiry) / (avg_iv * np.sqrt(time_to_expiry))
        
        if target_strike > current_price:
            # Probability of finishing above strike
            probability = 1 - norm.cdf(d2)
        else:
            # Probability of finishing below strike
            probability = norm.cdf(d2)
        
        return max(0.01, min(0.99, probability))
    
    def _calculate_pressure_score(self, probability: float, dealer_flow: str, 
                                pcr: float, walls: List[GammaWall]) -> float:
        """Calculate composite pressure score"""
        score = 0.0
        
        # Probability component (0-40 points)
        score += probability * 40
        
        # Dealer flow component (0-30 points)
        if dealer_flow == "bullish":
            score += 30
        elif dealer_flow == "bearish":
            score += 20  # Still tradeable, just bearish
        
        # Put/call ratio component (0-20 points)
        if pcr < 0.7:  # Very bullish
            score += 20
        elif pcr < 1.0:  # Moderately bullish
            score += 15
        elif pcr > 1.5:  # Very bearish but can squeeze
            score += 10
        
        # Gamma wall strength (0-10 points)
        if walls:
            strongest_gamma = walls[0].gamma_value
            score += min(10, strongest_gamma / 5000)  # Scale appropriately
        
        return min(100, score)
    
    def get_pressure_reasoning(self, signal: PressureSignal) -> str:
        """Generate human-readable reasoning for pressure signal"""
        reasons = []
        
        if signal.target_strike:
            reasons.append(f"Target strike ${signal.target_strike:.2f} ({signal.probability_reach:.1%} probability)")
        
        reasons.append(f"Dealer flow: {signal.dealer_flow}")
        
        if signal.put_call_ratio < 0.8:
            reasons.append(f"Low P/C ratio ({signal.put_call_ratio:.2f}) - bullish")
        elif signal.put_call_ratio > 1.2:
            reasons.append(f"High P/C ratio ({signal.put_call_ratio:.2f}) - squeeze potential")
        
        if signal.nearest_walls:
            wall_count = len(signal.nearest_walls)
            reasons.append(f"{wall_count} significant gamma wall(s)")
        
        return "; ".join(reasons)