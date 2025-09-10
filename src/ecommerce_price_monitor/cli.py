"""Command-line interface for the e-commerce price monitoring system."""

import click
import json
import sys
from pathlib import Path
from typing import List, Optional

from .collectors.price_collector import PriceCollector
from .analyzers.price_analyzer import PriceAnalyzer
from .visualizers.price_visualizer import PriceVisualizer
from .exporters.data_exporter import DataExporter
from .utils.logging_config import setup_logging, setup_colored_logging
from .utils.exceptions import PriceMonitorError


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--quiet', '-q', is_flag=True, help='Suppress console output')
@click.option('--log-file', help='Log file path')
def cli(verbose: bool, quiet: bool, log_file: Optional[str]):
    """E-commerce Price Monitoring and Analysis System.
    
    A comprehensive tool for collecting, analyzing, and visualizing
    e-commerce price data from multiple platforms.
    """
    if quiet:
        log_level = "ERROR"
        console_output = False
    elif verbose:
        log_level = "DEBUG"
        console_output = True
    else:
        log_level = "INFO"
        console_output = True
    
    if log_file:
        setup_logging(
            log_level=log_level,
            log_dir=Path(log_file).parent,
            console_output=console_output,
            file_output=True
        )
    else:
        setup_colored_logging(log_level)


@cli.command()
@click.option('--query', '-q', required=True, help='Search query')
@click.option('--platforms', '-p', multiple=True, 
              help='Platforms to search (amazon, ebay, walmart)')
@click.option('--max-results', '-n', default=20, type=int,
              help='Maximum results per platform')
@click.option('--output', '-o', help='Output file path')
@click.option('--format', '-f', 'output_format', default='csv',
              type=click.Choice(['csv', 'json', 'excel']),
              help='Output format')
def search(query: str, platforms: tuple, max_results: int, 
           output: Optional[str], output_format: str):
    """Search for products across e-commerce platforms."""
    try:
        click.echo(f"[*] Searching for '{query}' across platforms...")
        
        # Initialize collector
        platform_list = list(platforms) if platforms else None
        collector = PriceCollector(platforms=platform_list)
        
        # Search products
        results = collector.search_all_platforms(
            query=query,
            max_results_per_platform=max_results,
            use_parallel=True
        )
        
        # Display results summary
        total_products = sum(len(products) for products in results.values())
        click.echo(f"[+] Found {total_products} products across {len(results)} platforms")
        
        for platform, products in results.items():
            if products:
                avg_price = sum(p.price for p in products if p.price > 0) / len([p for p in products if p.price > 0])
                click.echo(f"  -> {platform}: {len(products)} products (avg: ${avg_price:.2f})")
        
        # Export results if requested
        if output:
            all_products = []
            for products in results.values():
                all_products.extend(products)
            
            exporter = DataExporter()
            file_path = exporter.export_data(
                all_products, 
                output_format, 
                Path(output).stem,
                Path(output).parent
            )
            click.echo(f"[S] Results exported to: {file_path}")
        
        collector.close()
        
    except Exception as e:
        click.echo(f"[-] Error during search: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', default='data/reports',
              help='Output directory for reports')
@click.option('--formats', '-f', multiple=True, 
              default=['html', 'markdown'],
              type=click.Choice(['csv', 'excel', 'json', 'markdown', 'html']),
              help='Export formats')
@click.option('--charts', '-c', is_flag=True, help='Generate charts')
def analyze(input_file: str, output_dir: str, formats: tuple, charts: bool):
    """Analyze price data from a file."""
    try:
        click.echo(f"📊 Analyzing data from {input_file}...")
        
        # Load data
        if input_file.endswith('.json'):
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Convert to ProductData if needed
            # This is simplified - in real implementation you'd reconstruct ProductData objects
            click.echo("⚠️  JSON analysis not fully implemented")
            return
        
        elif input_file.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(input_file)
        
        else:
            click.echo("❌ Unsupported file format", err=True)
            sys.exit(1)
        
        # Perform analysis
        analyzer = PriceAnalyzer()
        results = analyzer.analyze(df)
        
        click.echo("✅ Analysis completed")
        click.echo(f"  📈 Analyzed {results.metadata.get('total_products', 0)} products")
        click.echo(f"  🏪 Across {len(results.metadata.get('platforms', []))} platforms")
        
        # Export results
        exporter = DataExporter()
        exported_files = exporter.export_multiple_formats(
            results,
            list(formats),
            "price_analysis",
            output_dir
        )
        
        for format_name, file_path in exported_files.items():
            if file_path:
                click.echo(f"💾 {format_name.upper()}: {file_path}")
        
        # Generate charts if requested
        if charts:
            click.echo("📊 Generating visualization charts...")
            visualizer = PriceVisualizer()
            
            try:
                # Create dashboard
                dashboard = visualizer.create_dashboard(df)
                chart_path = visualizer.save_chart(
                    dashboard, 
                    "price_dashboard", 
                    "html",
                    output_dir
                )
                click.echo(f"📈 Dashboard: {chart_path}")
                
            except Exception as e:
                click.echo(f"⚠️  Chart generation failed: {e}")
        
    except Exception as e:
        click.echo(f"❌ Error during analysis: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('urls_file', type=click.Path(exists=True))
@click.option('--interval', '-i', default=24, type=int,
              help='Check interval in hours')
@click.option('--output-dir', '-o', default='data/monitoring',
              help='Output directory')
def monitor(urls_file: str, interval: int, output_dir: str):
    """Monitor product prices from a list of URLs."""
    try:
        click.echo(f"👀 Starting price monitoring (interval: {interval}h)")
        
        # Load URLs
        with open(urls_file, 'r', encoding='utf-8') as f:
            urls = {}
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if ',' in line:
                        name, url = line.split(',', 1)
                        urls[name.strip()] = url.strip()
                    else:
                        urls[line] = line
        
        click.echo(f"📝 Loaded {len(urls)} URLs to monitor")
        
        # Initialize collector
        collector = PriceCollector()
        
        # Monitor products (single check for now)
        results = collector.monitor_products(urls)
        
        if results:
            click.echo(f"✅ Monitored {len(results)} products:")
            
            for product_name, product_data in results.items():
                click.echo(f"  💰 {product_name}: ${product_data.price:.2f} ({product_data.platform})")
            
            # Export results
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            exporter = DataExporter()
            
            products_list = list(results.values())
            file_path = exporter.export_data(
                products_list,
                'csv',
                f"monitoring_results",
                output_dir
            )
            
            click.echo(f"💾 Results saved to: {file_path}")
        
        collector.close()
        
    except Exception as e:
        click.echo(f"❌ Error during monitoring: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('data_file', type=click.Path(exists=True))
@click.option('--chart-type', '-t', 
              type=click.Choice(['price_distribution', 'platform_comparison', 
                               'price_trend', 'scatter_analysis', 'heatmap', 'box_plot']),
              default='price_distribution',
              help='Type of chart to generate')
@click.option('--output', '-o', help='Output file path')
@click.option('--format', '-f', 'output_format', default='html',
              type=click.Choice(['png', 'html', 'svg', 'pdf']),
              help='Chart format')
def visualize(data_file: str, chart_type: str, output: Optional[str], output_format: str):
    """Generate visualizations from price data."""
    try:
        click.echo(f"📊 Creating {chart_type} chart from {data_file}...")
        
        # Load data
        if data_file.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(data_file)
        else:
            click.echo("❌ Only CSV files are supported for visualization", err=True)
            sys.exit(1)
        
        # Create visualization
        visualizer = PriceVisualizer()
        chart = visualizer.create_chart(df, chart_type=chart_type)
        
        # Save chart
        if output:
            output_path = Path(output)
            file_path = visualizer.save_chart(
                chart,
                output_path.stem,
                output_format,
                str(output_path.parent)
            )
        else:
            file_path = visualizer.save_chart(
                chart,
                f"{chart_type}_chart",
                output_format
            )
        
        click.echo(f"✅ Chart saved to: {file_path}")
        
    except Exception as e:
        click.echo(f"❌ Error creating visualization: {e}", err=True)
        sys.exit(1)


@cli.command()
def version():
    """Show version information."""
    from . import __version__
    click.echo(f"E-commerce Price Monitor v{__version__}")
    click.echo("A comprehensive price monitoring and analysis system")


@cli.command()
def config():
    """Show current configuration."""
    try:
        from .config import config_manager
        config = config_manager.load_config()
        
        click.echo("📋 Current Configuration:")
        click.echo(f"  Supported platforms: {', '.join(config.supported_platforms)}")
        click.echo(f"  Export formats: {', '.join(config.export_formats)}")
        click.echo(f"  Request delay: {config.scraping.request_delay}s")
        click.echo(f"  Retry attempts: {config.scraping.retry_attempts}")
        
    except Exception as e:
        click.echo(f"❌ Error loading configuration: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n👋 Goodbye!")
        sys.exit(0)
    except PriceMonitorError as e:
        click.echo(f"❌ {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()