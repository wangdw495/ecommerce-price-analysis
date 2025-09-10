"""
国内电商平台使用示例 - Chinese e-commerce platforms usage examples.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecommerce_price_monitor import PriceCollector, PriceAnalyzer, PriceVisualizer, DataExporter


def example_chinese_platforms_search():
    """国内电商平台搜索示例 - Chinese platforms search example."""
    print("🇨🇳 国内电商平台搜索示例 / Chinese E-commerce Platforms Search")
    print("=" * 70)
    
    # 支持的国内平台
    chinese_platforms = ['jd', 'taobao', 'xiaohongshu', 'douyin']
    
    # 搜索不同类型的商品
    search_queries = {
        '数码产品': ['华为手机', '小米手机', 'iPhone', 'MacBook'],
        '美妆护肤': ['护肤品', '口红', '面膜', '洗面奶'],
        '服装鞋包': ['连衣裙', '运动鞋', '手提包', '牛仔裤'],
        '家居用品': ['加湿器', '扫地机器人', '空气净化器', '智能音箱']
    }
    
    # 初始化收集器
    collector = PriceCollector(platforms=chinese_platforms)
    
    print("🔍 开始搜索各类商品...")
    
    all_results = {}
    
    for category, queries in search_queries.items():
        print(f"\n📱 {category} 类商品搜索:")
        print("-" * 40)
        
        category_results = {}
        
        for query in queries[:2]:  # 限制每个分类搜索2个关键词
            try:
                print(f"   🔍 搜索关键词: {query}")
                
                results = collector.search_all_platforms(
                    query=query,
                    max_results_per_platform=3,  # 每个平台3个结果
                    use_parallel=False  # 顺序搜索，避免被反爬
                )
                
                category_results[query] = results
                
                # 显示搜索结果统计
                total_found = sum(len(products) for products in results.values())
                print(f"     ✅ 找到 {total_found} 个商品")
                
                for platform, products in results.items():
                    if products:
                        avg_price = sum(p.price for p in products if p.price > 0) / len([p for p in products if p.price > 0]) if any(p.price > 0 for p in products) else 0
                        print(f"       📦 {platform}: {len(products)} 个商品 (平均价格: ¥{avg_price:.2f})")
                
            except Exception as e:
                print(f"     ❌ 搜索失败: {e}")
                continue
        
        all_results[category] = category_results
    
    collector.close()
    
    print(f"\n🎉 搜索完成! 共搜索了 {len([q for queries in search_queries.values() for q in queries[:2]])} 个关键词")
    
    return all_results


def example_chinese_text_processing():
    """中文文本处理示例 - Chinese text processing example."""
    print("\n📝 中文商品名称处理示例 / Chinese Text Processing Example")
    print("=" * 70)
    
    try:
        from ecommerce_price_monitor.utils.chinese_text_processor import chinese_processor
        
        # 测试商品名称
        test_names = [
            "华为 HUAWEI Mate 60 Pro 5G 智能手机 12GB+512GB 雅黑色 鸿蒙系统",
            "苹果Apple MacBook Air 13.6英寸笔记本电脑 M2芯片 8核CPU 8核GPU 8GB+256GB SSD",
            "小米Redmi Note 12 Pro 5G手机 8+256GB 冰蓝色 天玑1080处理器",
            "【京东自营】华为智能手表 WATCH GT 4 46mm 运动款 黑色 蓝牙通话 健康监测",
            "兰蔻小黑瓶精华液30ml 修护保湿 淡化细纹 抗衰老 正品专柜",
        ]
        
        print("🔤 商品名称标准化处理:")
        print("-" * 50)
        
        for name in test_names:
            normalized = chinese_processor.normalize_product_name(name)
            print(f"原始: {name}")
            print(f"标准化: {normalized}")
            print()
        
        print("🔍 商品特征提取:")
        print("-" * 50)
        
        for name in test_names[:3]:  # 取前3个进行特征提取
            features = chinese_processor.extract_key_features(name)
            print(f"商品: {name[:50]}...")
            
            for feature_type, feature_list in features.items():
                if feature_list:
                    print(f"  {feature_type}: {', '.join(feature_list)}")
            print()
        
        print("📊 商品相似度计算:")
        print("-" * 50)
        
        # 测试相似度计算
        similarity_tests = [
            ("华为Mate 60 Pro 5G手机", "HUAWEI Mate60Pro 智能手机"),
            ("苹果MacBook Air 13.6寸", "Apple MacBook Air 13英寸笔记本"),
            ("小米手机Note 12", "华为手机Mate 60"),
        ]
        
        for name1, name2 in similarity_tests:
            similarity = chinese_processor.calculate_similarity(name1, name2)
            print(f"商品1: {name1}")
            print(f"商品2: {name2}")
            print(f"相似度: {similarity:.3f}")
            print()
            
    except ImportError as e:
        print(f"⚠️  中文处理库未安装: {e}")
        print("请运行: pip install jieba zhconv")


def example_cross_platform_comparison():
    """跨平台价格比较示例 - Cross-platform price comparison example."""
    print("\n💰 跨平台价格比较示例 / Cross-platform Price Comparison")
    print("=" * 70)
    
    # 创建模拟数据进行比较分析
    import pandas as pd
    import numpy as np
    from datetime import datetime
    
    np.random.seed(42)
    
    # 模拟不同平台的同类商品数据
    platforms = ['京东', '淘宝', '小红书', '抖音电商']
    product_categories = ['数码', '美妆', '服装', '家居']
    
    data = []
    product_id = 1
    
    for category in product_categories:
        for platform in platforms:
            # 每个平台每个分类生成10个商品
            for i in range(10):
                base_price = {
                    '数码': np.random.normal(2000, 500),
                    '美妆': np.random.normal(200, 50),
                    '服装': np.random.normal(150, 30),
                    '家居': np.random.normal(300, 100)
                }[category]
                
                # 不同平台的价格策略
                platform_multiplier = {
                    '京东': 1.0,      # 基准价格
                    '淘宝': 0.85,     # 相对便宜15%
                    '小红书': 1.15,   # 相对贵15%
                    '抖音电商': 0.90  # 相对便宜10%
                }[platform]
                
                price = max(10, base_price * platform_multiplier + np.random.normal(0, 20))
                
                data.append({
                    'platform': platform,
                    'product_id': f'{platform}_{product_id:04d}',
                    'name': f'{category}商品_{i+1}',
                    'price': price,
                    'currency': 'CNY',
                    'category': category,
                    'rating': np.random.uniform(3.5, 5.0),
                    'review_count': np.random.randint(10, 1000),
                    'timestamp': datetime.now()
                })
                product_id += 1
    
    df = pd.DataFrame(data)
    
    print("📊 跨平台价格统计分析:")
    print("-" * 50)
    
    # 按平台统计
    platform_stats = df.groupby('platform').agg({
        'price': ['mean', 'median', 'std', 'min', 'max'],
        'rating': 'mean',
        'review_count': 'mean'
    }).round(2)
    
    print("各平台价格统计:")
    for platform in platforms:
        platform_data = df[df['platform'] == platform]
        avg_price = platform_data['price'].mean()
        median_price = platform_data['price'].median()
        avg_rating = platform_data['rating'].mean()
        
        print(f"  🏪 {platform}:")
        print(f"    平均价格: ¥{avg_price:.2f}")
        print(f"    中位数价格: ¥{median_price:.2f}")
        print(f"    平均评分: {avg_rating:.2f}⭐")
        print()
    
    print("📈 分品类价格比较:")
    print("-" * 50)
    
    for category in product_categories:
        print(f"🏷️  {category}类商品:")
        category_data = df[df['category'] == category]
        
        platform_prices = category_data.groupby('platform')['price'].mean().sort_values()
        
        cheapest_platform = platform_prices.index[0]
        most_expensive_platform = platform_prices.index[-1]
        price_diff = platform_prices.iloc[-1] - platform_prices.iloc[0]
        
        print(f"    最便宜: {cheapest_platform} (¥{platform_prices.iloc[0]:.2f})")
        print(f"    最贵: {most_expensive_platform} (¥{platform_prices.iloc[-1]:.2f})")
        print(f"    价差: ¥{price_diff:.2f}")
        print()
    
    # 分析和可视化
    try:
        analyzer = PriceAnalyzer()
        analysis_result = analyzer.analyze(df)
        
        print("🎯 购买建议:")
        print("-" * 50)
        
        if 'recommendations' in analysis_result.data:
            for rec in analysis_result.data['recommendations']:
                print(f"✅ {rec.get('title', '建议')}: {rec.get('description', '')}")
        
        # 生成报告
        exporter = DataExporter()
        
        output_dir = Path("examples/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 导出数据和分析结果
        data_file = exporter.export_data(df, 'csv', 'chinese_platforms_data', str(output_dir))
        analysis_file = exporter.export_data(analysis_result, 'html', 'chinese_platforms_analysis', str(output_dir))
        
        print(f"\n💾 数据已导出:")
        print(f"   📄 数据文件: {data_file}")
        print(f"   📊 分析报告: {analysis_file}")
        
    except Exception as e:
        print(f"⚠️  分析过程中出现错误: {e}")


def main():
    """运行所有中文平台示例 - Run all Chinese platform examples."""
    print("🛒 国内电商平台价格监控系统 - 中文示例")
    print("E-commerce Price Monitor - Chinese Platforms Examples")
    print("=" * 80)
    
    try:
        # 示例1: 基础搜索 (注释掉以避免实际网络请求)
        # example_chinese_platforms_search()
        print("💡 提示: 基础搜索示例已注释，如需测试请取消注释")
        
        # 示例2: 中文文本处理
        example_chinese_text_processing()
        
        # 示例3: 跨平台比较
        example_cross_platform_comparison()
        
        print("\n🎉 所有中文平台示例运行完成!")
        print("📁 查看 examples/output 目录获取生成的文件")
        
    except Exception as e:
        print(f"\n❌ 运行示例时出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()