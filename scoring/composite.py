"""Composite scoring algorithm - combines all signals and benchmarks against BTC"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from utils import MarketData, ScanResult, logger
from signals import IgnitionEngine, PressureEngine, FuelEngine, IgnitionSignal, PressureSignal, FuelSignal
from config import config
from benchmark import BTCBenchmark

@dataclass
class CompositeScore:
    symbol: str
    total_score: float
    ignition_score: float
    pressure_score: float
    fuel_score: float
    btc_benchmark_passed: bool
    expected_return: float
    btc_expected_return: float
    probability_reach: float
    target_price: Optional[float]
    risk_reward_ratio: float
    
class CompositeScorer:
    """Combines all signal engines and calculates final scores"""
    
    def __init__(self):
        self.ignition_engine = IgnitionEngine()
        self.pressure_engine = PressureEngine()
        self.fuel_engine = FuelEngine()
        self.btc_benchmark = BTCBenchmark()
        
    async def score_symbol(self, market_data: MarketData, 
                          timeframe: str = "1h") -> Optional[CompositeScore]:
        """Score a single symbol using all engines"""
        try:
            # Run all signal engines
            ignition_signal = self.ignition_engine.analyze(market_data)
            pressure_signal = self.pressure_engine.analyze(market_data)
            fuel_signal = self.fuel_engine.analyze(market_data)
            
            # Calculate weighted composite score
            total_score = self._calculate_weighted_score(
                ignition_signal, pressure_signal, fuel_signal
            )
            
            # Calculate expected return and target price
            expected_return, target_price = self._calculate_expected_return(
                market_data, pressure_signal, fuel_signal
            )
            
            # Get BTC benchmark
            btc_return = await self.btc_benchmark.get_expected_return(timeframe)
            btc_passed = expected_return > btc_return
            
            # Calculate risk/reward ratio
            risk_reward = self._calculate_risk_reward(
                market_data.price, target_price, expected_return
            )
            
            return CompositeScore(
                symbol=market_data.symbol,
                total_score=total_score,
                ignition_score=ignition_signal.score,
                pressure_score=pressure_signal.score,
                fuel_score=fuel_signal.score,
                btc_benchmark_passed=btc_passed,
                expected_return=expected_return,
                btc_expected_return=btc_return,
                probability_reach=pressure_signal.probability_reach,
                target_price=target_price,
                risk_reward_ratio=risk_reward
            )
            
        except Exception as e:
            logger.error(f"Error scoring symbol {market_data.symbol}: {e}")
            return None
    
    def _calculate_weighted_score(self, ignition: IgnitionSignal, 
                                pressure: PressureSignal, fuel: FuelSignal) -> float:
        """Calculate weighted composite score from all signals"""
        
        # Apply configured weights
        weighted_score = (
            ignition.score * (config.VWAP_MOMENTUM_WEIGHT / 100) +
            pressure.score * (config.OPTIONS_PRESSURE_WEIGHT / 100) +
            fuel.score * (config.VOLUME_WEIGHT / 100) +
            # Additional timing and float weights are embedded in the signals
            0  # Placeholder for additional factors
        )
        
        # Apply bonuses for signal combinations
        bonus = self._calculate_combination_bonus(ignition, pressure, fuel)
        
        final_score = min(100, weighted_score + bonus)
        
        logger.debug(f"Weighted score: {weighted_score:.1f}, bonus: {bonus:.1f}, final: {final_score:.1f}")
        
        return final_score
    
    def _calculate_combination_bonus(self, ignition: IgnitionSignal,
                                   pressure: PressureSignal, fuel: FuelSignal) -> float:
        """Calculate bonus points for favorable signal combinations"""
        bonus = 0.0
        
        # Triple confirmation bonus
        strong_signals = 0
        if ignition.score > 70:
            strong_signals += 1
        if pressure.score > 70:
            strong_signals += 1
        if fuel.score > 70:
            strong_signals += 1
        
        if strong_signals >= 3:
            bonus += 15  # Triple confirmation
        elif strong_signals >= 2:
            bonus += 8   # Double confirmation
        
        # Specific combination bonuses
        if ignition.vwap_momentum and pressure.probability_reach > 0.7:
            bonus += 5  # Momentum + high probability
        
        if fuel.low_float and fuel.high_short_interest and pressure.dealer_flow == "bullish":
            bonus += 8  # Squeeze setup with bullish flow
        
        if ignition.expansion_energy and fuel.volume_surge:
            bonus += 5  # Energy + volume
        
        return bonus
    
    def _calculate_expected_return(self, market_data: MarketData,
                                 pressure: PressureSignal, fuel: FuelSignal) -> Tuple[float, Optional[float]]:
        """Calculate expected return and target price"""
        current_price = market_data.price
        
        # Use options target if available
        if pressure.target_strike and pressure.probability_reach > 0.5:
            target_price = pressure.target_strike
            basic_return = (target_price - current_price) / current_price
        else:
            # Estimate based on volatility and signals
            estimated_move = self._estimate_price_move(market_data, fuel)
            target_price = current_price * (1 + estimated_move)
            basic_return = estimated_move
        
        # Adjust for probability
        probability_adjusted_return = basic_return * pressure.probability_reach
        
        # Squeeze multiplier from fuel signals
        if fuel.short_squeeze_score > 70:
            squeeze_multiplier = 1.0 + (fuel.short_squeeze_score / 200)  # Up to 1.5x
            probability_adjusted_return *= squeeze_multiplier
        
        return probability_adjusted_return, target_price
    
    def _estimate_price_move(self, market_data: MarketData, fuel: FuelSignal) -> float:
        """Estimate potential price move based on market data and fuel"""
        base_move = 0.05  # 5% base expectation
        
        # Volume factor
        if fuel.relative_volume > 3:
            base_move *= 1.5
        elif fuel.relative_volume > 2:
            base_move *= 1.2
        
        # Volatility factor (estimated from price range)
        if market_data.high > 0 and market_data.low > 0:
            daily_range = (market_data.high - market_data.low) / market_data.price
            if daily_range > 0.15:  # High volatility day
                base_move *= 1.3
        
        # Squeeze fuel factor
        if fuel.short_squeeze_score > 80:
            base_move *= 2.0
        elif fuel.short_squeeze_score > 60:
            base_move *= 1.5
        
        return min(0.50, base_move)  # Cap at 50% expected move
    
    def _calculate_risk_reward(self, current_price: float, target_price: Optional[float],
                             expected_return: float) -> float:
        """Calculate risk/reward ratio"""
        if not target_price or target_price <= current_price:
            return 1.0
        
        # Estimate stop loss at 5% below entry
        stop_loss = current_price * 0.95
        potential_loss = (current_price - stop_loss) / current_price
        potential_gain = expected_return
        
        if potential_loss <= 0:
            return 10.0  # Very favorable
        
        return potential_gain / potential_loss
    
    async def score_multiple_symbols(self, symbols_data: List[MarketData],
                                   timeframe: str = "1h") -> List[CompositeScore]:
        """Score multiple symbols concurrently"""
        tasks = [
            self.score_symbol(market_data, timeframe)
            for market_data in symbols_data
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        valid_scores = []
        for result in results:
            if isinstance(result, CompositeScore):
                valid_scores.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Error in concurrent scoring: {result}")
        
        return valid_scores
    
    def filter_and_rank(self, scores: List[CompositeScore]) -> List[CompositeScore]:
        """Filter scores and rank by composite criteria"""
        # Apply filters
        filtered = []
        for score in scores:
            # Must pass BTC benchmark
            if not score.btc_benchmark_passed:
                logger.debug(f"Filtered {score.symbol}: Failed BTC benchmark")
                continue
                
            # Minimum score threshold
            if score.total_score < config.MIN_SCORE_THRESHOLD:
                logger.debug(f"Filtered {score.symbol}: Score {score.total_score} below threshold")
                continue
                
            # Minimum probability
            if score.probability_reach < config.MIN_PROBABILITY_THRESHOLD:
                logger.debug(f"Filtered {score.symbol}: Probability {score.probability_reach} too low")
                continue
            
            filtered.append(score)
        
        # Rank by composite score with probability weighting
        def ranking_key(score: CompositeScore) -> float:
            return (
                score.total_score * 0.7 +  # 70% weight on total score
                score.probability_reach * 30 +  # 30% weight on probability (scaled to 0-30)
                score.risk_reward_ratio * 5  # Small bonus for good risk/reward
            )
        
        ranked = sorted(filtered, key=ranking_key, reverse=True)
        
        # Return top candidates
        return ranked[:config.MAX_SYMBOLS_PER_SCAN]
    
    def create_scan_results(self, scores: List[CompositeScore], 
                          market_data_dict: Dict[str, MarketData]) -> List[ScanResult]:
        """Convert composite scores to scan results"""
        results = []
        
        for i, score in enumerate(scores):
            market_data = market_data_dict[score.symbol]
            
            # Calculate entry zone (±1% around current price)
            entry_low = market_data.price * 0.99
            entry_high = market_data.price * 1.01
            
            # Calculate stop loss (5% below current price)
            stop_loss = market_data.price * 0.95
            
            # Estimate timeframe
            timeframe = self._estimate_timeframe(score.probability_reach)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(score, market_data)
            
            # Identify squeeze factors
            squeeze_factors = self._identify_squeeze_factors(score)
            
            result = ScanResult(
                symbol=score.symbol,
                rank=i + 1,
                score=score.total_score,
                current_price=market_data.price,
                vwap=market_data.vwap,
                target_strike=score.target_price,
                probability_reach=score.probability_reach,
                expected_return=score.expected_return,
                timeframe=timeframe,
                entry_zone=(entry_low, entry_high),
                stop_loss=stop_loss,
                squeeze_factors=squeeze_factors,
                reasoning=reasoning
            )
            
            results.append(result)
        
        return results
    
    def _estimate_timeframe(self, probability: float) -> str:
        """Estimate timeframe based on probability"""
        if probability > 0.8:
            return "20-60 minutes"
        elif probability > 0.7:
            return "1-2 hours"  
        elif probability > 0.6:
            return "2-4 hours"
        else:
            return "4+ hours"
    
    def _generate_reasoning(self, score: CompositeScore, market_data: MarketData) -> str:
        """Generate human-readable reasoning for the score"""
        reasons = []
        
        reasons.append(f"Score: {score.total_score:.0f}/100")
        
        if score.expected_return > 0.1:
            reasons.append(f"Expected return: {score.expected_return:.1%}")
        
        if score.target_price:
            reasons.append(f"Target: ${score.target_price:.2f}")
        
        reasons.append(f"vs BTC: {score.expected_return:.1%} vs {score.btc_expected_return:.1%}")
        
        if score.probability_reach > 0.7:
            reasons.append(f"High probability: {score.probability_reach:.1%}")
        
        if score.risk_reward_ratio > 3:
            reasons.append(f"Good R/R: {score.risk_reward_ratio:.1f}:1")
        
        return "; ".join(reasons)
    
    def _identify_squeeze_factors(self, score: CompositeScore) -> List[str]:
        """Identify squeeze factors from the score"""
        factors = []
        
        if score.ignition_score > 70:
            factors.append("momentum_ignition")
        
        if score.pressure_score > 70:
            factors.append("options_pressure")
        
        if score.fuel_score > 70:
            factors.append("squeeze_fuel")
        
        if score.probability_reach > 0.8:
            factors.append("high_probability")
        
        if score.expected_return > 0.15:
            factors.append("high_return_potential")
        
        return factors