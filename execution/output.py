"""Output formatting and display for scan results"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from utils import ScanResult, format_percentage, format_currency
from config import config

class OutputFormatter:
    """Formats and displays scan results in various formats"""
    
    def __init__(self):
        self.console = Console()
    
    def format_json(self, results: List[ScanResult], metadata: Optional[Dict] = None) -> str:
        """Format results as JSON"""
        output = {
            "scan_timestamp": datetime.now().isoformat(),
            "total_candidates": len(results),
            "metadata": metadata or {},
            "candidates": []
        }
        
        for result in results:
            candidate = {
                "rank": result.rank,
                "symbol": result.symbol,
                "score": round(result.score, 1),
                "current_price": round(result.current_price, 2),
                "vwap": round(result.vwap, 2),
                "target_strike": round(result.target_strike, 2) if result.target_strike else None,
                "probability_reach": round(result.probability_reach, 3),
                "expected_return": round(result.expected_return, 3),
                "timeframe": result.timeframe,
                "entry_zone": {
                    "low": round(result.entry_zone[0], 2),
                    "high": round(result.entry_zone[1], 2)
                },
                "stop_loss": round(result.stop_loss, 2),
                "squeeze_factors": result.squeeze_factors,
                "reasoning": result.reasoning
            }
            output["candidates"].append(candidate)
        
        return json.dumps(output, indent=2)
    
    def format_table(self, results: List[ScanResult]) -> str:
        """Format results as a rich table"""
        if not results:
            return "No candidates found meeting the criteria."
        
        table = Table(title="🚀 Market Scanner Results", show_header=True, header_style="bold magenta")
        
        table.add_column("Rank", style="dim", width=4)
        table.add_column("Symbol", style="bold cyan", width=8)
        table.add_column("Score", style="bold green", width=6)
        table.add_column("Price", style="bold white", width=8)
        table.add_column("Target", style="bold yellow", width=8)
        table.add_column("Return", style="bold green", width=8)
        table.add_column("Prob", style="blue", width=6)
        table.add_column("Timeframe", style="dim", width=12)
        
        for result in results:
            target_str = f"${result.target_strike:.2f}" if result.target_strike else "N/A"
            return_str = format_percentage(result.expected_return)
            prob_str = f"{result.probability_reach:.0%}"
            
            table.add_row(
                str(result.rank),
                result.symbol,
                f"{result.score:.0f}",
                f"${result.current_price:.2f}",
                target_str,
                return_str,
                prob_str,
                result.timeframe
            )
        
        # Create output string
        with self.console.capture() as capture:
            self.console.print(table)
        
        return capture.get()
    
    def format_detailed(self, results: List[ScanResult]) -> str:
        """Format results with detailed information"""
        if not results:
            return "No candidates found meeting the criteria."
        
        output_lines = []
        output_lines.append("🎯 MARKET SCANNER RESULTS")
        output_lines.append("=" * 50)
        output_lines.append(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append(f"Candidates Found: {len(results)}")
        output_lines.append("")
        
        for result in results:
            output_lines.append(f"#{result.rank} {result.symbol}")
            output_lines.append("-" * 30)
            output_lines.append(f"Score: {result.score:.0f}/100")
            output_lines.append(f"Current Price: ${result.current_price:.2f}")
            output_lines.append(f"VWAP: ${result.vwap:.2f}")
            
            if result.target_strike:
                output_lines.append(f"Target Strike: ${result.target_strike:.2f}")
                move_pct = ((result.target_strike - result.current_price) / result.current_price) * 100
                output_lines.append(f"Required Move: {move_pct:+.1f}%")
            
            output_lines.append(f"Expected Return: {format_percentage(result.expected_return)}")
            output_lines.append(f"Probability: {result.probability_reach:.0%}")
            output_lines.append(f"Timeframe: {result.timeframe}")
            
            entry_low, entry_high = result.entry_zone
            output_lines.append(f"Entry Zone: ${entry_low:.2f} - ${entry_high:.2f}")
            output_lines.append(f"Stop Loss: ${result.stop_loss:.2f}")
            
            if result.squeeze_factors:
                factors = ", ".join(result.squeeze_factors)
                output_lines.append(f"Squeeze Factors: {factors}")
            
            output_lines.append(f"Reasoning: {result.reasoning}")
            output_lines.append("")
        
        return "\\n".join(output_lines)
    
    def format_trade_cards(self, results: List[ScanResult]) -> str:
        """Format results as trade cards (like your TUYA example)"""
        if not results:
            return "No trade opportunities found."
        
        cards = []
        
        for result in results:
            card_lines = []
            card_lines.append(f"🎯 TRADE CARD #{result.rank}")
            card_lines.append("=" * 25)
            card_lines.append(f"Symbol: {result.symbol}")
            card_lines.append(f"Entry: ${result.current_price:.2f}")
            
            if result.target_strike:
                card_lines.append(f"Target: ${result.target_strike:.2f}")
            
            card_lines.append(f"Stop: ${result.stop_loss:.2f}")
            card_lines.append(f"Expected Return: {format_percentage(result.expected_return)}")
            card_lines.append(f"Probability: {result.probability_reach:.0%}")
            card_lines.append(f"Timeframe: {result.timeframe}")
            card_lines.append(f"Score: {result.score:.0f}/100")
            
            if result.squeeze_factors:
                card_lines.append(f"Factors: {', '.join(result.squeeze_factors[:3])}")  # Top 3 factors
            
            cards.append("\\n".join(card_lines))
        
        return "\\n\\n".join(cards)
    
    def display_results(self, results: List[ScanResult], format_type: str = "table"):
        """Display results using rich console"""
        if format_type == "table":
            if results:
                table = self._create_rich_table(results)
                self.console.print(table)
            else:
                self.console.print("No candidates found meeting the criteria.", style="yellow")
        
        elif format_type == "detailed":
            self._display_detailed_results(results)
        
        elif format_type == "cards":
            self._display_trade_cards(results)
    
    def _create_rich_table(self, results: List[ScanResult]) -> Table:
        """Create a rich table for console display"""
        table = Table(title="🚀 Market Scanner Results", show_header=True, header_style="bold magenta")
        
        table.add_column("Rank", style="dim", width=4)
        table.add_column("Symbol", style="bold cyan", width=8)
        table.add_column("Score", style="bold green", width=6)
        table.add_column("Price", style="bold white", width=8)
        table.add_column("Target", style="bold yellow", width=8)
        table.add_column("Return", style="bold green", width=8)
        table.add_column("Prob", style="blue", width=6)
        table.add_column("Timeframe", style="dim", width=12)
        
        for result in results:
            target_str = f"${result.target_strike:.2f}" if result.target_strike else "N/A"
            return_str = format_percentage(result.expected_return)
            prob_str = f"{result.probability_reach:.0%}"
            
            # Color coding based on score
            score_style = "bold green" if result.score >= 85 else "green" if result.score >= 75 else "yellow"
            
            table.add_row(
                str(result.rank),
                result.symbol,
                f"{result.score:.0f}",
                f"${result.current_price:.2f}",
                target_str,
                return_str,
                prob_str,
                result.timeframe,
                style=score_style if result.rank == 1 else None
            )
        
        return table
    
    def _display_detailed_results(self, results: List[ScanResult]):
        """Display detailed results with rich formatting"""
        if not results:
            self.console.print("No candidates found meeting the criteria.", style="yellow")
            return
        
        for result in results:
            # Create detailed panel for each result
            details = []
            details.append(f"Score: {result.score:.0f}/100")
            details.append(f"Current: ${result.current_price:.2f} | VWAP: ${result.vwap:.2f}")
            
            if result.target_strike:
                move_pct = ((result.target_strike - result.current_price) / result.current_price) * 100
                details.append(f"Target: ${result.target_strike:.2f} ({move_pct:+.1f}%)")
            
            details.append(f"Return: {format_percentage(result.expected_return)} | Prob: {result.probability_reach:.0%}")
            details.append(f"Timeframe: {result.timeframe}")
            
            entry_low, entry_high = result.entry_zone
            details.append(f"Entry: ${entry_low:.2f}-${entry_high:.2f} | Stop: ${result.stop_loss:.2f}")
            
            if result.squeeze_factors:
                details.append(f"Factors: {', '.join(result.squeeze_factors)}")
            
            details.append(f"Reasoning: {result.reasoning}")
            
            panel_content = "\\n".join(details)
            title = f"#{result.rank} {result.symbol}"
            
            # Color based on rank
            border_style = "green" if result.rank == 1 else "blue" if result.rank <= 3 else "dim"
            
            panel = Panel(panel_content, title=title, border_style=border_style)
            self.console.print(panel)
    
    def _display_trade_cards(self, results: List[ScanResult]):
        """Display trade cards with rich formatting"""
        if not results:
            self.console.print("No trade opportunities found.", style="yellow")
            return
        
        for result in results:
            card_content = []
            card_content.append(f"[bold]Entry:[/bold] ${result.current_price:.2f}")
            
            if result.target_strike:
                card_content.append(f"[bold]Target:[/bold] ${result.target_strike:.2f}")
            
            card_content.append(f"[bold]Stop:[/bold] ${result.stop_loss:.2f}")
            card_content.append(f"[bold]Return:[/bold] {format_percentage(result.expected_return)}")
            card_content.append(f"[bold]Probability:[/bold] {result.probability_reach:.0%}")
            card_content.append(f"[bold]Timeframe:[/bold] {result.timeframe}")
            card_content.append(f"[bold]Score:[/bold] {result.score:.0f}/100")
            
            panel_content = "\\n".join(card_content)
            title = f"🎯 {result.symbol} Trade Card"
            
            # Green for top pick, blue for others
            border_style = "green" if result.rank == 1 else "blue"
            
            panel = Panel(panel_content, title=title, border_style=border_style)
            self.console.print(panel)
    
    def save_results(self, results: List[ScanResult], filename: str, format_type: str = "json"):
        """Save results to file"""
        try:
            if format_type == "json":
                content = self.format_json(results)
            elif format_type == "detailed":
                content = self.format_detailed(results)
            elif format_type == "cards":
                content = self.format_trade_cards(results)
            else:
                content = self.format_table(results)
            
            with open(filename, 'w') as f:
                f.write(content)
            
            self.console.print(f"Results saved to {filename}", style="green")
            
        except Exception as e:
            self.console.print(f"Error saving results: {e}", style="red")