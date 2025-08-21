"""Performance tracking and logging system"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from ..utils import ScanResult, logger
from ..config import config

@dataclass
class TradeEntry:
    scan_id: int
    symbol: str
    entry_time: datetime
    entry_price: float
    target_price: Optional[float]
    stop_loss: float
    expected_return: float
    probability: float
    score: float
    reasoning: str

@dataclass
class TradeExit:
    trade_id: int
    exit_time: datetime
    exit_price: float
    actual_return: float
    outcome: str  # "target_hit", "stop_hit", "manual_exit", "time_exit"
    duration_minutes: int

@dataclass
class ScanLog:
    scan_id: int
    scan_time: datetime
    total_symbols: int
    candidates_found: int
    btc_benchmark: float
    timeframe: str
    metadata: str

class PerformanceTracker:
    """Tracks scanner performance and trade outcomes"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.PERFORMANCE_DB
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Scan logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scan_logs (
                        scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scan_time TIMESTAMP,
                        total_symbols INTEGER,
                        candidates_found INTEGER,
                        btc_benchmark REAL,
                        timeframe TEXT,
                        metadata TEXT
                    )
                ''')
                
                # Trade entries table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trade_entries (
                        trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scan_id INTEGER,
                        symbol TEXT,
                        entry_time TIMESTAMP,
                        entry_price REAL,
                        target_price REAL,
                        stop_loss REAL,
                        expected_return REAL,
                        probability REAL,
                        score REAL,
                        reasoning TEXT,
                        FOREIGN KEY (scan_id) REFERENCES scan_logs (scan_id)
                    )
                ''')
                
                # Trade exits table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trade_exits (
                        exit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trade_id INTEGER,
                        exit_time TIMESTAMP,
                        exit_price REAL,
                        actual_return REAL,
                        outcome TEXT,
                        duration_minutes INTEGER,
                        FOREIGN KEY (trade_id) REFERENCES trade_entries (trade_id)
                    )
                ''')
                
                # Model performance table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS model_performance (
                        date DATE,
                        total_trades INTEGER,
                        winning_trades INTEGER,
                        total_return REAL,
                        btc_return REAL,
                        outperformance REAL,
                        avg_score REAL,
                        avg_probability REAL
                    )
                ''')
                
                conn.commit()
                logger.info(f"Performance tracking database initialized: {self.db_path}")
                
        except Exception as e:
            logger.error(f"Error initializing performance database: {e}")
    
    def log_scan(self, results: List[ScanResult], total_symbols: int, 
                btc_benchmark: float, timeframe: str = "1h") -> int:
        """Log a scan and its results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert scan log
                scan_time = datetime.now()
                metadata = json.dumps({
                    "top_scores": [r.score for r in results[:3]],
                    "top_symbols": [r.symbol for r in results[:3]]
                })
                
                cursor.execute('''
                    INSERT INTO scan_logs 
                    (scan_time, total_symbols, candidates_found, btc_benchmark, timeframe, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (scan_time, total_symbols, len(results), btc_benchmark, timeframe, metadata))
                
                scan_id = cursor.lastrowid
                
                # Insert candidate entries
                for result in results:
                    cursor.execute('''
                        INSERT INTO trade_entries
                        (scan_id, symbol, entry_time, entry_price, target_price, stop_loss,
                         expected_return, probability, score, reasoning)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        scan_id, result.symbol, scan_time, result.current_price,
                        result.target_strike, result.stop_loss, result.expected_return,
                        result.probability_reach, result.score, result.reasoning
                    ))
                
                conn.commit()
                logger.info(f"Logged scan {scan_id} with {len(results)} candidates")
                return scan_id
                
        except Exception as e:
            logger.error(f"Error logging scan: {e}")
            return -1
    
    def log_trade_exit(self, trade_id: int, exit_price: float, outcome: str):
        """Log a trade exit"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get trade entry details
                cursor.execute('''
                    SELECT entry_time, entry_price FROM trade_entries WHERE trade_id = ?
                ''', (trade_id,))
                
                result = cursor.fetchone()
                if not result:
                    logger.error(f"Trade {trade_id} not found")
                    return
                
                entry_time, entry_price = result
                entry_time = datetime.fromisoformat(entry_time)
                
                # Calculate metrics
                exit_time = datetime.now()
                duration_minutes = int((exit_time - entry_time).total_seconds() / 60)
                actual_return = (exit_price - entry_price) / entry_price
                
                # Insert trade exit
                cursor.execute('''
                    INSERT INTO trade_exits
                    (trade_id, exit_time, exit_price, actual_return, outcome, duration_minutes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (trade_id, exit_time, exit_price, actual_return, outcome, duration_minutes))
                
                conn.commit()
                logger.info(f"Logged exit for trade {trade_id}: {actual_return:.2%} return in {duration_minutes}m")
                
        except Exception as e:
            logger.error(f"Error logging trade exit: {e}")
    
    def get_performance_stats(self, days: int = 30) -> Dict[str, float]:
        """Get performance statistics for the last N days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Get completed trades
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_trades,
                        AVG(te.actual_return) as avg_return,
                        SUM(CASE WHEN te.actual_return > 0 THEN 1 ELSE 0 END) as winning_trades,
                        AVG(tr.score) as avg_score,
                        AVG(tr.probability) as avg_probability,
                        AVG(te.duration_minutes) as avg_duration
                    FROM trade_exits te
                    JOIN trade_entries tr ON te.trade_id = tr.trade_id
                    WHERE te.exit_time > ?
                ''', (cutoff_date,))
                
                result = cursor.fetchone()
                
                if result and result[0] > 0:
                    total_trades, avg_return, winning_trades, avg_score, avg_probability, avg_duration = result
                    
                    return {
                        "total_trades": total_trades,
                        "win_rate": winning_trades / total_trades,
                        "avg_return": avg_return or 0,
                        "avg_score": avg_score or 0,
                        "avg_probability": avg_probability or 0,
                        "avg_duration_hours": (avg_duration or 0) / 60
                    }
                else:
                    return {
                        "total_trades": 0,
                        "win_rate": 0,
                        "avg_return": 0,
                        "avg_score": 0,
                        "avg_probability": 0,
                        "avg_duration_hours": 0
                    }
                    
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return {}
    
    def get_signal_effectiveness(self) -> Dict[str, Dict[str, float]]:
        """Analyze effectiveness of different signals"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Analyze by score ranges
                score_ranges = [(90, 100), (80, 90), (70, 80), (60, 70)]
                effectiveness = {}
                
                for low, high in score_ranges:
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total,
                            AVG(te.actual_return) as avg_return,
                            SUM(CASE WHEN te.actual_return > 0 THEN 1 ELSE 0 END) as winners
                        FROM trade_exits te
                        JOIN trade_entries tr ON te.trade_id = tr.trade_id
                        WHERE tr.score >= ? AND tr.score < ?
                    ''', (low, high))
                    
                    result = cursor.fetchone()
                    if result and result[0] > 0:
                        total, avg_return, winners = result
                        effectiveness[f"score_{low}_{high}"] = {
                            "total_trades": total,
                            "win_rate": winners / total,
                            "avg_return": avg_return or 0
                        }
                
                return effectiveness
                
        except Exception as e:
            logger.error(f"Error analyzing signal effectiveness: {e}")
            return {}
    
    def get_recent_scans(self, limit: int = 10) -> List[Dict]:
        """Get recent scan summaries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT scan_id, scan_time, total_symbols, candidates_found, 
                           btc_benchmark, timeframe, metadata
                    FROM scan_logs
                    ORDER BY scan_time DESC
                    LIMIT ?
                ''', (limit,))
                
                results = cursor.fetchall()
                
                scans = []
                for row in results:
                    scan_id, scan_time, total_symbols, candidates_found, btc_benchmark, timeframe, metadata = row
                    
                    scans.append({
                        "scan_id": scan_id,
                        "scan_time": scan_time,
                        "total_symbols": total_symbols,
                        "candidates_found": candidates_found,
                        "btc_benchmark": btc_benchmark,
                        "timeframe": timeframe,
                        "metadata": json.loads(metadata) if metadata else {}
                    })
                
                return scans
                
        except Exception as e:
            logger.error(f"Error getting recent scans: {e}")
            return []
    
    def cleanup_old_data(self, days: int = 90):
        """Clean up old tracking data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Delete old exits first (foreign key constraint)
                cursor.execute('''
                    DELETE FROM trade_exits 
                    WHERE trade_id IN (
                        SELECT trade_id FROM trade_entries 
                        WHERE entry_time < ?
                    )
                ''', (cutoff_date,))
                
                # Delete old entries
                cursor.execute('''
                    DELETE FROM trade_entries WHERE entry_time < ?
                ''', (cutoff_date,))
                
                # Delete old scans
                cursor.execute('''
                    DELETE FROM scan_logs WHERE scan_time < ?
                ''', (cutoff_date,))
                
                deleted_rows = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_rows} old records (older than {days} days)")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def export_performance_report(self, filename: str, days: int = 30):
        """Export detailed performance report"""
        try:
            stats = self.get_performance_stats(days)
            signal_effectiveness = self.get_signal_effectiveness()
            recent_scans = self.get_recent_scans(20)
            
            report = {
                "report_date": datetime.now().isoformat(),
                "period_days": days,
                "overall_performance": stats,
                "signal_effectiveness": signal_effectiveness,
                "recent_scans": recent_scans
            }
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Performance report exported to {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting performance report: {e}")