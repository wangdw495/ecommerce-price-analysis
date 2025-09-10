"""Tests for data analyzers."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ecommerce_price_monitor.analyzers.base_analyzer import BaseAnalyzer, AnalysisResult
from ecommerce_price_monitor.analyzers.price_analyzer import PriceAnalyzer
from ecommerce_price_monitor.analyzers.statistical_analyzer import StatisticalAnalyzer
from ecommerce_price_monitor.collectors.base_collector import ProductData
from ecommerce_price_monitor.utils.exceptions import AnalyzerError


class TestAnalysisResult:
    """Test AnalysisResult class."""
    
    def test_analysis_result_creation(self):
        """Test creating an AnalysisResult instance."""
        data = {'test_metric': 100, 'test_list': [1, 2, 3]}
        result = AnalysisResult(
            analysis_type="test_analysis",
            data=data,
            metadata={'sample_size': 10}
        )
        
        assert result.analysis_type == "test_analysis"
        assert result.data == data
        assert result.metadata == {'sample_size': 10}
        assert isinstance(result.timestamp, datetime)
    
    def test_analysis_result_to_dict(self):
        """Test converting AnalysisResult to dictionary."""
        data = {'metric': 42}
        result = AnalysisResult("test", data)
        
        dict_result = result.to_dict()
        
        assert dict_result['analysis_type'] == "test"
        assert dict_result['data'] == data
        assert 'timestamp' in dict_result
        assert 'metadata' in dict_result


class TestBaseAnalyzer:
    """Test BaseAnalyzer class."""
    
    def test_prepare_dataframe_empty_list(self):
        """Test preparing DataFrame from empty list."""
        class TestAnalyzer(BaseAnalyzer):
            def analyze(self, data, **kwargs):
                return AnalysisResult("test", {})
        
        analyzer = TestAnalyzer()
        df = analyzer.prepare_dataframe([])
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_prepare_dataframe_with_products(self):
        """Test preparing DataFrame from product list."""
        class TestAnalyzer(BaseAnalyzer):
            def analyze(self, data, **kwargs):
                return AnalysisResult("test", {})
        
        analyzer = TestAnalyzer()
        
        products = [
            ProductData(
                platform="Amazon",
                product_id="B123",
                name="Test Product",
                price=99.99,
                currency="USD",
                availability="Available",
                url="https://amazon.com/dp/B123",
                rating=4.5
            )
        ]
        
        df = analyzer.prepare_dataframe(products)
        
        assert len(df) == 1
        assert df.iloc[0]['platform'] == "Amazon"
        assert df.iloc[0]['price'] == 99.99
        assert df.iloc[0]['rating'] == 4.5
    
    def test_validate_data_valid_list(self):
        """Test data validation with valid product list."""
        class TestAnalyzer(BaseAnalyzer):
            def analyze(self, data, **kwargs):
                return AnalysisResult("test", {})
        
        analyzer = TestAnalyzer()
        
        products = [
            ProductData(
                platform="Amazon",
                product_id="B123", 
                name="Test Product",
                price=99.99,
                currency="USD",
                availability="Available",
                url="https://amazon.com/dp/B123"
            )
        ]
        
        assert analyzer.validate_data(products) is True
    
    def test_validate_data_empty_list(self):
        """Test data validation with empty list."""
        class TestAnalyzer(BaseAnalyzer):
            def analyze(self, data, **kwargs):
                return AnalysisResult("test", {})
        
        analyzer = TestAnalyzer()
        assert analyzer.validate_data([]) is False
    
    def test_validate_data_valid_dataframe(self):
        """Test data validation with valid DataFrame."""
        class TestAnalyzer(BaseAnalyzer):
            def analyze(self, data, **kwargs):
                return AnalysisResult("test", {})
        
        analyzer = TestAnalyzer()
        
        df = pd.DataFrame({
            'price': [99.99, 89.99],
            'timestamp': [datetime.now(), datetime.now()]
        })
        
        assert analyzer.validate_data(df) is True
    
    def test_validate_data_empty_dataframe(self):
        """Test data validation with empty DataFrame."""
        class TestAnalyzer(BaseAnalyzer):
            def analyze(self, data, **kwargs):
                return AnalysisResult("test", {})
        
        analyzer = TestAnalyzer()
        df = pd.DataFrame()
        
        assert analyzer.validate_data(df) is False
    
    def test_filter_by_date_range(self):
        """Test filtering DataFrame by date range."""
        class TestAnalyzer(BaseAnalyzer):
            def analyze(self, data, **kwargs):
                return AnalysisResult("test", {})
        
        analyzer = TestAnalyzer()
        
        # Create test data with different dates
        dates = [
            datetime(2024, 1, 1),
            datetime(2024, 1, 15),
            datetime(2024, 2, 1),
            datetime(2024, 2, 15)
        ]
        
        df = pd.DataFrame({
            'price': [100, 110, 120, 130],
            'timestamp': dates
        })
        
        # Filter for January 2024
        filtered = analyzer.filter_by_date_range(
            df, 
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        assert len(filtered) == 2
        assert all(filtered['timestamp'].dt.month == 1)
    
    def test_filter_by_platform(self):
        """Test filtering DataFrame by platforms."""
        class TestAnalyzer(BaseAnalyzer):
            def analyze(self, data, **kwargs):
                return AnalysisResult("test", {})
        
        analyzer = TestAnalyzer()
        
        df = pd.DataFrame({
            'platform': ['Amazon', 'eBay', 'Amazon', 'Walmart'],
            'price': [100, 90, 105, 95]
        })
        
        filtered = analyzer.filter_by_platform(df, ['Amazon', 'eBay'])
        
        assert len(filtered) == 3
        assert all(filtered['platform'].isin(['Amazon', 'eBay']))
    
    def test_calculate_basic_stats(self):
        """Test calculating basic statistics."""
        class TestAnalyzer(BaseAnalyzer):
            def analyze(self, data, **kwargs):
                return AnalysisResult("test", {})
        
        analyzer = TestAnalyzer()
        
        df = pd.DataFrame({
            'price': [100, 110, 120, 130, 140],
            'rating': [4.0, 4.5, 5.0, 3.5, 4.2]
        })
        
        stats = analyzer.calculate_basic_stats(df)
        
        assert 'price' in stats
        assert 'rating' in stats
        assert stats['price']['count'] == 5
        assert stats['price']['mean'] == 120.0
        assert stats['price']['min'] == 100.0
        assert stats['price']['max'] == 140.0


class TestPriceAnalyzer:
    """Test PriceAnalyzer class."""
    
    def test_price_analyzer_initialization(self):
        """Test PriceAnalyzer initialization."""
        analyzer = PriceAnalyzer()
        
        assert hasattr(analyzer, 'trend_analyzer')
        assert hasattr(analyzer, 'comparison_analyzer')
        assert hasattr(analyzer, 'statistical_analyzer')
    
    def test_analyze_with_dataframe(self):
        """Test analysis with DataFrame input."""
        analyzer = PriceAnalyzer()
        
        # Create sample data
        df = pd.DataFrame({
            'platform': ['Amazon', 'eBay', 'Amazon', 'eBay'],
            'name': ['Product A', 'Product B', 'Product C', 'Product D'],
            'price': [100.0, 90.0, 110.0, 85.0],
            'rating': [4.5, 4.0, 4.2, 3.8],
            'timestamp': [datetime.now()] * 4
        })
        
        result = analyzer.analyze(df)
        
        assert isinstance(result, AnalysisResult)
        assert result.analysis_type == 'comprehensive_price_analysis'
        assert 'overview' in result.data
        assert 'platform_comparison' in result.data
        assert result.metadata['total_products'] == 4
    
    def test_analyze_overview(self):
        """Test overview analysis."""
        analyzer = PriceAnalyzer()
        
        df = pd.DataFrame({
            'platform': ['Amazon', 'eBay'],
            'price': [100.0, 90.0],
            'availability': ['Available', 'Available'],
            'rating': [4.5, 4.0]
        })
        
        overview = analyzer._analyze_overview(df)
        
        assert overview['total_products'] == 2
        assert overview['platforms_count'] == 2
        assert 'price_stats' in overview
        assert overview['price_stats']['average'] == 95.0
    
    def test_analyze_platforms(self):
        """Test platform analysis."""
        analyzer = PriceAnalyzer()
        
        df = pd.DataFrame({
            'platform': ['Amazon', 'Amazon', 'eBay', 'eBay'],
            'price': [100.0, 110.0, 90.0, 95.0],
            'rating': [4.5, 4.2, 4.0, 4.1]
        })
        
        platform_analysis = analyzer._analyze_platforms(df)
        
        assert 'Amazon' in platform_analysis
        assert 'eBay' in platform_analysis
        assert platform_analysis['Amazon']['average_price'] == 105.0
        assert platform_analysis['eBay']['average_price'] == 92.5
        assert 'summary' in platform_analysis
    
    def test_identify_best_deals(self):
        """Test best deals identification."""
        analyzer = PriceAnalyzer()
        
        df = pd.DataFrame({
            'platform': ['Amazon', 'eBay', 'Walmart'],
            'name': ['Product A', 'Product B', 'Product C'],
            'price': [100.0, 80.0, 120.0],
            'rating': [4.5, 4.0, 4.8],
            'url': ['url1', 'url2', 'url3']
        })
        
        best_deals = analyzer._identify_best_deals(df)
        
        assert 'cheapest' in best_deals
        assert len(best_deals['cheapest']) > 0
        assert best_deals['cheapest'][0]['price'] == 80.0  # eBay product
        
        if 'highest_rated' in best_deals:
            assert best_deals['highest_rated'][0]['rating'] == 4.8  # Walmart product


class TestStatisticalAnalyzer:
    """Test StatisticalAnalyzer class."""
    
    def test_statistical_analyzer_initialization(self):
        """Test StatisticalAnalyzer initialization."""
        analyzer = StatisticalAnalyzer()
        assert hasattr(analyzer, 'config')
    
    def test_descriptive_stats(self):
        """Test descriptive statistics calculation."""
        analyzer = StatisticalAnalyzer()
        
        # Create sample data with known statistics
        prices = [100, 110, 120, 130, 140]
        df = pd.DataFrame({
            'price': prices,
            'platform': ['Amazon'] * 5
        })
        
        stats = analyzer._calculate_descriptive_stats(df)
        
        assert 'count' in stats
        assert 'mean' in stats
        assert 'median' in stats
        assert 'std' in stats
        assert stats['count'] == 5
        assert stats['mean'] == 120.0
        assert stats['median'] == 120.0
    
    def test_outlier_detection_iqr(self):
        """Test outlier detection using IQR method."""
        analyzer = StatisticalAnalyzer()
        
        # Create data with obvious outliers
        df = pd.DataFrame({
            'price': [10, 15, 20, 25, 30, 1000],  # 1000 is an outlier
            'name': ['P1', 'P2', 'P3', 'P4', 'P5', 'P6'],
            'platform': ['Amazon'] * 6
        })
        
        outliers = analyzer._detect_outliers_iqr(df['price'], df)
        
        assert outliers['outlier_count'] >= 1
        assert 1000.0 in outliers['outlier_values']
    
    def test_correlation_analysis(self):
        """Test correlation analysis."""
        analyzer = StatisticalAnalyzer()
        
        # Create correlated data
        np.random.seed(42)
        price = np.random.normal(100, 20, 50)
        rating = 5 - (price - 100) / 50 + np.random.normal(0, 0.1, 50)  # Negative correlation
        
        df = pd.DataFrame({
            'price': price,
            'rating': rating,
            'review_count': np.random.randint(10, 1000, 50)
        })
        
        corr_analysis = analyzer._analyze_correlations(df)
        
        assert 'correlation_matrix' in corr_analysis
        assert 'strong_correlations' in corr_analysis


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing."""
    np.random.seed(42)
    
    return pd.DataFrame({
        'platform': ['Amazon', 'eBay', 'Walmart'] * 20,
        'name': [f'Product {i}' for i in range(60)],
        'price': np.random.normal(100, 25, 60),
        'rating': np.random.uniform(3, 5, 60),
        'review_count': np.random.randint(10, 1000, 60),
        'timestamp': [datetime.now() - timedelta(days=i) for i in range(60)]
    })


class TestIntegration:
    """Integration tests for analyzers."""
    
    def test_complete_analysis_workflow(self, sample_dataframe):
        """Test complete analysis workflow."""
        analyzer = PriceAnalyzer()
        
        result = analyzer.analyze(sample_dataframe)
        
        assert isinstance(result, AnalysisResult)
        assert result.analysis_type == 'comprehensive_price_analysis'
        assert 'overview' in result.data
        assert 'platform_comparison' in result.data
        assert 'statistics' in result.data
    
    def test_statistical_analysis_workflow(self, sample_dataframe):
        """Test statistical analysis workflow."""
        analyzer = StatisticalAnalyzer()
        
        result = analyzer.analyze(sample_dataframe)
        
        assert isinstance(result, AnalysisResult)
        assert result.analysis_type == 'statistical_analysis'
        assert 'descriptive_stats' in result.data
        assert 'outlier_analysis' in result.data
    
    def test_error_handling_invalid_data(self):
        """Test error handling with invalid data."""
        analyzer = PriceAnalyzer()
        
        with pytest.raises(ValueError):
            analyzer.analyze("invalid data")
        
        with pytest.raises(ValueError):
            analyzer.analyze([])


if __name__ == "__main__":
    pytest.main([__file__])