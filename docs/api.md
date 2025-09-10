# 📋 API 文档 / API Documentation

本文档详细介绍了电商价格监控分析系统的API接口和使用方法。

This document provides detailed API documentation for the E-commerce Price Monitoring & Analysis System.

## 📚 目录 / Table of Contents

- [核心模块 / Core Modules](#核心模块--core-modules)
  - [PriceCollector 价格收集器](#pricecollector-价格收集器)
  - [PriceAnalyzer 价格分析器](#priceanalyzer-价格分析器)
  - [PriceVisualizer 价格可视化器](#pricevisualizer-价格可视化器)
  - [DataExporter 数据导出器](#dataexporter-数据导出器)
- [数据模型 / Data Models](#数据模型--data-models)
- [配置选项 / Configuration Options](#配置选项--configuration-options)
- [异常处理 / Exception Handling](#异常处理--exception-handling)
- [使用示例 / Usage Examples](#使用示例--usage-examples)

---

## 🔧 核心模块 / Core Modules

### PriceCollector 价格收集器

价格收集器是系统的核心组件，负责从多个电商平台收集价格数据。

#### 初始化 / Initialization

```python
from ecommerce_price_monitor import PriceCollector

# 初始化收集器，指定平台
collector = PriceCollector(platforms=['amazon', 'ebay', 'jd', 'taobao'])

# 使用默认平台
collector = PriceCollector()
```

**参数 / Parameters:**
- `platforms` (List[str], 可选): 要使用的平台列表
  - 国际平台: `['amazon', 'ebay', 'walmart']`
  - 中文平台: `['jd', 'taobao', 'xiaohongshu', 'douyin']`
- `config` (dict, 可选): 自定义配置选项

#### 主要方法 / Main Methods

##### `search_all_platforms(query, max_results_per_platform=20, use_parallel=True)`

在所有配置的平台上搜索产品。

**参数:**
- `query` (str): 搜索关键词
- `max_results_per_platform` (int): 每个平台最大结果数，默认20
- `use_parallel` (bool): 是否使用并行搜索，默认True

**返回值:**
- `Dict[str, List[ProductData]]`: 平台名称到产品列表的映射

**示例:**
```python
# 搜索手机产品
results = collector.search_all_platforms("iPhone 15", max_results_per_platform=50)

# 搜索中文产品
results = collector.search_all_platforms("华为手机", max_results_per_platform=30, use_parallel=False)
```

##### `search_platform(platform, query, max_results=20)`

在指定平台搜索产品。

**参数:**
- `platform` (str): 平台名称
- `query` (str): 搜索关键词  
- `max_results` (int): 最大结果数

**返回值:**
- `List[ProductData]`: 产品数据列表

##### `monitor_products(urls)`

监控指定URL的产品价格变化。

**参数:**
- `urls` (Dict[str, str]): 产品名称到URL的映射

**返回值:**
- `Dict[str, ProductData]`: 产品监控结果

##### `close()`

关闭收集器，清理资源。

---

### PriceAnalyzer 价格分析器

价格分析器提供深度的价格数据分析功能。

#### 初始化 / Initialization

```python
from ecommerce_price_monitor import PriceAnalyzer

analyzer = PriceAnalyzer()
```

#### 主要方法 / Main Methods

##### `analyze(data)`

对价格数据进行全面分析。

**参数:**
- `data` (Union[pd.DataFrame, List[ProductData]]): 要分析的数据

**返回值:**
- `AnalysisResult`: 分析结果对象

**示例:**
```python
# 分析收集的数据
analysis_result = analyzer.analyze(product_data)

# 获取分析结果
print(f"平均价格: ${analysis_result.metadata['price_range']['average']:.2f}")
print(f"总产品数: {analysis_result.metadata['total_products']}")
```

**分析结果包含:**
- **价格统计**: 平均值、中位数、标准差、最值
- **趋势分析**: 价格趋势识别和预测
- **平台对比**: 不同平台的价格比较
- **购买建议**: 基于分析的智能推荐

---

### PriceVisualizer 价格可视化器

价格可视化器创建专业的数据可视化图表。

#### 初始化 / Initialization

```python
from ecommerce_price_monitor import PriceVisualizer

visualizer = PriceVisualizer()
```

#### 主要方法 / Main Methods

##### `create_chart(data, chart_type, **kwargs)`

创建指定类型的图表。

**参数:**
- `data` (pd.DataFrame): 要可视化的数据
- `chart_type` (str): 图表类型
- `**kwargs`: 图表选项

**支持的图表类型:**
- `'price_distribution'`: 价格分布直方图
- `'platform_comparison'`: 平台对比柱状图
- `'price_trend'`: 价格趋势线图
- `'scatter_analysis'`: 散点分析图
- `'correlation_heatmap'`: 相关性热图
- `'box_plot'`: 箱线图

**返回值:**
- 图表对象 (Plotly或Matplotlib)

##### `create_dashboard(data)`

创建综合仪表盘，包含多种图表。

**参数:**
- `data` (pd.DataFrame): 数据

**返回值:**
- 仪表盘对象

##### `save_chart(chart, filename, format='html', output_dir='charts')`

保存图表到文件。

**参数:**
- `chart`: 图表对象
- `filename` (str): 文件名
- `format` (str): 输出格式 ('html', 'png', 'svg', 'pdf')
- `output_dir` (str): 输出目录

**示例:**
```python
# 创建价格分布图
chart = visualizer.create_chart(data, 'price_distribution')

# 保存为HTML文件
path = visualizer.save_chart(chart, 'price_analysis', 'html', 'output/')
```

---

### DataExporter 数据导出器

数据导出器支持多种格式的数据导出。

#### 初始化 / Initialization

```python
from ecommerce_price_monitor import DataExporter

exporter = DataExporter()
```

#### 主要方法 / Main Methods

##### `export_data(data, format, filename=None, output_dir='reports')`

导出数据到指定格式。

**参数:**
- `data`: 要导出的数据
- `format` (str): 导出格式
- `filename` (str, 可选): 文件名
- `output_dir` (str): 输出目录

**支持的格式:**
- `'csv'`: CSV格式
- `'excel'`: Excel格式
- `'json'`: JSON格式
- `'html'`: HTML报告
- `'markdown'`: Markdown文档

##### `export_multiple_formats(data, formats, base_filename=None, output_dir='reports')`

同时导出多种格式。

**参数:**
- `data`: 要导出的数据
- `formats` (List[str]): 格式列表
- `base_filename` (str, 可选): 基础文件名
- `output_dir` (str): 输出目录

**返回值:**
- `Dict[str, str]`: 格式到文件路径的映射

**示例:**
```python
# 导出多种格式
results = exporter.export_multiple_formats(
    data, 
    ['csv', 'excel', 'html'],
    'price_analysis_20240901',
    'output/'
)

for format_name, file_path in results.items():
    print(f"{format_name}: {file_path}")
```

---

## 📊 数据模型 / Data Models

### ProductData 产品数据模型

```python
@dataclass
class ProductData:
    platform: str           # 平台名称
    product_id: str         # 产品ID
    name: str               # 产品名称
    price: float            # 价格
    currency: str           # 货币单位
    url: Optional[str]      # 产品URL
    image_url: Optional[str] # 图片URL
    rating: Optional[float]  # 评分
    review_count: Optional[int] # 评论数
    availability: Optional[str] # 库存状态
    seller: Optional[str]    # 卖家信息
    category: Optional[str]  # 商品分类
    brand: Optional[str]     # 品牌
    timestamp: datetime      # 抓取时间
```

### AnalysisResult 分析结果模型

```python
@dataclass
class AnalysisResult:
    data: Dict[str, Any]    # 分析数据
    metadata: Dict[str, Any] # 元数据
    recommendations: List[Dict] # 购买建议
    timestamp: datetime     # 分析时间
```

---

## ⚙️ 配置选项 / Configuration Options

### 全局配置 / Global Configuration

```yaml
# config/config.yaml
scraping:
  request_delay: 1.0      # 请求延迟(秒)
  timeout: 30            # 超时时间
  retry_attempts: 3      # 重试次数
  user_agent: "Mozilla/5.0..."
  
  # 中文平台特殊配置
  chinese_platforms:
    request_delay: 2.0   # 更长延迟避免反爬
    use_proxy: false
    
analysis:
  price_change_threshold: 0.05  # 价格变化阈值
  volatility_window: 7         # 波动率计算窗口
  trend_window: 30             # 趋势分析窗口
  
database:
  path: "data/monitor.db"      # 数据库路径
  backup_enabled: true         # 启用备份
```

### 运行时配置 / Runtime Configuration

```python
# 自定义配置
config = {
    'scraping': {
        'request_delay': 2.0,
        'timeout': 60
    },
    'analysis': {
        'price_change_threshold': 0.1
    }
}

collector = PriceCollector(config=config)
```

---

## 🚨 异常处理 / Exception Handling

### 常见异常类型 / Common Exception Types

```python
from ecommerce_price_monitor.utils.exceptions import (
    CollectorError,      # 收集器异常
    AnalyzerError,       # 分析器异常
    ExporterError,       # 导出器异常
    RateLimitError       # 频率限制异常
)

# 异常处理示例
try:
    results = collector.search_all_platforms("iPhone")
except RateLimitError as e:
    print(f"请求频率过高: {e}")
    time.sleep(60)  # 等待一分钟后重试
except CollectorError as e:
    print(f"数据收集失败: {e}")
```

---

## 💡 使用示例 / Usage Examples

### 完整工作流示例 / Complete Workflow Example

```python
import pandas as pd
from ecommerce_price_monitor import (
    PriceCollector, PriceAnalyzer, 
    PriceVisualizer, DataExporter
)

# 1. 数据收集
collector = PriceCollector(['amazon', 'jd', 'taobao'])
products = collector.search_all_platforms("手机", max_results_per_platform=100)

# 2. 数据整理
all_products = []
for platform_products in products.values():
    all_products.extend(platform_products)

df = pd.DataFrame([product.__dict__ for product in all_products])

# 3. 数据分析
analyzer = PriceAnalyzer()
analysis = analyzer.analyze(df)

print(f"分析完成，共{analysis.metadata['total_products']}个产品")
print(f"平均价格: {analysis.metadata['price_range']['average']:.2f}")

# 4. 数据可视化
visualizer = PriceVisualizer()
dashboard = visualizer.create_dashboard(df)
visualizer.save_chart(dashboard, 'price_dashboard', 'html')

# 5. 数据导出
exporter = DataExporter()
export_results = exporter.export_multiple_formats(
    analysis, 
    ['html', 'excel', 'csv'],
    'price_report_20240901'
)

# 6. 清理资源
collector.close()
```

### 中文平台专用示例 / Chinese Platforms Example

```python
# 专门针对中文平台的使用
collector = PriceCollector(['jd', 'taobao', 'xiaohongshu', 'douyin'])

# 搜索中文产品
products = collector.search_all_platforms(
    "华为Mate60Pro", 
    max_results_per_platform=50,
    use_parallel=False  # 避免反爬虫
)

# 中文文本处理
from ecommerce_price_monitor.utils.chinese_text_processor import chinese_processor

for platform, product_list in products.items():
    for product in product_list:
        # 标准化产品名称
        product.name = chinese_processor.normalize_product_name(product.name)
        
        # 提取关键特征
        features = chinese_processor.extract_key_features(product.name)
        print(f"产品特征: {features}")
```

### 监控模式示例 / Monitoring Mode Example

```python
# 产品价格监控
monitor_urls = {
    "iPhone 15 Pro": "https://www.amazon.com/dp/B0CHX1W3N1",
    "华为Mate60": "https://item.jd.com/100012345678.html"
}

# 定期监控
import schedule
import time

def monitor_prices():
    collector = PriceCollector()
    results = collector.monitor_products(monitor_urls)
    
    for product_name, product_data in results.items():
        print(f"{product_name}: ${product_data.price:.2f}")
    
    collector.close()

# 每小时监控一次
schedule.every().hour.do(monitor_prices)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 🔗 相关链接 / Related Links

- [项目主页 / Project Home](../README.md)
- [配置文档 / Configuration](../config/config.yaml)
- [贡献指南 / Contributing Guide](../CONTRIBUTING.md)
- [问题反馈 / Issue Tracker](https://github.com/wangdw495/ecommerce-price-analysis/issues)

---

## 📞 获取帮助 / Getting Help

如果您在使用API时遇到问题，可以通过以下方式获取帮助：

- 📧 **邮件**: wangdw495@gmail.com
- 🐛 **问题报告**: [GitHub Issues](https://github.com/wangdw495/ecommerce-price-analysis/issues)
- 💬 **讨论交流**: [GitHub Discussions](https://github.com/wangdw495/ecommerce-price-analysis/discussions)

---

**最后更新**: 2025-09-10  
**版本**: v1.2.0