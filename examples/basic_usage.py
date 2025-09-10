"""
Basic usage examples for the e-commerce price monitoring system.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecommerce_price_monitor import PriceCollector, PriceAnalyzer, PriceVisualizer, DataExporter


def example_1_basic_search():
    """Example 1: Basic product search across platforms."""
    print("🔍 Example 1: Basic Product Search")
    print("=" * 50)
    
    # Initialize collector for international platforms
    print("🌍 Searching international platforms...")
    collector_intl = PriceCollector(platforms=['amazon', 'ebay'])
    
    # Search for products
    query_intl = "wireless headphones"
    results_intl = collector_intl.search_all_platforms(
        query=query_intl,
        max_results_per_platform=5,
        use_parallel=True
    )
    
    # Initialize collector for Chinese platforms
    print("🇨🇳 Searching Chinese platforms...")
    collector_cn = PriceCollector(platforms=['jd', 'taobao'])
    
    query_cn = "无线耳机"
    results_cn = collector_cn.search_all_platforms(
        query=query_cn,
        max_results_per_platform=5,
        use_parallel=True
    )
    
    # Combine results
    results = {**results_intl, **results_cn}
    
    # Display results
    for platform, products in results.items():
        print(f"\n📦 {platform.upper()}: {len(products)} products found")
        
        for i, product in enumerate(products[:3], 1):  # Show first 3
            print(f"  {i}. {product.name[:60]}...")
            print(f"     💰 ${product.price:.2f}")
            if product.rating:
                print(f"     ⭐ {product.rating}/5.0")
    
    collector_intl.close()
    collector_cn.close()
    print("\n✅ Search completed!")


def example_2_data_analysis():
    """Example 2: Price data analysis."""
    print("\n📊 Example 2: Price Data Analysis")
    print("=" * 50)
    
    # For this example, we'll create sample data
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Create sample data
    sample_data = []
    platforms = ['Amazon', 'eBay', 'Walmart']
    products = ['iPhone 15', 'MacBook Air', 'AirPods Pro', 'iPad Air']
    
    for i in range(50):
        sample_data.append({
            'platform': platforms[i % 3],
            'name': f"{products[i % 4]} Model {i}",
            'price': 100 + (i * 23.5) % 1200,
            'rating': 3.5 + (i % 3) * 0.5,
            'review_count': 50 + i * 10,
            'timestamp': datetime.now() - timedelta(days=i % 30)
        })
    
    df = pd.DataFrame(sample_data)
    
    # Perform analysis
    analyzer = PriceAnalyzer()
    results = analyzer.analyze(df)
    
    # Display analysis results
    print(f"\n📈 Analysis Results:")
    print(f"  • Total products analyzed: {results.metadata['total_products']}")
    print(f"  • Platforms: {', '.join(results.metadata['platforms'])}")
    print(f"  • Price range: ${results.metadata['price_range']['min']:.2f} - ${results.metadata['price_range']['max']:.2f}")
    
    # Show overview stats
    overview = results.data.get('overview', {})
    if 'price_stats' in overview:
        stats = overview['price_stats']
        print(f"\n💰 Price Statistics:")
        print(f"  • Average: ${stats['average']:.2f}")
        print(f"  • Median: ${stats['median']:.2f}")
        print(f"  • Standard deviation: ${stats['std']:.2f}")
    
    # Show platform comparison
    if 'platform_comparison' in results.data:
        print(f"\n🏪 Platform Comparison:")
        for platform, stats in results.data['platform_comparison'].items():
            if isinstance(stats, dict) and 'average_price' in stats:
                print(f"  • {platform}: ${stats['average_price']:.2f} avg ({stats['product_count']} products)")
    
    print("\n✅ Analysis completed!")


def example_3_visualization():
    """Example 3: Create visualizations."""
    print("\n📊 Example 3: Data Visualization")
    print("=" * 50)
    
    # Create sample data for visualization
    import pandas as pd
    import numpy as np
    
    np.random.seed(42)
    
    # Generate realistic sample data
    data = []
    platforms = ['Amazon', 'eBay', 'Walmart']
    
    for platform in platforms:
        n_products = 30
        base_price = {'Amazon': 200, 'eBay': 180, 'Walmart': 190}[platform]
        
        for i in range(n_products):
            price = base_price + np.random.normal(0, 50)
            price = max(price, 10)  # Ensure positive price
            
            data.append({
                'platform': platform,
                'name': f'Product {i+1}',
                'price': price,
                'rating': np.random.uniform(3.0, 5.0),
                'review_count': np.random.randint(10, 1000),
                'timestamp': pd.Timestamp.now()
            })
    
    df = pd.DataFrame(data)
    
    # Create visualizations
    visualizer = PriceVisualizer()
    
    print("📈 Creating price distribution chart...")
    try:
        chart1 = visualizer.create_chart(df, chart_type='price_distribution')
        path1 = visualizer.save_chart(chart1, "price_distribution", "html", "examples/output")
        print(f"  ✅ Saved to: {path1}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print("📊 Creating platform comparison chart...")
    try:
        chart2 = visualizer.create_chart(df, chart_type='platform_comparison')
        path2 = visualizer.save_chart(chart2, "platform_comparison", "html", "examples/output")
        print(f"  ✅ Saved to: {path2}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print("📋 Creating comprehensive dashboard...")
    try:
        dashboard = visualizer.create_dashboard(df)
        dashboard_path = visualizer.save_chart(dashboard, "comprehensive_dashboard", "html", "examples/output")
        print(f"  ✅ Dashboard saved to: {dashboard_path}")
    except Exception as e:
        print(f"  ❌ Dashboard error: {e}")
    
    print("\n✅ Visualization completed!")


def example_4_export_data():
    """Example 4: Export data in multiple formats."""
    print("\n💾 Example 4: Data Export")
    print("=" * 50)
    
    # Create sample analysis results
    import pandas as pd
    
    # Sample product data
    sample_products = []
    for i in range(20):
        sample_products.append({
            'platform': ['Amazon', 'eBay', 'Walmart'][i % 3],
            'name': f'Sample Product {i+1}',
            'price': 50 + i * 15.5,
            'rating': 3.5 + (i % 3) * 0.5,
            'review_count': 100 + i * 25
        })
    
    df = pd.DataFrame(sample_products)
    
    # Initialize exporter
    exporter = DataExporter()
    
    print("📄 Exporting data in multiple formats...")
    
    # Export in different formats
    formats = ['csv', 'excel', 'json', 'markdown', 'html']
    results = exporter.export_multiple_formats(
        df,
        formats,
        "sample_export",
        "examples/output"
    )
    
    # Display export results
    for format_name, file_path in results.items():
        if file_path:
            print(f"  ✅ {format_name.upper()}: {file_path}")
        else:
            print(f"  ❌ {format_name.upper()}: Export failed")
    
    print("\n✅ Export completed!")


def example_5_comprehensive_workflow():
    """Example 5: Complete workflow from search to report."""
    print("\n🔄 Example 5: Complete Workflow")
    print("=" * 50)
    
    try:
        # Step 1: Data collection (simulated)
        print("1️⃣ Collecting product data...")
        
        # Create realistic sample data instead of actual scraping
        import pandas as pd
        import numpy as np
        from datetime import datetime
        
        np.random.seed(42)
        
        data = []
        platforms = ['Amazon', 'eBay', 'Walmart']
        product_names = [
            'iPhone 15 Pro Max', 'Samsung Galaxy S24', 'Google Pixel 8',
            'MacBook Air M3', 'Dell XPS 13', 'HP Spectre x360',
            'iPad Air 5th Gen', 'Surface Pro 9', 'Galaxy Tab S9',
            'AirPods Pro 2', 'Sony WH-1000XM5', 'Bose QuietComfort'
        ]
        
        for i, name in enumerate(product_names * 5):  # 60 products total
            platform = platforms[i % 3]
            base_price = np.random.uniform(200, 1500)
            
            data.append({
                'platform': platform,
                'product_id': f'PROD_{i:03d}',
                'name': f'{name} - Model {i}',
                'price': base_price,
                'currency': 'USD',
                'availability': np.random.choice(['Available', 'Out of Stock'], p=[0.8, 0.2]),
                'rating': np.random.uniform(3.0, 5.0),
                'review_count': np.random.randint(50, 5000),
                'brand': name.split()[0],
                'category': 'Electronics',
                'timestamp': datetime.now()
            })
        
        df = pd.DataFrame(data)
        print(f"   📦 Collected {len(df)} products from {df['platform'].nunique()} platforms")
        
        # Step 2: Analysis
        print("2️⃣ Analyzing price data...")
        analyzer = PriceAnalyzer()
        analysis_results = analyzer.analyze(df)
        
        overview = analysis_results.data.get('overview', {})
        print(f"   📊 Average price: ${overview.get('price_stats', {}).get('average', 0):.2f}")
        print(f"   📈 Price range: ${overview.get('price_stats', {}).get('min', 0):.2f} - ${overview.get('price_stats', {}).get('max', 0):.2f}")
        
        # Step 3: Visualization
        print("3️⃣ Creating visualizations...")
        visualizer = PriceVisualizer()
        dashboard = visualizer.create_dashboard(df)
        viz_path = visualizer.save_chart(dashboard, "workflow_dashboard", "html", "examples/output")
        print(f"   📊 Dashboard: {viz_path}")
        
        # Step 4: Export reports
        print("4️⃣ Generating reports...")
        exporter = DataExporter()
        
        # Export analysis results
        report_paths = exporter.export_multiple_formats(
            analysis_results,
            ['html', 'markdown', 'json'],
            "comprehensive_report",
            "examples/output"
        )
        
        # Export raw data
        data_paths = exporter.export_multiple_formats(
            df,
            ['csv', 'excel'],
            "product_data",
            "examples/output"
        )
        
        print("   📄 Reports generated:")
        for format_name, path in {**report_paths, **data_paths}.items():
            if path:
                print(f"      • {format_name.upper()}: {path}")
        
        print("\n🎉 Complete workflow finished successfully!")
        print("\n📂 Check the 'examples/output' directory for all generated files.")
        
    except Exception as e:
        print(f"❌ Workflow error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all examples."""
    print("🛒 E-commerce Price Monitor - Examples")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path("examples/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Run examples (commenting out actual web scraping for demo)
        # example_1_basic_search()  # Uncomment to test actual web scraping
        example_2_data_analysis()
        example_3_visualization()
        example_4_export_data()
        example_5_comprehensive_workflow()
        
        print("\n🎉 All examples completed successfully!")
        print(f"📁 Output files saved to: {output_dir.absolute()}")
        
    except KeyboardInterrupt:
        print("\n👋 Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()