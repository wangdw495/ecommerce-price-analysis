#!/usr/bin/env python3
"""Simple demo data generator for README screenshots."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path

# Set Chinese font for matplotlib
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def generate_sample_data():
    """Generate sample data for demonstration."""
    np.random.seed(42)
    
    # Platform and product data
    platforms = ['京东', '淘宝', '小红书', '抖音电商', 'Amazon', 'eBay']
    categories = ['手机数码', '美妆护肤', '服装鞋包', '家居用品', '食品保健']
    brands = ['华为', '小米', '苹果', 'OPPO', 'vivo', '三星', 'OnePlus']
    
    data = []
    
    # Generate 150 sample products
    for i in range(150):
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
        price = max(10, price)
        
        data.append({
            'platform': platform,
            'name': f'{brand} {category}产品',
            'price': round(price, 2),
            'category': category,
            'brand': brand,
            'rating': np.random.uniform(3.8, 5.0),
            'review_count': np.random.randint(10, 5000),
            'timestamp': datetime.now() - timedelta(days=np.random.randint(0, 30))
        })
    
    return pd.DataFrame(data)

def create_analysis_charts():
    """Create data analysis charts."""
    print("[*] 生成数据分析图表...")
    
    df = generate_sample_data()
    
    # Create docs/images directory
    docs_dir = Path("docs/images")
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create analysis dashboard
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Average price by platform
    platform_prices = df.groupby('platform')['price'].mean().sort_values(ascending=False)
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FCEA2B', '#FF9F40']
    bars1 = ax1.bar(range(len(platform_prices)), platform_prices.values, color=colors)
    ax1.set_title('各平台平均价格对比', fontweight='bold', pad=15)
    ax1.set_ylabel('平均价格 (CNY/USD)')
    ax1.set_xticks(range(len(platform_prices)))
    ax1.set_xticklabels(platform_prices.index, rotation=45)
    
    # Add value labels on bars
    for bar, value in zip(bars1, platform_prices.values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 50,
                f'{value:.0f}', ha='center', va='bottom', fontweight='bold')
    
    # 2. Price distribution by category
    categories = df['category'].unique()
    category_prices = [df[df['category'] == cat]['price'].values for cat in categories]
    
    bp = ax2.boxplot(category_prices, labels=categories, patch_artist=True)
    ax2.set_title('品类价格分布箱线图', fontweight='bold', pad=15)
    ax2.set_ylabel('价格 (CNY/USD)')
    ax2.set_xlabel('商品品类')
    plt.setp(ax2.get_xticklabels(), rotation=45)
    
    # Color the boxes
    box_colors = ['#FFB6C1', '#87CEEB', '#DDA0DD', '#98FB98', '#F0E68C']
    for patch, color in zip(bp['boxes'], box_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # 3. Rating vs Price scatter
    platform_colors = {
        '京东': '#E3002B', '淘宝': '#FF6900', '小红书': '#FF2442', 
        '抖音电商': '#000000', 'Amazon': '#FF9900', 'eBay': '#0064D2'
    }
    
    platforms = ['京东', '淘宝', '小红书', '抖音电商', 'Amazon', 'eBay']
    for platform in platforms:
        platform_data = df[df['platform'] == platform]
        ax3.scatter(platform_data['price'], platform_data['rating'], 
                   label=platform, alpha=0.6, s=60, 
                   color=platform_colors.get(platform, '#333333'))
    
    ax3.set_title('价格与评分关系分析', fontweight='bold', pad=15)
    ax3.set_xlabel('价格 (CNY/USD)')
    ax3.set_ylabel('评分')
    ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax3.grid(True, alpha=0.3)
    
    # 4. Platform market share
    platform_counts = df['platform'].value_counts()
    wedges, texts, autotexts = ax4.pie(platform_counts.values, 
                                       labels=platform_counts.index, 
                                       autopct='%1.1f%%', 
                                       startangle=90,
                                       colors=[platform_colors.get(p, '#333333') 
                                              for p in platform_counts.index])
    ax4.set_title('平台商品数量分布', fontweight='bold', pad=15)
    
    # Make percentage text more readable
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    plt.tight_layout()
    plt.savefig(docs_dir / 'data_analysis_demo.png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    # Generate summary statistics
    stats = {
        'total_products': len(df),
        'platform_count': len(df['platform'].unique()),
        'category_count': len(df['category'].unique()),
        'price_range': f"{df['price'].min():.0f} - {df['price'].max():.0f}",
        'avg_price': f"{df['price'].mean():.0f}",
        'avg_rating': f"{df['rating'].mean():.1f}"
    }
    
    print(f"[+] 数据分析图表生成完成: docs/images/data_analysis_demo.png")
    print(f"[I] 数据概览: 总商品数={stats['total_products']}, 平台数={stats['platform_count']}")
    
    return df, stats

def create_visualization_charts(df):
    """Create visualization charts."""
    print("[*] 生成可视化图表...")
    
    docs_dir = Path("docs/images")
    
    # Create visualization dashboard  
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Price distribution histogram
    chinese_platforms = df[df['platform'].isin(['京东', '淘宝', '小红书', '抖音电商'])]
    international_platforms = df[df['platform'].isin(['Amazon', 'eBay'])]
    
    ax1.hist(chinese_platforms['price'], bins=25, alpha=0.7, label='中文平台', 
             color='#FF6B6B', density=True, edgecolor='black', linewidth=0.5)
    ax1.hist(international_platforms['price'], bins=25, alpha=0.7, label='国际平台', 
             color='#4ECDC4', density=True, edgecolor='black', linewidth=0.5)
    ax1.set_title('价格分布直方图', fontweight='bold', pad=15)
    ax1.set_xlabel('价格 (CNY/USD)')
    ax1.set_ylabel('密度')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Platform price violin plot
    platforms = df['platform'].unique()
    platform_prices = [df[df['platform'] == p]['price'].values for p in platforms]
    
    parts = ax2.violinplot(platform_prices, positions=range(len(platforms)), 
                          showmeans=True, showmedians=True)
    ax2.set_title('平台价格分布小提琴图', fontweight='bold', pad=15)
    ax2.set_ylabel('价格 (CNY/USD)')
    ax2.set_xticks(range(len(platforms)))
    ax2.set_xticklabels(platforms, rotation=45)
    ax2.grid(True, alpha=0.3)
    
    # Color the violin plots
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FCEA2B', '#FF9F40']
    for pc, color in zip(parts['bodies'], colors):
        pc.set_facecolor(color)
        pc.set_alpha(0.7)
    
    # 3. Time series trend simulation
    dates = pd.date_range(start='2024-08-01', end='2024-09-10', freq='D')
    
    # Generate trending data for major platforms
    trend_platforms = ['京东', '淘宝', 'Amazon']
    for i, platform in enumerate(trend_platforms):
        base_price = df[df['platform'] == platform]['price'].mean()
        # Create realistic price trend with some seasonality
        trend = np.cumsum(np.random.normal(0, base_price*0.015, len(dates))) + base_price
        trend += 50 * np.sin(np.linspace(0, 2*np.pi, len(dates))) * (i+1) * 0.3
        
        ax3.plot(dates, trend, marker='o', linewidth=2.5, markersize=4, 
                label=platform, alpha=0.8)
    
    ax3.set_title('价格趋势变化', fontweight='bold', pad=15)
    ax3.set_xlabel('日期')
    ax3.set_ylabel('平均价格 (CNY/USD)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='x', rotation=45)
    
    # 4. Correlation heatmap
    numeric_cols = ['price', 'rating', 'review_count']
    corr_data = df[numeric_cols].corr()
    
    im = ax4.imshow(corr_data, cmap='RdYlBu_r', vmin=-1, vmax=1)
    ax4.set_title('变量相关性热图', fontweight='bold', pad=15)
    ax4.set_xticks(range(len(numeric_cols)))
    ax4.set_yticks(range(len(numeric_cols)))
    ax4.set_xticklabels(['价格', '评分', '评论数'])
    ax4.set_yticklabels(['价格', '评分', '评论数'])
    
    # Add correlation values
    for i in range(len(numeric_cols)):
        for j in range(len(numeric_cols)):
            text_color = "white" if abs(corr_data.iloc[i, j]) > 0.5 else "black"
            ax4.text(j, i, f'{corr_data.iloc[i, j]:.2f}',
                    ha="center", va="center", color=text_color, fontweight='bold')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax4, shrink=0.8)
    cbar.set_label('相关系数')
    
    plt.tight_layout()
    plt.savefig(docs_dir / 'visualization_demo.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"[+] 可视化图表生成完成: docs/images/visualization_demo.png")

def main():
    print("[*] 生成README演示截图...")
    print("=" * 50)
    
    try:
        # Generate data and charts
        df, stats = create_analysis_charts()
        create_visualization_charts(df)
        
        print(f"\n[+] 所有图表生成完成!")
        print(f"[F] 生成的文件:")
        print(f"  - docs/images/data_analysis_demo.png")
        print(f"  - docs/images/visualization_demo.png")
        
        print(f"\n[I] 数据概览:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")
        
    except Exception as e:
        print(f"[-] 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()