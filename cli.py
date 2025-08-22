#!/usr/bin/env python3
"""
Market Scanner CLI - One-button autonomous market scanning
"""

import asyncio
import click
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from execution import MarketScanner, OutputFormatter
from tracking import PerformanceTracker
from config import config
from utils import logger, setup_logging

console = Console()

@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--config-file', help='Path to config file')
@click.pass_context
def cli(ctx, debug, config_file):
    """🚀 Autonomous Market Scanner - Find symbols guaranteed to outperform BTC"""
    ctx.ensure_object(dict)
    
    # Setup logging
    log_level = "DEBUG" if debug else config.LOG_LEVEL
    setup_logging(log_level, config.LOG_FILE)
    
    # Store context
    ctx.obj['debug'] = debug
    ctx.obj['config_file'] = config_file

@cli.command()
@click.option('--timeframe', '-t', default='1h', help='Timeframe (1h, 2h, 4h, 1d)')
@click.option('--format', '-f', default='table', 
              type=click.Choice(['table', 'json', 'detailed', 'cards']),
              help='Output format')
@click.option('--save', '-s', help='Save results to file')
@click.option('--symbols', help='Comma-separated list of symbols to scan')
@click.pass_context
def scan(ctx, timeframe, format, save, symbols):
    """🎯 Run a one-button market scan"""
    
    console.print(Panel.fit(
        "[bold cyan]🚀 Market Scanner[/bold cyan]\n"
        "[dim]Finding symbols guaranteed to outperform BTC[/dim]",
        border_style="blue"
    ))
    
    async def run_scan():
        scanner = MarketScanner()
        formatter = OutputFormatter()
        tracker = PerformanceTracker() if config.TRACK_PERFORMANCE else None
        
        try:
            # Validate setup
            console.print("🔍 Validating setup...", style="yellow")
            validation = await scanner.validate_setup()
            
            failed_checks = [k for k, v in validation.items() if not v]
            if failed_checks:
                console.print(f"⚠️  Setup issues: {', '.join(failed_checks)}", style="red")
                console.print("Continuing with available components...", style="yellow")
            
            # Parse custom symbols
            symbol_list = None
            if symbols:
                symbol_list = [s.strip().upper() for s in symbols.split(',')]
                console.print(f"📋 Custom symbols: {symbol_list}")
            
            # Run scan
            console.print(f"🔄 Scanning market (timeframe: {timeframe})...", style="blue")
            results = await scanner.run_scan(timeframe, symbol_list)
            
            # Display results
            if results:
                console.print(f"\n✅ Found {len(results)} candidates:", style="green")
                formatter.display_results(results, format)
                
                # Log to tracker
                if tracker:
                    btc_return = await scanner.composer_scorer.btc_benchmark.get_expected_return(timeframe)
                    total_symbols = len(symbol_list) if symbol_list else len(scanner.data_manager.universe.get_active_symbols())
                    scan_id = tracker.log_scan(results, total_symbols, btc_return, timeframe)
                    console.print(f"📊 Logged scan #{scan_id}", style="dim")
                
                # Save results
                if save:
                    formatter.save_results(results, save, format)
                
            else:
                console.print("❌ No candidates found meeting criteria", style="red")
                console.print("💡 Try adjusting filters or scanning different symbols", style="dim")
            
        except KeyboardInterrupt:
            console.print("\n⏹️  Scan interrupted by user", style="yellow")
        except Exception as e:
            console.print(f"💥 Error during scan: {e}", style="red")
            if ctx.obj['debug']:
                import traceback
                traceback.print_exc()
    
    # Run the async scan
    try:
        asyncio.run(run_scan())
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="blue")

@cli.command()
@click.option('--interval', '-i', default=5, help='Scan interval in minutes')
@click.option('--max-scans', '-m', default=100, help='Maximum number of scans')
@click.option('--timeframe', '-t', default='1h', help='Timeframe (1h, 2h, 4h, 1d)')
def watch(interval, max_scans, timeframe):
    """👀 Continuous market watching mode"""
    
    console.print(Panel.fit(
        f"[bold green]👀 Continuous Scanner[/bold green]\n"
        f"[dim]Interval: {interval}m | Max scans: {max_scans} | Timeframe: {timeframe}[/dim]",
        border_style="green"
    ))
    
    async def run_continuous():
        scanner = MarketScanner()
        formatter = OutputFormatter()
        
        try:
            await scanner.continuous_scan(interval, max_scans)
        except KeyboardInterrupt:
            console.print("\n⏹️  Continuous scanning stopped", style="yellow")
    
    try:
        asyncio.run(run_continuous())
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="blue")

@cli.command()
@click.argument('symbols', nargs=-1, required=True)
@click.option('--format', '-f', default='cards', 
              type=click.Choice(['table', 'json', 'detailed', 'cards']),
              help='Output format')
def quick(symbols, format):
    """⚡ Quick scan of specific symbols"""
    
    symbol_list = [s.upper() for s in symbols]
    console.print(f"⚡ Quick scan: {', '.join(symbol_list)}")
    
    async def run_quick():
        scanner = MarketScanner()
        formatter = OutputFormatter()
        
        try:
            results = await scanner.quick_scan(symbol_list)
            if results:
                formatter.display_results(results, format)
            else:
                console.print("❌ No opportunities found", style="red")
        except Exception as e:
            console.print(f"💥 Error: {e}", style="red")
    
    asyncio.run(run_quick())

@cli.command()
@click.option('--days', '-d', default=30, help='Number of days to analyze')
@click.option('--export', '-e', help='Export report to file')
def stats(days, export):
    """📊 View performance statistics"""
    
    tracker = PerformanceTracker()
    
    try:
        stats_data = tracker.get_performance_stats(days)
        
        if stats_data.get('total_trades', 0) > 0:
            console.print(Panel.fit(
                f"[bold]📊 Performance Stats ({days} days)[/bold]\n\n"
                f"Total Trades: {stats_data['total_trades']}\n"
                f"Win Rate: {stats_data['win_rate']:.1%}\n"
                f"Avg Return: {stats_data['avg_return']:.2%}\n"
                f"Avg Score: {stats_data['avg_score']:.1f}\n"
                f"Avg Duration: {stats_data['avg_duration_hours']:.1f}h",
                border_style="green"
            ))
            
            # Signal effectiveness
            effectiveness = tracker.get_signal_effectiveness()
            if effectiveness:
                console.print("\n🎯 Signal Effectiveness:")
                for score_range, data in effectiveness.items():
                    range_str = score_range.replace('_', '-').replace('score-', '')
                    console.print(f"  Score {range_str}: {data['win_rate']:.1%} win rate, {data['avg_return']:.2%} avg return")
        else:
            console.print("📊 No trade data available yet", style="yellow")
        
        if export:
            tracker.export_performance_report(export, days)
            console.print(f"📄 Report exported to {export}", style="green")
            
    except Exception as e:
        console.print(f"💥 Error getting stats: {e}", style="red")

@cli.command()
def validate():
    """🔧 Validate scanner setup and connectivity"""
    
    async def run_validation():
        scanner = MarketScanner()
        
        console.print("🔧 Validating Market Scanner Setup...\n")
        
        validation = await scanner.validate_setup()
        
        for component, status in validation.items():
            emoji = "✅" if status else "❌"
            style = "green" if status else "red"
            console.print(f"{emoji} {component.replace('_', ' ').title()}", style=style)
        
        all_good = all(validation.values())
        if all_good:
            console.print("\n🎉 All systems operational!", style="bold green")
        else:
            console.print("\n⚠️  Some components need attention", style="yellow")
            console.print("💡 Scanner will work with available components", style="dim")
    
    asyncio.run(run_validation())

@cli.command()
@click.option('--add', help='Add symbol to universe')
@click.option('--remove', help='Remove symbol from universe')
@click.option('--list', 'list_symbols', is_flag=True, help='List current symbols')
@click.option('--load', help='Load symbols from CSV file')
def universe(add, remove, list_symbols, load):
    """🌌 Manage symbol universe"""
    
    from data import UniverseManager
    
    universe_manager = UniverseManager()
    
    if add:
        universe_manager.add_symbol(add.upper())
        console.print(f"✅ Added {add.upper()} to universe", style="green")
    
    elif remove:
        universe_manager.remove_symbol(remove.upper())
        console.print(f"🗑️  Removed {remove.upper()} from universe", style="yellow")
    
    elif load:
        symbols = universe_manager.load_symbols_from_file(load)
        console.print(f"📂 Loaded {len(symbols)} symbols from {load}", style="green")
    
    elif list_symbols:
        symbols = universe_manager.get_active_symbols()
        console.print(f"🌌 Current universe ({len(symbols)} symbols):")
        for i, symbol in enumerate(symbols, 1):
            console.print(f"  {i:3d}. {symbol}")
    
    else:
        symbols = universe_manager.get_active_symbols()
        console.print(f"🌌 Universe contains {len(symbols)} symbols")
        console.print("Use --list to see all symbols")

@cli.command()
@click.option('--host', default='127.0.0.1', help='API server host')
@click.option('--port', default=8888, help='API server port')
def api(host, port):
    """🌐 Start REST API server for Claude integration"""
    
    console.print(Panel.fit(
        f"[bold green]🌐 Starting API Server[/bold green]\n"
        f"[dim]Host: {host}:{port}[/dim]\n"
        f"[dim]Docs: http://{host}:{port}/docs[/dim]",
        border_style="green"
    ))
    
    from api import run_server
    
    try:
        run_server(host=host, port=port)
    except KeyboardInterrupt:
        console.print("\n⏹️  API server stopped", style="yellow")

@cli.command()
def version():
    """📋 Show version information"""
    
    __version__ = "1.0.0"
    
    console.print(Panel.fit(
        f"[bold cyan]🚀 Market Scanner[/bold cyan]\n"
        f"Version: {__version__}\n"
        f"Platform: macOS\n"
        f"Python: {sys.version.split()[0]}\n"
        f"API: http://127.0.0.1:8888",
        border_style="blue"
    ))

def main():
    """Main entry point for the CLI"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="blue")
    except Exception as e:
        console.print(f"💥 Fatal error: {e}", style="red")
        sys.exit(1)

if __name__ == '__main__':
    main()