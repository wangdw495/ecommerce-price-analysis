# 贡献指南 / Contributing Guide

感谢您对E-commerce Price Monitor项目的关注！我们欢迎所有形式的贡献。

Thank you for your interest in contributing to the E-commerce Price Monitor project! We welcome all forms of contributions.

## 🚀 如何贡献 / How to Contribute

### 1. 报告问题 / Report Issues
- 使用[GitHub Issues](https://github.com/wangdw495/ecommerce-price-analysis/issues)报告bug
- 提交功能请求和改进建议
- 请尽可能详细地描述问题

### 2. 提交代码 / Submit Code
1. Fork 这个仓库
2. 创建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个Pull Request

### 3. 改进文档 / Improve Documentation
- 修复文档中的错误
- 添加新的示例
- 改善API文档

## 🛠️ 开发环境设置 / Development Setup

```bash
# 克隆仓库
git clone https://github.com/wangdw495/ecommerce-price-analysis.git
cd ecommerce-price-analysis

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -e ".[dev]"

# 安装pre-commit钩子
pre-commit install
```

## 📋 代码规范 / Code Standards

### Python 代码风格 / Python Code Style
- 使用 [Black](https://black.readthedocs.io/) 进行代码格式化
- 使用 [flake8](https://flake8.pycqa.org/) 进行代码检查
- 使用 [mypy](https://mypy.readthedocs.io/) 进行类型检查
- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范

### 运行代码检查 / Run Code Checks
```bash
# 格式化代码
black src/ tests/

# 代码检查
flake8 src/ tests/

# 类型检查
mypy src/

# 运行所有检查
pre-commit run --all-files
```

### 文档字符串 / Docstrings
使用Google风格的文档字符串：

```python
def example_function(param1: str, param2: int) -> bool:
    """Example function with types documented in the docstring.
    
    Args:
        param1: The first parameter.
        param2: The second parameter.
    
    Returns:
        True if successful, False otherwise.
    
    Raises:
        ValueError: If param1 is empty.
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    return True
```

## 🧪 测试 / Testing

### 运行测试 / Running Tests
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_collectors.py

# 运行带覆盖率的测试
pytest --cov=ecommerce_price_monitor --cov-report=html

# 运行特定测试类
pytest tests/test_collectors.py::TestAmazonCollector
```

### 编写测试 / Writing Tests
- 为所有新功能编写测试
- 测试文件命名格式: `test_*.py`
- 使用描述性的测试方法名
- 包含正常情况和边界情况测试

```python
import pytest
from ecommerce_price_monitor.collectors.base_collector import BaseCollector


class TestBaseCollector:
    def test_rate_limiting(self):
        """Test that rate limiting works correctly."""
        # Test implementation here
        pass
    
    def test_invalid_url_handling(self):
        """Test handling of invalid URLs."""
        with pytest.raises(ValueError):
            # Test code that should raise ValueError
            pass
```

## 📦 添加新的平台支持 / Adding New Platform Support

要添加新的电商平台支持，请：

To add support for a new e-commerce platform:

1. 在 `src/ecommerce_price_monitor/collectors/` 中创建新的收集器
2. 继承 `BaseCollector` 类
3. 实现必需的抽象方法
4. 在 `price_collector.py` 中注册新的收集器
5. 添加相应的测试
6. 更新文档

示例结构：
```python
from .base_collector import BaseCollector, ProductData

class NewPlatformCollector(BaseCollector):
    def __init__(self):
        super().__init__("NewPlatform")
        
    def search_products(self, query: str, max_results: int = 20):
        # Implementation
        pass
        
    def get_product_details(self, product_url: str):
        # Implementation
        pass
        
    def extract_product_id(self, url: str):
        # Implementation
        pass
```

## 🐛 调试 / Debugging

### 日志配置 / Logging Configuration
```python
from ecommerce_price_monitor.utils.logging_config import setup_logging

# 启用调试日志
setup_logging(log_level="DEBUG", console_output=True)
```

### 常见问题 / Common Issues
1. **网络请求失败**: 检查网络连接和防火墙设置
2. **解析错误**: 目标网站可能更新了HTML结构
3. **速率限制**: 调整请求延迟设置

## 📖 文档贡献 / Documentation Contributions

### API文档 / API Documentation
- 保持文档字符串最新
- 添加使用示例
- 解释复杂的算法和数据结构

### README更新 / README Updates
- 添加新功能说明
- 更新安装说明
- 改进示例代码

## 🏷️ 版本发布 / Release Process

我们使用[语义版本控制](https://semver.org/)：

- **主版本号**: 不兼容的API更改
- **次版本号**: 向后兼容的功能添加
- **修订号**: 向后兼容的bug修复

## 📞 获取帮助 / Getting Help

- 📧 Email: wangdw495@gmail.com
- 💬 [GitHub Discussions](https://github.com/wangdw495/ecommerce-price-analysis/discussions)
- 📖 [文档](https://github.com/wangdw495/ecommerce-price-analysis/wiki)

## 🎯 贡献想法 / Contribution Ideas

### 🔥 热门需求 / High Priority
- [ ] 添加新的电商平台支持 (Target, Best Buy)
- [ ] 改进价格预测算法
- [ ] 添加移动端友好的报告模板
- [ ] 实现实时价格监控

### 📊 数据分析增强 / Analytics Enhancements
- [ ] 季节性分析改进
- [ ] 价格弹性分析
- [ ] 竞争对手分析功能
- [ ] 机器学习价格预测

### 🎨 可视化改进 / Visualization Improvements
- [ ] 交互式仪表板
- [ ] 更多图表类型
- [ ] 移动端适配
- [ ] 深色主题支持

### 🔧 基础设施 / Infrastructure
- [ ] Docker容器化
- [ ] API接口开发
- [ ] 数据库优化
- [ ] 缓存机制改进

## ⚖️ 行为准则 / Code of Conduct

请友善和尊重地对待所有项目参与者。我们致力于为所有人创造一个开放和欢迎的环境。

Please be kind and respectful to all project participants. We are committed to creating an open and welcoming environment for everyone.

## 📝 许可证 / License

通过贡献代码，您同意您的贡献将按照项目的MIT许可证进行许可。

By contributing, you agree that your contributions will be licensed under the project's MIT License.

---

再次感谢您的贡献！🎉

Thank you again for your contributions! 🎉