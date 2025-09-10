"""Walmart product data collector."""

import re
import json
from typing import List, Optional
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup

from .base_collector import BaseCollector, ProductData
from ..utils.exceptions import CollectorError


class WalmartCollector(BaseCollector):
    """Walmart-specific product data collector."""
    
    def __init__(self):
        super().__init__("Walmart")
        self.base_url = "https://www.walmart.com"
        self.search_url = "https://www.walmart.com/search"
    
    def search_products(self, query: str, max_results: int = 20) -> List[ProductData]:
        """Search for products on Walmart.
        
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
                    'query': query,
                    'page': page
                }
                
                response = self._make_request(self.search_url, params=params)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find JSON data in script tags
                script_tags = soup.find_all('script')
                product_data = None
                
                for script in script_tags:
                    if script.string and 'window.__WML_REDUX_INITIAL_STATE__' in script.string:
                        # Extract JSON data from Walmart's Redux state
                        try:
                            json_start = script.string.find('{')
                            json_end = script.string.rfind('}') + 1
                            json_data = script.string[json_start:json_end]
                            data = json.loads(json_data)
                            
                            # Navigate through the data structure to find products
                            if 'searchProduct' in data and 'products' in data['searchProduct']:
                                products_data = data['searchProduct']['products']
                                for item in products_data:
                                    if len(products) >= max_results:
                                        break
                                    try:
                                        product = self._extract_product_from_json(item)
                                        if product and self.validate_product_data(product):
                                            products.append(product)
                                    except Exception as e:
                                        self.logger.warning(f"Error extracting product: {e}")
                                        continue
                            break
                        except json.JSONDecodeError:
                            continue
                
                # Fallback to HTML parsing if JSON extraction fails
                if not products:
                    products.extend(self._extract_from_html(soup, max_results - len(products)))
                
                if len(products) == 0:
                    self.logger.info("No more products found")
                    break
                
                page += 1
                
            except Exception as e:
                self.logger.error(f"Error searching Walmart: {e}")
                break
        
        self.logger.info(f"Found {len(products)} products for query: {query}")
        return products
    
    def _extract_product_from_json(self, item: dict) -> Optional[ProductData]:
        """Extract product data from JSON structure."""
        try:
            # Basic product info
            product_id = str(item.get('id', ''))
            name = item.get('name', '')
            
            if not product_id or not name:
                return None
            
            # Price
            price = 0.0
            price_info = item.get('priceInfo', {})
            if 'currentPrice' in price_info:
                price = float(price_info['currentPrice'].get('price', 0))
            
            # URL
            url = f"{self.base_url}/ip/{item.get('canonicalUrl', '')}"
            if item.get('canonicalUrl'):
                url = urljoin(self.base_url, item['canonicalUrl'])
            
            # Image
            image_url = None
            if 'image' in item and 'src' in item['image']:
                image_url = item['image']['src']
            
            # Rating
            rating = None
            if 'averageRating' in item:
                rating = float(item['averageRating'])
            
            # Review count
            review_count = None
            if 'numberOfReviews' in item:
                review_count = int(item['numberOfReviews'])
            
            # Brand
            brand = item.get('brand', None)
            
            # Availability
            availability = "Available"
            if item.get('availabilityStatus') == 'OUT_OF_STOCK':
                availability = "Out of Stock"
            
            return ProductData(
                platform=self.platform_name,
                product_id=product_id,
                name=name,
                price=price,
                currency="USD",
                availability=availability,
                url=url,
                image_url=image_url,
                rating=rating,
                review_count=review_count,
                brand=brand
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting Walmart product from JSON: {e}")
            return None
    
    def _extract_from_html(self, soup: BeautifulSoup, max_results: int) -> List[ProductData]:
        """Fallback HTML extraction method."""
        products = []
        
        # Find product containers using common selectors
        selectors = [
            '[data-testid="item-stack"]',
            '.search-result-gridview-item',
            '.search-result-product-tile'
        ]
        
        containers = []
        for selector in selectors:
            containers = soup.select(selector)
            if containers:
                break
        
        for container in containers[:max_results]:
            try:
                product_data = self._extract_product_from_html(container)
                if product_data and self.validate_product_data(product_data):
                    products.append(product_data)
            except Exception as e:
                self.logger.warning(f"Error extracting product from HTML: {e}")
                continue
        
        return products
    
    def _extract_product_from_html(self, container) -> Optional[ProductData]:
        """Extract product data from HTML container."""
        try:
            # Product name and URL
            link_elem = container.find('a')
            if not link_elem:
                return None
            
            url = urljoin(self.base_url, link_elem.get('href', ''))
            product_id = self.extract_product_id(url)
            
            # Name
            name_elem = container.find(['span', 'h3', 'h4'], string=True)
            if not name_elem:
                return None
            name = name_elem.get_text(strip=True)
            
            # Price
            price = 0.0
            price_elem = container.find(['span', 'div'], string=re.compile(r'\$[\d,]+\.?\d*'))
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self._parse_price(price_text)
            
            # Image
            image_url = None
            img_elem = container.find('img')
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
            
            if not product_id:
                return None
            
            return ProductData(
                platform=self.platform_name,
                product_id=product_id,
                name=name,
                price=price,
                currency="USD",
                availability="Available",
                url=url,
                image_url=image_url
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting Walmart product from HTML: {e}")
            return None
    
    def get_product_details(self, product_url: str) -> Optional[ProductData]:
        """Get detailed information for a specific Walmart product."""
        try:
            response = self._make_request(product_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            product_id = self.extract_product_id(product_url)
            if not product_id:
                return None
            
            # Try to extract from JSON-LD structured data
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                try:
                    data = json.loads(json_ld.string)
                    if isinstance(data, list):
                        data = data[0]
                    
                    if data.get('@type') == 'Product':
                        name = data.get('name', '')
                        
                        # Price from structured data
                        price = 0.0
                        offers = data.get('offers', {})
                        if isinstance(offers, list):
                            offers = offers[0]
                        if 'price' in offers:
                            price = float(offers['price'])
                        
                        # Image
                        image_url = None
                        if 'image' in data:
                            image_url = data['image'][0] if isinstance(data['image'], list) else data['image']
                        
                        # Brand
                        brand = None
                        if 'brand' in data:
                            brand_data = data['brand']
                            if isinstance(brand_data, dict):
                                brand = brand_data.get('name')
                            else:
                                brand = str(brand_data)
                        
                        # Rating
                        rating = None
                        if 'aggregateRating' in data:
                            rating = float(data['aggregateRating'].get('ratingValue', 0))
                        
                        # Availability
                        availability = "Available"
                        if offers.get('availability') == 'http://schema.org/OutOfStock':
                            availability = "Out of Stock"
                        
                        return ProductData(
                            platform=self.platform_name,
                            product_id=product_id,
                            name=name,
                            price=price,
                            currency="USD",
                            availability=availability,
                            url=product_url,
                            image_url=image_url,
                            rating=rating,
                            brand=brand
                        )
                except json.JSONDecodeError:
                    pass
            
            # Fallback to HTML parsing
            return self._extract_details_from_html(soup, product_id, product_url)
            
        except Exception as e:
            self.logger.error(f"Error getting Walmart product details: {e}")
            return None
    
    def _extract_details_from_html(self, soup: BeautifulSoup, product_id: str, url: str) -> Optional[ProductData]:
        """Extract product details from HTML."""
        try:
            # Product name
            name_selectors = ['h1[data-automation-id="product-title"]', 'h1.prod-ProductTitle']
            name = None
            for selector in name_selectors:
                elem = soup.select_one(selector)
                if elem:
                    name = elem.get_text(strip=True)
                    break
            
            if not name:
                return None
            
            # Price
            price = 0.0
            price_selectors = [
                '[data-automation-id="product-price"] span',
                '.price-current span',
                '.price span'
            ]
            
            for selector in price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    price_text = elem.get_text(strip=True)
                    price = self._parse_price(price_text)
                    if price > 0:
                        break
            
            return ProductData(
                platform=self.platform_name,
                product_id=product_id,
                name=name,
                price=price,
                currency="USD",
                availability="Available",
                url=url
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting Walmart details from HTML: {e}")
            return None
    
    def extract_product_id(self, url: str) -> Optional[str]:
        """Extract product ID from Walmart URL."""
        # Walmart product ID patterns
        patterns = [
            r'/ip/[^/]+/(\d+)',
            r'product_id=(\d+)',
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
        
        # Remove currency symbols and extract numbers
        price_clean = re.sub(r'[^\d.,]', '', price_text)
        price_clean = price_clean.replace(',', '')
        
        try:
            return float(price_clean)
        except (ValueError, TypeError):
            return 0.0