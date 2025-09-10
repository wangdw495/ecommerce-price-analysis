"""eBay product data collector."""

import re
import json
from typing import List, Optional
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup

from .base_collector import BaseCollector, ProductData
from ..utils.exceptions import CollectorError


class EbayCollector(BaseCollector):
    """eBay-specific product data collector."""
    
    def __init__(self):
        super().__init__("eBay")
        self.base_url = "https://www.ebay.com"
        self.search_url = "https://www.ebay.com/sch/i.html"
    
    def search_products(self, query: str, max_results: int = 20) -> List[ProductData]:
        """Search for products on eBay.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of product data
        """
        products = []
        page = 1
        
        while len(products) < max_results:
            try:
                params = {
                    '_nkw': query,
                    '_pgn': page,
                    '_skc': 0,
                    'rt': 'nc'
                }
                
                response = self._make_request(self.search_url, params=params)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find product containers
                product_containers = soup.find_all('div', class_='s-item__wrapper')
                
                if not product_containers:
                    self.logger.info("No more products found")
                    break
                
                for container in product_containers:
                    if len(products) >= max_results:
                        break
                        
                    try:
                        product_data = self._extract_product_from_search(container)
                        if product_data and self.validate_product_data(product_data):
                            products.append(product_data)
                    except Exception as e:
                        self.logger.warning(f"Error extracting product: {e}")
                        continue
                
                page += 1
                
            except Exception as e:
                self.logger.error(f"Error searching eBay: {e}")
                break
        
        self.logger.info(f"Found {len(products)} products for query: {query}")
        return products
    
    def _extract_product_from_search(self, container) -> Optional[ProductData]:
        """Extract product data from search result container."""
        try:
            # Skip promoted/ad items
            if container.find(class_='s-item--promoted'):
                return None
            
            # Product name and URL
            title_elem = container.find('h3', class_='s-item__title')
            if not title_elem:
                return None
                
            link_elem = title_elem.find('a')
            if not link_elem:
                return None
                
            name = title_elem.get_text(strip=True)
            url = link_elem.get('href')
            
            if not url or 'New listing' in name:
                return None
            
            product_id = self.extract_product_id(url)
            if not product_id:
                return None
            
            # Price
            price = 0.0
            price_elem = container.find('span', class_='s-item__price')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self._parse_price(price_text)
            
            # Shipping info
            shipping_elem = container.find('span', class_='s-item__shipping')
            shipping_cost = 0.0
            if shipping_elem:
                shipping_text = shipping_elem.get_text(strip=True)
                if 'Free shipping' not in shipping_text:
                    shipping_cost = self._parse_price(shipping_text)
            
            # Total price including shipping
            total_price = price + shipping_cost
            
            # Condition
            condition_elem = container.find('span', class_='SECONDARY_INFO')
            condition = "Used"
            if condition_elem:
                condition_text = condition_elem.get_text(strip=True).lower()
                if 'new' in condition_text:
                    condition = "New"
                elif 'refurbished' in condition_text:
                    condition = "Refurbished"
            
            # Image
            image_url = None
            img_elem = container.find('img', class_='s-item__image')
            if img_elem:
                image_url = img_elem.get('src')
            
            # Seller info
            seller = None
            seller_elem = container.find('span', class_='s-item__seller-info-text')
            if seller_elem:
                seller = seller_elem.get_text(strip=True)
            
            return ProductData(
                platform=self.platform_name,
                product_id=product_id,
                name=name,
                price=total_price,
                currency="USD",
                availability=condition,
                url=url,
                image_url=image_url,
                seller=seller
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting eBay product: {e}")
            return None
    
    def get_product_details(self, product_url: str) -> Optional[ProductData]:
        """Get detailed information for a specific eBay product."""
        try:
            response = self._make_request(product_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            product_id = self.extract_product_id(product_url)
            if not product_id:
                return None
            
            # Product name
            name_elem = soup.find('h1', id='x-title-label-lbl')
            if not name_elem:
                return None
            name = name_elem.get_text(strip=True)
            
            # Price
            price = 0.0
            price_selectors = [
                '.price .currentPrice .amount',
                '.price .original .amount',
                '#mainPrice .amount'
            ]
            
            for selector in price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    price_text = elem.get_text(strip=True)
                    price = self._parse_price(price_text)
                    if price > 0:
                        break
            
            # Condition
            condition = "Used"
            condition_elem = soup.find('div', class_='u-flL condText')
            if condition_elem:
                condition_text = condition_elem.get_text(strip=True).lower()
                if 'new' in condition_text:
                    condition = "New"
                elif 'refurbished' in condition_text:
                    condition = "Refurbished"
            
            # Seller
            seller = None
            seller_elem = soup.find('span', class_='mbg-nw')
            if seller_elem:
                seller = seller_elem.get_text(strip=True)
            
            # Image
            image_url = None
            img_elem = soup.find('img', id='icImg')
            if img_elem:
                image_url = img_elem.get('src')
            
            # Category
            category = None
            breadcrumb = soup.select('.breadcrumbs a')
            if breadcrumb and len(breadcrumb) > 1:
                category = breadcrumb[-2].get_text(strip=True)
            
            return ProductData(
                platform=self.platform_name,
                product_id=product_id,
                name=name,
                price=price,
                currency="USD",
                availability=condition,
                url=product_url,
                image_url=image_url,
                seller=seller,
                category=category
            )
            
        except Exception as e:
            self.logger.error(f"Error getting eBay product details: {e}")
            return None
    
    def extract_product_id(self, url: str) -> Optional[str]:
        """Extract product ID from eBay URL."""
        # eBay item ID patterns
        patterns = [
            r'/itm/(\d+)',
            r'item=(\d+)',
            r'hash=item([a-f0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price string to float."""
        if not price_text:
            return 0.0
        
        # Handle price ranges (take the first/lower price)
        if 'to' in price_text.lower():
            price_text = price_text.split('to')[0]
        
        # Remove currency symbols and extract numbers
        price_clean = re.sub(r'[^\d.,]', '', price_text)
        price_clean = price_clean.replace(',', '')
        
        try:
            return float(price_clean)
        except (ValueError, TypeError):
            return 0.0