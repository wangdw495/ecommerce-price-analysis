"""Main price collector that coordinates multiple platform collectors."""

import logging
from typing import List, Dict, Optional, Type
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from .base_collector import BaseCollector, ProductData
from .amazon_collector import AmazonCollector
from .ebay_collector import EbayCollector
from .walmart_collector import WalmartCollector
from .jd_collector import JDCollector
from .taobao_collector import TaobaoCollector
from .xiaohongshu_collector import XiaohongshuCollector
from .douyin_collector import DouyinCollector
from ..config import config_manager
from ..utils.exceptions import CollectorError


class PriceCollector:
    """Main collector that coordinates multiple platform collectors."""
    
    def __init__(self, platforms: Optional[List[str]] = None):
        """Initialize the price collector.
        
        Args:
            platforms: List of platform names to use. If None, uses all available.
        """
        self.config = config_manager.load_config()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Available collector classes
        self._collector_classes: Dict[str, Type[BaseCollector]] = {
            'amazon': AmazonCollector,
            'ebay': EbayCollector,
            'walmart': WalmartCollector,
            'jd': JDCollector,
            'jingdong': JDCollector,  # 京东别名
            'taobao': TaobaoCollector,
            'xiaohongshu': XiaohongshuCollector,
            'xhs': XiaohongshuCollector,  # 小红书别名
            'douyin': DouyinCollector,
        }
        
        # Initialize collectors for specified platforms
        if platforms is None:
            platforms = list(self._collector_classes.keys())
        
        self.collectors: Dict[str, BaseCollector] = {}
        for platform in platforms:
            if platform.lower() in self._collector_classes:
                try:
                    self.collectors[platform] = self._collector_classes[platform.lower()]()
                    self.logger.info(f"Initialized {platform} collector")
                except Exception as e:
                    self.logger.error(f"Failed to initialize {platform} collector: {e}")
            else:
                self.logger.warning(f"Unknown platform: {platform}")
        
        if not self.collectors:
            raise CollectorError("No valid collectors initialized")
    
    def search_all_platforms(
        self, 
        query: str, 
        max_results_per_platform: int = 20,
        use_parallel: bool = True
    ) -> Dict[str, List[ProductData]]:
        """Search for products across all configured platforms.
        
        Args:
            query: Search query string
            max_results_per_platform: Maximum results per platform
            use_parallel: Whether to search platforms in parallel
            
        Returns:
            Dictionary mapping platform names to product lists
        """
        self.logger.info(f"Searching for '{query}' across {len(self.collectors)} platforms")
        
        results = {}
        
        if use_parallel:
            results = self._search_parallel(query, max_results_per_platform)
        else:
            results = self._search_sequential(query, max_results_per_platform)
        
        total_results = sum(len(products) for products in results.values())
        self.logger.info(f"Found {total_results} total products across all platforms")
        
        return results
    
    def _search_parallel(
        self, 
        query: str, 
        max_results_per_platform: int
    ) -> Dict[str, List[ProductData]]:
        """Search platforms in parallel using ThreadPoolExecutor."""
        results = {}
        
        with ThreadPoolExecutor(max_workers=len(self.collectors)) as executor:
            # Submit search tasks
            future_to_platform = {
                executor.submit(
                    collector.search_products, 
                    query, 
                    max_results_per_platform
                ): platform
                for platform, collector in self.collectors.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    products = future.result()
                    results[platform] = products
                    self.logger.info(f"Found {len(products)} products on {platform}")
                except Exception as e:
                    self.logger.error(f"Error searching {platform}: {e}")
                    results[platform] = []
        
        return results
    
    def _search_sequential(
        self, 
        query: str, 
        max_results_per_platform: int
    ) -> Dict[str, List[ProductData]]:
        """Search platforms sequentially."""
        results = {}
        
        for platform, collector in self.collectors.items():
            try:
                products = collector.search_products(query, max_results_per_platform)
                results[platform] = products
                self.logger.info(f"Found {len(products)} products on {platform}")
            except Exception as e:
                self.logger.error(f"Error searching {platform}: {e}")
                results[platform] = []
        
        return results
    
    def get_product_details(
        self, 
        platform: str, 
        product_url: str
    ) -> Optional[ProductData]:
        """Get detailed product information from a specific platform.
        
        Args:
            platform: Platform name
            product_url: Product URL
            
        Returns:
            Product data or None if not found
        """
        if platform not in self.collectors:
            raise ValueError(f"Platform '{platform}' not configured")
        
        collector = self.collectors[platform]
        return collector.get_product_details(product_url)
    
    def monitor_products(
        self, 
        product_urls: Dict[str, str],
        check_interval_hours: int = 24
    ) -> Dict[str, ProductData]:
        """Monitor multiple products for price changes.
        
        Args:
            product_urls: Dict mapping product names to URLs
            check_interval_hours: How often to check (not implemented in this version)
            
        Returns:
            Dictionary mapping product names to current data
        """
        self.logger.info(f"Monitoring {len(product_urls)} products")
        
        results = {}
        
        for product_name, url in product_urls.items():
            # Determine platform from URL
            platform = self._detect_platform(url)
            if not platform:
                self.logger.warning(f"Could not detect platform for {url}")
                continue
            
            if platform not in self.collectors:
                self.logger.warning(f"Platform '{platform}' not available for {url}")
                continue
            
            try:
                product_data = self.get_product_details(platform, url)
                if product_data:
                    results[product_name] = product_data
                    self.logger.info(
                        f"Updated {product_name}: ${product_data.price} ({platform})"
                    )
                else:
                    self.logger.warning(f"Could not get data for {product_name}")
            except Exception as e:
                self.logger.error(f"Error monitoring {product_name}: {e}")
        
        return results
    
    def _detect_platform(self, url: str) -> Optional[str]:
        """Detect platform from URL.
        
        Args:
            url: Product URL
            
        Returns:
            Platform name or None if not detected
        """
        url_lower = url.lower()
        
        if 'amazon.com' in url_lower:
            return 'amazon'
        elif 'ebay.com' in url_lower:
            return 'ebay'
        elif 'walmart.com' in url_lower:
            return 'walmart'
        elif 'jd.com' in url_lower:
            return 'jd'
        elif 'taobao.com' in url_lower:
            return 'taobao'
        elif 'xiaohongshu.com' in url_lower:
            return 'xiaohongshu'
        elif 'jinritemai.com' in url_lower or 'douyin.com' in url_lower:
            return 'douyin'
        
        return None
    
    def get_available_platforms(self) -> List[str]:
        """Get list of available platform names.
        
        Returns:
            List of platform names
        """
        return list(self.collectors.keys())
    
    def close(self) -> None:
        """Close all collectors and clean up resources."""
        for collector in self.collectors.values():
            try:
                collector.close()
            except Exception as e:
                self.logger.error(f"Error closing collector: {e}")
        
        self.logger.info("All collectors closed")