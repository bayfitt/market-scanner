"""Main scanner orchestrator - coordinates all components"""

import asyncio
import time
from datetime import datetime
from typing import List, Optional, Dict

from data import DataManager
from scoring import CompositeScorer
from utils import ScanResult, MarketData, logger
from config import config

class MarketScanner:
    """Main scanner that orchestrates the entire scanning process"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.composer_scorer = CompositeScorer()
        self.last_scan_time = None
        self.scan_count = 0
        
    async def run_scan(self, timeframe: str = "1h", 
                      custom_symbols: Optional[List[str]] = None) -> List[ScanResult]:
        """Execute a complete market scan"""
        scan_start = time.time()
        self.scan_count += 1
        
        logger.info(f"Starting scan #{self.scan_count} (timeframe: {timeframe})")
        
        try:
            # Step 1: Get symbol universe
            if custom_symbols:
                symbols = [s.upper().strip() for s in custom_symbols]
                logger.info(f"Using custom symbols: {symbols}")
            else:
                symbols = self.data_manager.universe.get_active_symbols()
                logger.info(f"Scanning {len(symbols)} symbols from universe")
            
            # Step 2: Fetch market data for all symbols
            market_data_list = await self._fetch_market_data(symbols)
            if not market_data_list:
                logger.warning("No market data available")
                return []
            
            logger.info(f"Retrieved data for {len(market_data_list)} symbols")
            
            # Step 3: Apply basic filters
            filtered_data = self._apply_basic_filters(market_data_list)
            logger.info(f"After basic filters: {len(filtered_data)} symbols")
            
            if not filtered_data:
                logger.warning("No symbols passed basic filters")
                return []
            
            # Step 4: Score all symbols
            scores = await self.composer_scorer.score_multiple_symbols(filtered_data, timeframe)
            logger.info(f"Scored {len(scores)} symbols")
            
            # Step 5: Filter and rank by composite score
            top_scores = self.composer_scorer.filter_and_rank(scores)
            logger.info(f"Top candidates after ranking: {len(top_scores)}")
            
            # Step 6: Convert to scan results
            market_data_dict = {md.symbol: md for md in filtered_data}
            results = self.composer_scorer.create_scan_results(top_scores, market_data_dict)
            
            # Step 7: Log scan completion
            scan_duration = time.time() - scan_start
            self.last_scan_time = datetime.now()
            
            logger.info(f"Scan #{self.scan_count} completed in {scan_duration:.2f}s. "
                       f"Found {len(results)} candidates")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during scan: {e}")
            return []
    
    async def _fetch_market_data(self, symbols: List[str]) -> List[MarketData]:
        """Fetch market data for all symbols concurrently"""
        tasks = []
        
        # Batch symbols to avoid overwhelming the API
        batch_size = 10
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            for symbol in batch:
                task = self.data_manager.get_market_data(symbol)
                tasks.append(task)
            
            # Small delay between batches
            if i + batch_size < len(symbols):
                await asyncio.sleep(0.5)
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        market_data = []
        for i, result in enumerate(results):
            if isinstance(result, MarketData):
                market_data.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Failed to fetch data for {symbols[i % len(symbols)]}: {result}")
            # None results are skipped silently
        
        return market_data
    
    def _apply_basic_filters(self, market_data_list: List[MarketData]) -> List[MarketData]:
        """Apply basic filters before expensive scoring"""
        filtered = []
        
        for data in market_data_list:
            # Price filters
            if data.price < config.MIN_PRICE or data.price > config.MAX_PRICE:
                logger.debug(f"Filtered {data.symbol}: Price ${data.price:.2f} outside range")
                continue
            
            # Volume filter (basic check)
            if data.volume <= 0:
                logger.debug(f"Filtered {data.symbol}: No volume")
                continue
            
            # Sanity checks
            if data.high <= 0 or data.low <= 0 or data.open <= 0:
                logger.debug(f"Filtered {data.symbol}: Invalid OHLC data")
                continue
            
            # Check for halted/suspended stocks (price == high == low)
            if data.high == data.low == data.price and data.volume < 1000:
                logger.debug(f"Filtered {data.symbol}: Appears halted")
                continue
            
            filtered.append(data)
        
        return filtered
    
    async def quick_scan(self, target_symbols: List[str]) -> List[ScanResult]:
        """Quick scan of specific symbols (bypass universe)"""
        logger.info(f"Quick scan of {len(target_symbols)} symbols")
        return await self.run_scan(custom_symbols=target_symbols)
    
    async def continuous_scan(self, interval_minutes: int = 5, max_iterations: int = 100):
        """Run continuous scanning at specified intervals"""
        logger.info(f"Starting continuous scan (interval: {interval_minutes}m, max: {max_iterations})")
        
        for iteration in range(max_iterations):
            try:
                results = await self.run_scan()
                
                if results:
                    logger.info(f"Continuous scan #{iteration + 1}: Found {len(results)} candidates")
                    for result in results:
                        logger.info(f"  {result.rank}. {result.symbol} - Score: {result.score:.0f}, "
                                  f"Target: ${result.target_strike:.2f if result.target_strike else 0:.2f}")
                else:
                    logger.info(f"Continuous scan #{iteration + 1}: No candidates found")
                
                # Wait for next iteration
                if iteration < max_iterations - 1:
                    await asyncio.sleep(interval_minutes * 60)
                    
            except KeyboardInterrupt:
                logger.info("Continuous scan interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous scan iteration {iteration + 1}: {e}")
                await asyncio.sleep(30)  # Short delay before retry
    
    def get_scan_stats(self) -> Dict[str, any]:
        """Get statistics about scanning performance"""
        return {
            "total_scans": self.scan_count,
            "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None,
            "universe_size": len(self.data_manager.universe.get_active_symbols()),
            "cache_status": "active" if hasattr(self.data_manager, 'redis_client') else "disabled"
        }
    
    async def validate_setup(self) -> Dict[str, bool]:
        """Validate scanner setup and connectivity"""
        validation = {
            "redis_connection": False,
            "data_feed": False,
            "btc_benchmark": False,
            "symbol_universe": False
        }
        
        try:
            # Test Redis connection
            self.data_manager.universe.redis_client.ping()
            validation["redis_connection"] = True
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
        
        try:
            # Test data feed
            test_data = await self.data_manager.get_market_data("AAPL")
            validation["data_feed"] = test_data is not None
        except Exception as e:
            logger.warning(f"Data feed test failed: {e}")
        
        try:
            # Test BTC benchmark
            btc_return = await self.composer_scorer.btc_benchmark.get_expected_return()
            validation["btc_benchmark"] = btc_return > 0
        except Exception as e:
            logger.warning(f"BTC benchmark test failed: {e}")
        
        try:
            # Test symbol universe
            symbols = self.data_manager.universe.get_active_symbols()
            validation["symbol_universe"] = len(symbols) > 0
        except Exception as e:
            logger.warning(f"Symbol universe test failed: {e}")
        
        return validation