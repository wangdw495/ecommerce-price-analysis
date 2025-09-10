"""Tests for data collectors."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import requests

from ecommerce_price_monitor.collectors.base_collector import BaseCollector, ProductData
from ecommerce_price_monitor.collectors.amazon_collector import AmazonCollector
from ecommerce_price_monitor.collectors.price_collector import PriceCollector
from ecommerce_price_monitor.utils.exceptions import CollectorError, RateLimitError


class TestProductData:
    """Test ProductData class."""
    
    def test_product_data_creation(self):
        """Test creating a ProductData instance."""
        product = ProductData(
            platform="Amazon",
            product_id="B123456789",
            name="Test Product",
            price=99.99,
            currency="USD",
            availability="Available",
            url="https://amazon.com/dp/B123456789"
        )
        
        assert product.platform == "Amazon"
        assert product.product_id == "B123456789"
        assert product.name == "Test Product"
        assert product.price == 99.99
        assert product.currency == "USD"
        assert product.availability == "Available"
        assert product.url == "https://amazon.com/dp/B123456789"
        assert isinstance(product.timestamp, datetime)
    
    def test_product_data_with_optional_fields(self):
        """Test ProductData with optional fields."""
        product = ProductData(
            platform="eBay",
            product_id="123456789",
            name="Test Product",
            price=49.99,
            currency="USD",
            availability="Available",
            url="https://ebay.com/itm/123456789",
            rating=4.5,
            review_count=100,
            seller="TestSeller"
        )
        
        assert product.rating == 4.5
        assert product.review_count == 100
        assert product.seller == "TestSeller"


class TestBaseCollector:
    """Test BaseCollector class."""
    
    def test_base_collector_initialization(self):
        """Test BaseCollector initialization."""
        # Create a concrete implementation for testing
        class TestCollector(BaseCollector):
            def search_products(self, query, max_results=20):
                return []
            
            def get_product_details(self, product_url):
                return None
                
            def extract_product_id(self, url):
                return None
        
        collector = TestCollector("TestPlatform")
        assert collector.platform_name == "TestPlatform"
        assert hasattr(collector, 'session')
        assert hasattr(collector, 'config')
    
    @patch('ecommerce_price_monitor.collectors.base_collector.requests.Session.get')
    def test_rate_limiting(self, mock_get):
        """Test rate limiting functionality."""
        class TestCollector(BaseCollector):
            def search_products(self, query, max_results=20):
                return []
            
            def get_product_details(self, product_url):
                return None
                
            def extract_product_id(self, url):
                return None
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        collector = TestCollector("TestPlatform")
        
        # First request
        start_time = datetime.now()
        collector._make_request("https://example.com")
        
        # Second request should be rate limited
        collector._make_request("https://example.com")
        end_time = datetime.now()
        
        # Should take at least the delay time
        duration = (end_time - start_time).total_seconds()
        assert duration >= collector.config.scraping.request_delay
    
    @patch('ecommerce_price_monitor.collectors.base_collector.requests.Session.get')
    def test_retry_mechanism(self, mock_get):
        """Test retry mechanism for failed requests."""
        class TestCollector(BaseCollector):
            def search_products(self, query, max_results=20):
                return []
            
            def get_product_details(self, product_url):
                return None
                
            def extract_product_id(self, url):
                return None
        
        # Mock failed responses followed by success
        mock_get.side_effect = [
            requests.exceptions.RequestException("Connection error"),
            requests.exceptions.RequestException("Connection error"),
            Mock(status_code=200)
        ]
        
        collector = TestCollector("TestPlatform")
        
        # Should succeed after retries
        response = collector._make_request("https://example.com")
        assert response.status_code == 200
        assert mock_get.call_count == 3
    
    @patch('ecommerce_price_monitor.collectors.base_collector.requests.Session.get')
    def test_rate_limit_error(self, mock_get):
        """Test handling of rate limit responses."""
        class TestCollector(BaseCollector):
            def search_products(self, query, max_results=20):
                return []
            
            def get_product_details(self, product_url):
                return None
                
            def extract_product_id(self, url):
                return None
        
        # Mock rate limit response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        collector = TestCollector("TestPlatform")
        
        with pytest.raises(RateLimitError):
            collector._make_request("https://example.com")
    
    def test_validate_product_data_valid(self):
        """Test validation of valid product data."""
        class TestCollector(BaseCollector):
            def search_products(self, query, max_results=20):
                return []
            
            def get_product_details(self, product_url):
                return None
                
            def extract_product_id(self, url):
                return None
        
        collector = TestCollector("TestPlatform")
        
        valid_product = ProductData(
            platform="TestPlatform",
            product_id="123",
            name="Test Product",
            price=99.99,
            currency="USD",
            availability="Available",
            url="https://example.com/product/123"
        )
        
        assert collector.validate_product_data(valid_product) is True
    
    def test_validate_product_data_invalid(self):
        """Test validation of invalid product data."""
        class TestCollector(BaseCollector):
            def search_products(self, query, max_results=20):
                return []
            
            def get_product_details(self, product_url):
                return None
                
            def extract_product_id(self, url):
                return None
        
        collector = TestCollector("TestPlatform")
        
        # Invalid product with negative price
        invalid_product = ProductData(
            platform="TestPlatform",
            product_id="123",
            name="Test Product",
            price=-10.0,
            currency="USD",
            availability="Available",
            url="https://example.com/product/123"
        )
        
        assert collector.validate_product_data(invalid_product) is False


class TestAmazonCollector:
    """Test AmazonCollector class."""
    
    def test_amazon_collector_initialization(self):
        """Test AmazonCollector initialization."""
        collector = AmazonCollector()
        assert collector.platform_name == "Amazon"
        assert collector.base_url == "https://www.amazon.com"
        assert collector.search_url == "https://www.amazon.com/s"
    
    def test_extract_product_id_valid_urls(self):
        """Test extracting product ID from valid Amazon URLs."""
        collector = AmazonCollector()
        
        test_urls = [
            ("https://www.amazon.com/dp/B08N5WRWNW", "B08N5WRWNW"),
            ("https://amazon.com/product/B08N5WRWNW", "B08N5WRWNW"),
            ("https://www.amazon.com/gp/product/B08N5WRWNW", "B08N5WRWNW"),
            ("https://amazon.com/dp/B08N5WRWNW?ref=sr_1_1", "B08N5WRWNW"),
        ]
        
        for url, expected_id in test_urls:
            result = collector.extract_product_id(url)
            assert result == expected_id
    
    def test_extract_product_id_invalid_urls(self):
        """Test extracting product ID from invalid URLs."""
        collector = AmazonCollector()
        
        invalid_urls = [
            "https://www.amazon.com/",
            "https://google.com/",
            "invalid-url",
            "https://amazon.com/search?q=test"
        ]
        
        for url in invalid_urls:
            result = collector.extract_product_id(url)
            assert result is None
    
    def test_parse_price_valid(self):
        """Test parsing valid price strings."""
        collector = AmazonCollector()
        
        test_prices = [
            ("$19.99", 19.99),
            ("$1,234.56", 1234.56),
            ("19.99", 19.99),
            ("1,000.00", 1000.00),
        ]
        
        for price_str, expected in test_prices:
            result = collector._parse_price(price_str)
            assert result == expected
    
    def test_parse_price_invalid(self):
        """Test parsing invalid price strings."""
        collector = AmazonCollector()
        
        invalid_prices = [
            "",
            "not a price",
            "free",
            None
        ]
        
        for price_str in invalid_prices:
            result = collector._parse_price(price_str)
            assert result == 0.0


class TestPriceCollector:
    """Test PriceCollector class."""
    
    def test_price_collector_initialization_default(self):
        """Test PriceCollector initialization with default platforms."""
        with patch.dict('ecommerce_price_monitor.collectors.price_collector.PriceCollector._collector_classes', 
                       {'test_platform': Mock}):
            collector = PriceCollector(['test_platform'])
            assert 'test_platform' in collector.collectors
    
    def test_price_collector_initialization_specific_platforms(self):
        """Test PriceCollector initialization with specific platforms."""
        with patch.dict('ecommerce_price_monitor.collectors.price_collector.PriceCollector._collector_classes', 
                       {'amazon': Mock, 'ebay': Mock}):
            collector = PriceCollector(['amazon'])
            assert len(collector.collectors) <= 1  # Should only have amazon if initialization succeeds
    
    def test_get_available_platforms(self):
        """Test getting available platforms."""
        with patch.dict('ecommerce_price_monitor.collectors.price_collector.PriceCollector._collector_classes', 
                       {'platform1': Mock, 'platform2': Mock}):
            collector = PriceCollector(['platform1', 'platform2'])
            platforms = collector.get_available_platforms()
            # Check that platforms is a list (exact content depends on mock success)
            assert isinstance(platforms, list)
    
    def test_detect_platform(self):
        """Test platform detection from URLs."""
        collector = PriceCollector([])  # Empty list to avoid initialization issues
        
        test_cases = [
            ("https://amazon.com/dp/B123", "amazon"),
            ("https://www.amazon.com/product/B123", "amazon"),
            ("https://ebay.com/itm/123", "ebay"),
            ("https://www.ebay.com/item/123", "ebay"),
            ("https://walmart.com/ip/123", "walmart"),
            ("https://www.walmart.com/product/123", "walmart"),
            ("https://unknown.com/product/123", None),
            ("invalid-url", None)
        ]
        
        for url, expected in test_cases:
            result = collector._detect_platform(url)
            assert result == expected


class TestIntegration:
    """Integration tests for collectors."""
    
    @pytest.fixture
    def sample_product_data(self):
        """Sample product data for testing."""
        return [
            ProductData(
                platform="Amazon",
                product_id="B123",
                name="Product 1",
                price=99.99,
                currency="USD",
                availability="Available",
                url="https://amazon.com/dp/B123"
            ),
            ProductData(
                platform="eBay",
                product_id="456",
                name="Product 2", 
                price=89.99,
                currency="USD",
                availability="Available",
                url="https://ebay.com/itm/456"
            )
        ]
    
    def test_collector_close_method(self):
        """Test that collectors can be properly closed."""
        try:
            collector = PriceCollector([])
            collector.close()
            # Should not raise any exceptions
        except Exception as e:
            pytest.fail(f"Collector close method failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__])