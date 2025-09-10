"""抖音电商(Douyin)商品数据收集器 - Douyin e-commerce product data collector."""

import re
import json
import time
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup

from .base_collector import BaseCollector, ProductData
from ..utils.exceptions import CollectorError


class DouyinCollector(BaseCollector):
    """抖音电商商品数据收集器 - Douyin e-commerce product data collector."""
    
    def __init__(self):
        super().__init__("抖音电商")
        self.base_url = "https://haohuo.jinritemai.com"
        self.search_url = "https://haohuo.jinritemai.com/views/search/index.html"
        self.api_search_url = "https://haohuo.jinritemai.com/api/index/search"
        
        # 抖音电商专用请求头
        self.session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json',
            'Origin': 'https://haohuo.jinritemai.com',
            'Referer': 'https://haohuo.jinritemai.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest'
        })
    
    def search_products(self, query: str, max_results: int = 20) -> List[ProductData]:
        """在抖音电商搜索商品 - Search products on Douyin e-commerce.
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数量
            
        Returns:
            商品数据列表
        """
        products = []
        page = 1
        
        while len(products) < max_results:
            try:
                # 尝试API搜索
                try:
                    api_products = self._search_products_api(query, page, max_results - len(products))
                    products.extend(api_products)
                    
                    if len(api_products) == 0:
                        break
                        
                except Exception as api_error:
                    self.logger.warning(f"API搜索失败，尝试网页搜索: {api_error}")
                    # 备用网页搜索
                    web_products = self._search_products_web(query, max_results - len(products))
                    products.extend(web_products)
                    break
                
                page += 1
                time.sleep(2)  # 避免请求过快
                
            except Exception as e:
                self.logger.error(f"抖音电商搜索错误: {e}")
                break
        
        self.logger.info(f"在抖音电商找到 {len(products)} 个商品，关键词: {query}")
        return products
    
    def _search_products_api(self, query: str, page: int, limit: int) -> List[ProductData]:
        """通过API搜索商品 - Search products via API."""
        products = []
        
        try:
            params = {
                'keyword': query,
                'page': page,
                'size': min(20, limit),
                'sort_type': 0,  # 综合排序
                'source': 'pc'
            }
            
            response = self._make_request(self.api_search_url, params=params)
            data = response.json()
            
            if data.get('status_code') == 0 and 'data' in data:
                items = data['data'].get('products', [])
                
                for item in items:
                    if len(products) >= limit:
                        break
                        
                    try:
                        product_data = self._extract_product_from_api(item)
                        if product_data and self.validate_product_data(product_data):
                            products.append(product_data)
                    except Exception as e:
                        self.logger.warning(f"提取API商品信息失败: {e}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"API搜索失败: {e}")
            raise
        
        return products
    
    def _search_products_web(self, query: str, limit: int) -> List[ProductData]:
        """网页端商品搜索 - Web-based product search."""
        products = []
        
        try:
            params = {'keyword': query}
            response = self._make_request(self.search_url, params=params)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找商品容器
            product_cards = (soup.find_all('div', class_='product-card') or 
                           soup.find_all('div', class_='goods-item') or
                           soup.find_all('a', class_='product-link'))
            
            for card in product_cards[:limit]:
                try:
                    product_data = self._extract_product_from_web(card)
                    if product_data and self.validate_product_data(product_data):
                        products.append(product_data)
                except Exception as e:
                    self.logger.warning(f"提取网页商品信息失败: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"网页搜索失败: {e}")
        
        return products
    
    def _extract_product_from_api(self, item_data: Dict) -> Optional[ProductData]:
        """从API数据提取商品信息 - Extract product data from API response."""
        try:
            # 基本信息
            product_id = str(item_data.get('product_id', ''))
            name = item_data.get('title', '').strip()
            
            if not product_id or not name:
                return None
            
            # 价格信息 - 抖音电商价格通常以分为单位
            price = 0.0
            price_info = item_data.get('price_info', {})
            if price_info:
                if 'min_price' in price_info:
                    price = float(price_info['min_price']) / 100
                elif 'price' in price_info:
                    price = float(price_info['price']) / 100
            elif 'price' in item_data:
                price = float(item_data['price']) / 100
            
            # 图片
            image_url = None
            images = item_data.get('images', [])
            if images and len(images) > 0:
                image_url = images[0]
                if not image_url.startswith('http'):
                    image_url = 'https:' + image_url if image_url.startswith('//') else None
            
            # 店铺信息
            seller = None
            shop_info = item_data.get('shop_info', {})
            if shop_info:
                seller = shop_info.get('shop_name', '') or shop_info.get('name', '')
            
            # 销量信息
            review_count = None
            if 'sales_count' in item_data:
                review_count = int(item_data['sales_count'])
            elif 'sold_count' in item_data:
                review_count = int(item_data['sold_count'])
            
            # 评分
            rating = None
            if 'rating' in item_data:
                rating = float(item_data['rating'])
            elif 'score' in item_data:
                rating = float(item_data['score'])
            
            # 构建商品URL
            url = f"{self.base_url}/views/product/item2?id={product_id}"
            if 'url' in item_data:
                url = item_data['url']
                if not url.startswith('http'):
                    url = urljoin(self.base_url, url)
            
            return ProductData(
                platform=self.platform_name,
                product_id=product_id,
                name=name,
                price=price,
                currency="CNY",
                availability="有库存",
                url=url,
                image_url=image_url,
                rating=rating,
                review_count=review_count,
                seller=seller
            )
            
        except Exception as e:
            self.logger.error(f"提取API商品数据失败: {e}")
            return None
    
    def _extract_product_from_web(self, container) -> Optional[ProductData]:
        """从网页容器提取商品信息 - Extract product data from web container."""
        try:
            # 获取商品链接
            link_elem = container if container.name == 'a' else container.find('a')
            if not link_elem:
                return None
            
            url = link_elem.get('href', '')
            if url.startswith('/'):
                url = urljoin(self.base_url, url)
            
            product_id = self.extract_product_id(url)
            if not product_id:
                return None
            
            # 商品名称
            title_elem = (container.find(['h3', 'h4', 'span'], class_=re.compile('title|name')) or
                         container.find('img'))
            
            if not title_elem:
                return None
            
            if title_elem.name == 'img':
                name = title_elem.get('alt', '').strip()
            else:
                name = title_elem.get_text(strip=True)
            
            if not name:
                return None
            
            # 价格
            price = 0.0
            price_elem = container.find(['span', 'div'], class_=re.compile('price'))
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self._parse_price(price_text)
            
            # 图片
            image_url = None
            img_elem = container.find('img')
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
                if image_url and not image_url.startswith('http'):
                    image_url = 'https:' + image_url if image_url.startswith('//') else urljoin(self.base_url, image_url)
            
            # 销量
            sales_elem = container.find(['span', 'div'], string=re.compile(r'销量|已售'))
            sales_count = None
            if sales_elem:
                sales_text = sales_elem.get_text(strip=True)
                sales_count = self._parse_sales_count(sales_text)
            
            return ProductData(
                platform=self.platform_name,
                product_id=product_id,
                name=name,
                price=price,
                currency="CNY",
                availability="有库存",
                url=url,
                image_url=image_url,
                review_count=sales_count
            )
            
        except Exception as e:
            self.logger.error(f"提取网页商品信息失败: {e}")
            return None
    
    def get_product_details(self, product_url: str) -> Optional[ProductData]:
        """获取抖音电商商品详细信息 - Get detailed Douyin product information."""
        try:
            product_id = self.extract_product_id(product_url)
            if not product_id:
                return None
            
            # 尝试API获取商品详情
            try:
                api_url = f"https://haohuo.jinritemai.com/api/product/detail"
                params = {'product_id': product_id}
                
                response = self._make_request(api_url, params=params)
                data = response.json()
                
                if data.get('status_code') == 0 and 'data' in data:
                    return self._extract_product_details_from_api(data['data'], product_id, product_url)
                    
            except Exception as api_error:
                self.logger.warning(f"API获取详情失败，尝试网页抓取: {api_error}")
            
            # 备用方法：网页抓取
            response = self._make_request(product_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            return self._extract_product_details_from_html(soup, product_id, product_url)
            
        except Exception as e:
            self.logger.error(f"获取抖音电商商品详情失败: {e}")
            return None
    
    def _extract_product_details_from_api(self, data: Dict, product_id: str, url: str) -> Optional[ProductData]:
        """从API数据提取商品详情 - Extract detailed product data from API."""
        try:
            name = data.get('title', '').strip()
            if not name:
                return None
            
            # 价格
            price = 0.0
            price_info = data.get('price_info', {})
            if price_info and 'price' in price_info:
                price = float(price_info['price']) / 100
            
            # 库存
            availability = "有库存"
            if 'stock' in data and data['stock'] <= 0:
                availability = "缺货"
            
            # 图片
            image_url = None
            if 'images' in data and data['images']:
                image_url = data['images'][0]
            
            # 店铺
            seller = None
            if 'shop_info' in data:
                seller = data['shop_info'].get('shop_name', '')
            
            # 销量和评分
            review_count = data.get('sales_count', None)
            rating = data.get('rating', None)
            
            return ProductData(
                platform=self.platform_name,
                product_id=product_id,
                name=name,
                price=price,
                currency="CNY",
                availability=availability,
                url=url,
                image_url=image_url,
                rating=rating,
                review_count=review_count,
                seller=seller
            )
            
        except Exception as e:
            self.logger.error(f"从API提取商品详情失败: {e}")
            return None
    
    def _extract_product_details_from_html(self, soup: BeautifulSoup, product_id: str, url: str) -> Optional[ProductData]:
        """从HTML提取商品详情 - Extract detailed product data from HTML."""
        try:
            # 商品名称
            title_elem = soup.find(['h1', 'h2'], class_=re.compile('title|name'))
            if not title_elem:
                return None
            
            name = title_elem.get_text(strip=True)
            
            # 价格
            price = 0.0
            price_elem = soup.find(['span', 'div'], class_=re.compile('price'))
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self._parse_price(price_text)
            
            return ProductData(
                platform=self.platform_name,
                product_id=product_id,
                name=name,
                price=price,
                currency="CNY",
                availability="有库存",
                url=url
            )
            
        except Exception as e:
            self.logger.error(f"从HTML提取商品详情失败: {e}")
            return None
    
    def extract_product_id(self, url: str) -> Optional[str]:
        """从抖音电商URL提取商品ID - Extract product ID from Douyin URL."""
        patterns = [
            r'id=([a-f0-9]+)',
            r'/item2\?id=([a-f0-9]+)',
            r'/product/([a-f0-9]+)',
            r'product_id=([a-f0-9]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _parse_price(self, price_text: str) -> float:
        """解析价格字符串 - Parse price string to float."""
        if not price_text:
            return 0.0
        
        # 移除货币符号和中文字符
        price_clean = re.sub(r'[^\d.,\-]', '', price_text)
        
        # 处理价格区间，取较低价格
        if '-' in price_clean:
            prices = price_clean.split('-')
            if len(prices) >= 1:
                price_clean = prices[0]
        
        price_clean = price_clean.replace(',', '')
        
        try:
            return float(price_clean)
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_sales_count(self, sales_text: str) -> Optional[int]:
        """解析销量数字 - Parse sales count."""
        if not sales_text:
            return None
        
        try:
            # 处理万+、千+等格式
            sales_text = sales_text.replace('销量', '').replace('已售', '').strip()
            
            if '万+' in sales_text or '万' in sales_text:
                num = re.search(r'(\d+\.?\d*)万', sales_text)
                if num:
                    return int(float(num.group(1)) * 10000)
            elif '千+' in sales_text or '千' in sales_text:
                num = re.search(r'(\d+\.?\d*)千', sales_text)
                if num:
                    return int(float(num.group(1)) * 1000)
            else:
                # 直接数字
                num = re.search(r'(\d+)', sales_text.replace('+', ''))
                if num:
                    return int(num.group(1))
        except (ValueError, TypeError):
            pass
        
        return None