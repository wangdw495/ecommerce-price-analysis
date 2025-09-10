"""Amazon product data collector."""

import re
import json
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

from .base_collector import BaseCollector, ProductData
from ..utils.exceptions import CollectorError


class AmazonCollector(BaseCollector):
    """Amazon-specific product data collector."""
    
    def __init__(self):
        super().__init__("Amazon")
        self.base_url = "https://www.amazon.com"
        self.search_url = "https://www.amazon.com/s"
        
        # Amazon-specific headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        })
    
    def search_products(self, query: str, max_results: int = 20) -> List[ProductData]:
        """Search for products on Amazon.
        
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
                    'k': query,
                    'ref': 'sr_pg_' + str(page),
                    'page': page
                }
                
                response = self._make_request(self.search_url, params=params)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find product containers
                product_containers = soup.find_all(
                    'div', 
                    {'data-component-type': 's-search-result'}
                )
                
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
                self.logger.error(f"Error searching Amazon: {e}")
                break
        
        self.logger.info(f"Found {len(products)} products for query: {query}")
        return products
    
    def _extract_product_from_search(self, container) -> Optional[ProductData]:
        """Extract product data from search result container.
        
        Args:
            container: BeautifulSoup element containing product info
            
        Returns:
            ProductData object or None
        """
        try:
            # Product name and URL
            title_elem = container.find('h2', class_='a-size-mini')
            if not title_elem:
                return None
                
            link_elem = title_elem.find('a')
            if not link_elem:
                return None
                
            name = link_elem.get_text(strip=True)
            relative_url = link_elem.get('href')
            if not relative_url:
                return None
                
            url = urljoin(self.base_url, relative_url)
            product_id = self.extract_product_id(url)
            
            if not product_id:
                return None
            
            # Price
            price_container = container.find('span', class_='a-price')
            price = 0.0
            if price_container:
                price_elem = price_container.find('span', class_='a-offscreen')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = self._parse_price(price_text)
            
            # Rating
            rating = None
            rating_elem = container.find('span', class_='a-icon-alt')
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # Review count
            review_count = None
            review_elem = container.find('a', class_='a-link-normal')
            if review_elem:
                review_text = review_elem.get_text()
                review_match = re.search(r'([\d,]+)', review_text)
                if review_match:
                    review_count = int(review_match.group(1).replace(',', ''))
            
            # Image
            image_url = None
            img_elem = container.find('img', class_='s-image')
            if img_elem:
                image_url = img_elem.get('src')
            
            return ProductData(
                platform=self.platform_name,
                product_id=product_id,
                name=name,
                price=price,
                currency="USD",
                availability="Available" if price > 0 else "Unavailable",
                url=url,
                image_url=image_url,
                rating=rating,
                review_count=review_count
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting product from search: {e}")
            return None
    
    def get_product_details(self, product_url: str) -> Optional[ProductData]:
        """Get detailed information for a specific Amazon product.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            Product data or None if not found
        """
        try:
            response = self._make_request(product_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            product_id = self.extract_product_id(product_url)
            if not product_id:
                return None
            
            # Product name
            name_selectors = [
                '#productTitle',
                'h1.a-size-large',
                'h1.a-size-base-plus'
            ]
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
                '.a-price-whole',
                '#priceblock_dealprice',
                '#priceblock_ourprice',
                '.a-price .a-offscreen'
            ]
            
            for selector in price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    price_text = elem.get_text(strip=True)
                    price = self._parse_price(price_text)
                    if price > 0:
                        break
            
            # Availability
            availability = "Available"
            avail_elem = soup.select_one('#availability span')
            if avail_elem:
                avail_text = avail_elem.get_text(strip=True).lower()
                if 'out of stock' in avail_text or 'unavailable' in avail_text:
                    availability = "Out of Stock"
                elif 'in stock' in avail_text:
                    availability = "In Stock"
            
            # Rating and reviews
            rating = None
            review_count = None
            
            rating_elem = soup.select_one('span.a-icon-alt')
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            review_elem = soup.select_one('#acrCustomerReviewText')
            if review_elem:
                review_text = review_elem.get_text()
                review_match = re.search(r'([\d,]+)', review_text)
                if review_match:
                    review_count = int(review_match.group(1).replace(',', ''))
            
            # Brand
            brand = None
            brand_elem = soup.select_one('#bylineInfo')
            if brand_elem:
                brand = brand_elem.get_text(strip=True)
            
            # Category
            category = None
            breadcrumb = soup.select('#wayfinding-breadcrumbs_feature_div a')
            if breadcrumb:
                category = breadcrumb[-1].get_text(strip=True)
            
            # Image
            image_url = None
            img_elem = soup.select_one('#landingImage, #imgBlkFront')
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
            
            # Description
            description = None
            desc_elem = soup.select_one('#feature-bullets ul')
            if desc_elem:
                bullets = [li.get_text(strip=True) for li in desc_elem.find_all('li')]
                description = ' | '.join(bullets[:5])  # Limit to 5 bullet points
            
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
                review_count=review_count,
                brand=brand,
                category=category,
                description=description
            )
            
        except Exception as e:
            self.logger.error(f"Error getting Amazon product details: {e}")
            return None
    
    def extract_product_id(self, url: str) -> Optional[str]:
        """Extract product ID (ASIN) from Amazon URL.
        
        Args:
            url: Product URL
            
        Returns:
            ASIN or None if not found
        """
        # Common Amazon URL patterns for ASIN extraction
        patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/product/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'asin=([A-Z0-9]{10})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price string to float.
        
        Args:
            price_text: Price string (e.g., "$19.99", "$1,234.56")
            
        Returns:
            Price as float
        """
        if not price_text:
            return 0.0
        
        # Remove currency symbols and extract numbers
        price_clean = re.sub(r'[^\d.,]', '', price_text)
        price_clean = price_clean.replace(',', '')
        
        try:
            return float(price_clean)
        except (ValueError, TypeError):
            return 0.0