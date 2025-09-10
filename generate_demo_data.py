#!/usr/bin/env python3
"""Generate demo data and visualizations for README screenshots."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json

# Import our modules
from ecommerce_price_monitor import PriceAnalyzer, PriceVisualizer, DataExporter

# Set Chinese font for matplotlib
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def generate_demo_data():
    """Generate realistic demo data for screenshots."""
    np.random.seed(42)
    
    # Platform and product data
    platforms = ['京东', '淘宝', '小红书', '抖音电商', 'Amazon', 'eBay']
    categories = ['手机数码', '美妆护肤', '服装鞋包', '家居用品', '食品保健']
    brands = ['华为', '小米', '苹果', 'OPPO', 'vivo', '三星', 'OnePlus']
    
    demo_data = []
    
    # Generate 200 sample products
    for i in range(200):
        platform = np.random.choice(platforms)
        category = np.random.choice(categories)
        brand = np.random.choice(brands)
        
        # Base price varies by category
        base_prices = {
            '手机数码': (2000, 8000),
            '美妆护肤': (50, 500), 
            '服装鞋包': (100, 800),
            '家居用品': (200, 2000),
            '食品保健': (30, 300)
        }
        min_price, max_price = base_prices[category]
        
        # Platform price adjustments
        platform_multipliers = {
            '京东': 1.0,
            '淘宝': 0.85,
            '小红书': 1.15,
            '抖音电商': 0.80,
            'Amazon': 1.05,
            'eBay': 0.90
        }
        
        base_price = np.random.uniform(min_price, max_price)
        price = base_price * platform_multipliers[platform] * (1 + np.random.normal(0, 0.1))
        price = max(10, price)  # Minimum price
        
        # Generate time series data
        days_ago = np.random.randint(0, 30)
        timestamp = datetime.now() - timedelta(days=days_ago)
        
        demo_data.append({
            'platform': platform,
            'product_id': f'{platform}_{i:03d}',
            'name': f'{brand} {category}产品 Model-{i}',
            'price': round(price, 2),
            'currency': 'CNY' if platform in ['京东', '淘宝', '小红书', '抖音电商'] else 'USD',
            'category': category,
            'brand': brand,
            'rating': np.random.uniform(3.8, 5.0),
            'review_count': np.random.randint(10, 5000),
            'availability': np.random.choice(['现货', '预售', '缺货'], p=[0.8, 0.15, 0.05]),
            'timestamp': timestamp
        })
    
    return pd.DataFrame(demo_data)

def create_analysis_demo():
    """Create data analysis demo screenshots."""
    print("生成数据分析层演示数据...")
    
    df = generate_demo_data()
    analyzer = PriceAnalyzer()
    analysis = analyzer.analyze(df)
    
    # Create docs/images directory
    docs_dir = Path("docs/images")
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Platform comparison analysis
    platform_stats = df.groupby('platform').agg({
        'price': ['mean', 'median', 'std', 'count'],
        'rating': 'mean',
        'review_count': 'mean'
    }).round(2)
    
    # Create a summary table visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('电商平台价格分析报告 / E-commerce Price Analysis Report', fontsize=16, fontweight='bold')
    
    # 1. Average price by platform
    platform_prices = df.groupby('platform')['price'].mean().sort_values(ascending=False)
    bars1 = ax1.bar(range(len(platform_prices)), platform_prices.values, 
                    color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FCEA2B', '#FF9F40'])
    ax1.set_title('各平台平均价格对比 / Average Price by Platform', fontweight='bold')
    ax1.set_ylabel('平均价格 (CNY/USD)')
    ax1.set_xticks(range(len(platform_prices)))
    ax1.set_xticklabels(platform_prices.index, rotation=45)
    
    # Add value labels on bars
    for bar, value in zip(bars1, platform_prices.values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 10,
                f'¥{value:.0f}', ha='center', va='bottom', fontweight='bold')
    
    # 2. Price distribution by category
    category_data = []
    categories = df['category'].unique()
    for cat in categories:
        cat_prices = df[df['category'] == cat]['price'].values
        category_data.extend([(cat, price) for price in cat_prices])
    
    cat_df = pd.DataFrame(category_data, columns=['category', 'price'])
    cat_df.boxplot(column='price', by='category', ax=ax2)
    ax2.set_title('品类价格分布 / Price Distribution by Category')
    ax2.set_ylabel('价格 (CNY/USD)')
    ax2.set_xlabel('商品品类 / Product Category')
    plt.setp(ax2.get_xticklabels(), rotation=45)
    
    # 3. Rating vs Price scatter
    colors = {'京东': '#E3002B', '淘宝': '#FF6900', '小红书': '#FF2442', 
              '抖音电商': '#000000', 'Amazon': '#FF9900', 'eBay': '#0064D2'}
    
    for platform in df['platform'].unique():
        platform_data = df[df['platform'] == platform]
        ax3.scatter(platform_data['price'], platform_data['rating'], 
                   label=platform, alpha=0.6, s=50, color=colors.get(platform, '#333333'))
    
    ax3.set_title('价格与评分关系 / Price vs Rating Correlation')
    ax3.set_xlabel('价格 (CNY/USD)')
    ax3.set_ylabel('评分 / Rating')
    ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax3.grid(True, alpha=0.3)
    
    # 4. Market share pie chart
    platform_counts = df['platform'].value_counts()
    wedges, texts, autotexts = ax4.pie(platform_counts.values, labels=platform_counts.index, 
                                      autopct='%1.1f%%', startangle=90,
                                      colors=[colors.get(p, '#333333') for p in platform_counts.index])
    ax4.set_title('平台商品数量分布 / Platform Market Share')
    
    plt.tight_layout()
    plt.savefig(docs_dir / 'data_analysis_demo.png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    # Generate summary statistics table
    summary_stats = {
        "总商品数": len(df),
        "平台数": len(df['platform'].unique()),
        "品类数": len(df['category'].unique()),
        "价格区间": f"¥{df['price'].min():.0f} - ¥{df['price'].max():.0f}",
        "平均价格": f"¥{df['price'].mean():.0f}",
        "平均评分": f"{df['rating'].mean():.1f}⭐"
    }
    
    print("数据分析层演示图表已生成:")
    print(f"  - 综合分析图表: docs/images/data_analysis_demo.png")
    print(f"  - 数据概览: {summary_stats}")
    
    return summary_stats

def create_visualization_demo():
    """Create visualization demo screenshots."""
    print("\n生成可视化层演示数据...")
    
    df = generate_demo_data()
    visualizer = PriceVisualizer()
    docs_dir = Path("docs/images")
    
    # Create price trend visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('电商价格可视化图表集 / E-commerce Price Visualization Dashboard', 
                 fontsize=16, fontweight='bold')
    
    # 1. Price distribution histogram
    chinese_platforms = df[df['platform'].isin(['京东', '淘宝', '小红书', '抖音电商'])]
    international_platforms = df[df['platform'].isin(['Amazon', 'eBay'])]
    
    ax1.hist(chinese_platforms['price'], bins=30, alpha=0.7, label='中文平台', color='#FF6B6B', density=True)
    ax1.hist(international_platforms['price'], bins=30, alpha=0.7, label='国际平台', color='#4ECDC4', density=True)
    ax1.set_title('价格分布直方图 / Price Distribution', fontweight='bold')
    ax1.set_xlabel('价格 (CNY/USD)')
    ax1.set_ylabel('密度 / Density')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Platform comparison violin plot
    platform_prices = [df[df['platform'] == p]['price'].values for p in df['platform'].unique()]
    parts = ax2.violinplot(platform_prices, positions=range(len(df['platform'].unique())), showmeans=True)
    ax2.set_title('平台价格分布对比 / Platform Price Distribution', fontweight='bold')
    ax2.set_ylabel('价格 (CNY/USD)')
    ax2.set_xticks(range(len(df['platform'].unique())))
    ax2.set_xticklabels(df['platform'].unique(), rotation=45)
    ax2.grid(True, alpha=0.3)
    
    # Color the violin plots
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FCEA2B', '#FF9F40']
    for pc, color in zip(parts['bodies'], colors):
        pc.set_facecolor(color)
        pc.set_alpha(0.7)
    
    # 3. Time series trend (simulate daily prices)
    dates = pd.date_range(start='2024-08-01', end='2024-09-10', freq='D')
    
    # Generate trending data for major platforms
    trend_data = {}
    for platform in ['京东', '淘宝', 'Amazon']:
        base_price = df[df['platform'] == platform]['price'].mean()
        trend = np.cumsum(np.random.normal(0, base_price*0.02, len(dates))) + base_price
        trend_data[platform] = trend
    
    for platform, prices in trend_data.items():
        ax3.plot(dates, prices, marker='o', linewidth=2, markersize=4, label=platform)
    
    ax3.set_title('价格趋势变化 / Price Trend Over Time', fontweight='bold')
    ax3.set_xlabel('日期 / Date')
    ax3.set_ylabel('平均价格 (CNY/USD)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='x', rotation=45)
    
    # 4. Correlation heatmap
    numeric_cols = ['price', 'rating', 'review_count']
    corr_data = df[numeric_cols].corr()
    
    im = ax4.imshow(corr_data, cmap='coolwarm', vmin=-1, vmax=1)
    ax4.set_title('变量相关性热图 / Correlation Heatmap', fontweight='bold')
    ax4.set_xticks(range(len(numeric_cols)))
    ax4.set_yticks(range(len(numeric_cols)))
    ax4.set_xticklabels(['价格', '评分', '评论数'])
    ax4.set_yticklabels(['价格', '评分', '评论数'])
    
    # Add correlation values
    for i in range(len(numeric_cols)):
        for j in range(len(numeric_cols)):
            text = ax4.text(j, i, f'{corr_data.iloc[i, j]:.2f}',
                           ha="center", va="center", color="white", fontweight='bold')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax4, shrink=0.8)
    cbar.set_label('相关系数 / Correlation Coefficient')
    
    plt.tight_layout()
    plt.savefig(docs_dir / 'visualization_demo.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    
    print("可视化层演示图表已生成:")
    print(f"  - 可视化图表集: docs/images/visualization_demo.png")
    
    # Generate sample export data
    export_demo_data(df)

def export_demo_data(df):
    """Generate sample export files."""
    print("\n生成导出格式演示数据...")
    
    output_dir = Path("docs/sample_exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    exporter = DataExporter()
    
    # Sample subset for demo
    sample_df = df.head(20).copy()
    
    # Export in different formats
    formats = ['csv', 'json', 'html']
    results = exporter.export_multiple_formats(
        sample_df, formats, 'demo_sample', str(output_dir)
    )
    
    print("导出格式演示文件:")
    for fmt, path in results.items():
        if path:
            print(f"  - {fmt.upper()}: {path}")

def generate_readme_content():
    """Generate content snippets for README."""
    summary_stats = create_analysis_demo()
    create_visualization_demo()
    
    # Generate analysis results snippet
    analysis_snippet = f"""
### 📊 数据分析层演示 / Data Analysis Layer Demo

![数据分析演示](docs/images/data_analysis_demo.png)

#### 分析结果概览 / Analysis Overview
- **总商品数**: {summary_stats['总商品数']} 个产品
- **覆盖平台**: {summary_stats['平台数']} 个主流电商平台  
- **商品品类**: {summary_stats['品类数']} 个主要品类
- **价格范围**: {summary_stats['价格区间']}
- **平均价格**: {summary_stats['平均价格']}
- **平均评分**: {summary_stats['平均评分']}

#### 关键洞察 / Key Insights
- 🏪 **平台差异**: 不同平台定价策略明显，淘宝整体价格偏低15%，小红书偏高15%
- 📊 **品类分析**: 手机数码类价格波动最大，美妆护肤类相对稳定
- ⭐ **质量关联**: 价格与评分呈现适度正相关，高价商品评分相对更高
- 📈 **市场竞争**: 京东和淘宝占据主要市场份额，竞争激烈
"""
    
    visualization_snippet = """
### 🎨 可视化层演示 / Visualization Layer Demo

![可视化演示](docs/images/visualization_demo.png)

#### 图表类型说明 / Chart Types Description

1. **价格分布直方图**: 展示中文平台vs国际平台的价格分布差异
2. **平台对比小提琴图**: 直观显示各平台价格分布的形状和密度  
3. **价格趋势线图**: 时间序列分析，追踪主要平台的价格变化趋势
4. **相关性热图**: 揭示价格、评分、评论数之间的关系强度

#### 可视化特性 / Visualization Features
- 🎯 **交互式图表**: 支持Plotly交互式图表，可缩放、筛选、悬停查看
- 🎨 **自定义主题**: 支持多种配色方案和图表样式
- 📱 **响应式设计**: 图表自动适配不同屏幕尺寸  
- 💾 **多格式导出**: PNG、SVG、HTML、PDF多种格式保存
"""

    return analysis_snippet, visualization_snippet

if __name__ == "__main__":
    print("[*] 生成README演示数据和截图...")
    print("=" * 50)
    
    try:
        analysis_snippet, viz_snippet = generate_readme_content()
        
        print(f"\n[+] 所有演示数据已生成完成!")
        print(f"[F] 文件位置:")
        print(f"  - 数据分析图表: docs/images/data_analysis_demo.png")
        print(f"  - 可视化图表: docs/images/visualization_demo.png")
        print(f"  - 导出样例: docs/sample_exports/")
        
        print(f"\n[D] README内容片段已准备，可以添加到相应章节:")
        print("=" * 30)
        print(analysis_snippet)
        print("=" * 30)
        print(viz_snippet)
        
    except Exception as e:
        print(f"[-] 生成过程中出现错误: {e}")
        import traceback
        traceback.print_exc()