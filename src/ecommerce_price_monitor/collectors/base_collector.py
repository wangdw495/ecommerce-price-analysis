"""Base collector class for all e-commerce platform scrapers."""

import time
import logging
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from ..config import config_manager
from ..utils.exceptions import CollectorError, RateLimitError


@dataclass
class ProductData:
    """Data structure for product information."""
    platform: str
    product_id: str
    name: str
    price: float
    currency: str
    availability: str
    url: str
    image_url: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    seller: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BaseCollector(ABC):
    """Abstract base class for all price collectors."""
    
    def __init__(self, platform_name: str):
        """Initialize the base collector.
        
        Args:
            platform_name: Name of the e-commerce platform
        """
        self.platform_name = platform_name
        self.config = config_manager.load_config()
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        # Setup session with default headers
        self.session = requests.Session()
        self.session.headers.update(self.config.scraping.headers)
        self.session.headers['User-Agent'] = self.config.scraping.user_agent
        
        # Rate limiting
        self.last_request_time = 0
    
    def _rate_limit(self) -> None:
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        delay = self.config.scraping.request_delay
        
        if time_since_last < delay:
            sleep_time = delay - time_since_last
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """Make a rate-limited HTTP request with retry logic.
        
        Args:
            url: URL to request
            **kwargs: Additional arguments for requests
            
        Returns:
            HTTP response object
            
        Raises:
            CollectorError: If request fails after retries
            RateLimitError: If rate limited by the platform
        """
        self._rate_limit()
        
        for attempt in range(self.config.scraping.retry_attempts):
            try:
                response = self.session.get(
                    url,
                    timeout=self.config.scraping.timeout,
                    **kwargs
                )
                
                if response.status_code == 429:
                    raise RateLimitError(f"Rate limited by {self.platform_name}")
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(
                    f"Attempt {attempt + 1} failed for {url}: {e}"
                )
                if attempt == self.config.scraping.retry_attempts - 1:
                    raise CollectorError(
                        f"Failed to fetch {url} after {self.config.scraping.retry_attempts} attempts"
                    )
                time.sleep(2 ** attempt)  # Exponential backoff
    
    @abstractmethod
    def search_products(self, query: str, max_results: int = 20) -> List[ProductData]:
        """Search for products on the platform.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of product data
        """
        pass
    
    @abstractmethod
    def get_product_details(self, product_url: str) -> Optional[ProductData]:
        """Get detailed information for a specific product.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            Product data or None if not found
        """
        pass
    
    @abstractmethod
    def extract_product_id(self, url: str) -> Optional[str]:
        """Extract product ID from URL.
        
        Args:
            url: Product URL
            
        Returns:
            Product ID or None if not found
        """
        pass
    
    def get_price_history(self, product_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical price data for a product.
        
        Note: Base implementation returns empty list.
        Override in platform-specific collectors if supported.
        
        Args:
            product_id: Product identifier
            days: Number of days of history to retrieve
            
        Returns:
            List of price history records
        """
        self.logger.info(f"Price history not implemented for {self.platform_name}")
        return []
    
    def validate_product_data(self, data: ProductData) -> bool:
        """Validate product data integrity.
        
        Args:
            data: Product data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        required_fields = ['platform', 'product_id', 'name', 'price', 'currency', 'url']
        
        for field in required_fields:
            if not getattr(data, field):
                self.logger.error(f"Missing required field: {field}")
                return False
        
        if data.price < 0:
            self.logger.error("Price cannot be negative")
            return False
        
        return True
    
    def close(self) -> None:
        """Clean up resources."""
        if hasattr(self, 'session'):
            self.session.close()