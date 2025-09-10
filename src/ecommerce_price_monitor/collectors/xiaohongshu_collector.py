"""小红书(Xiaohongshu)商品数据收集器 - Xiaohongshu product data collector."""

import re
import json
import time
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup

from .base_collector import BaseCollector, ProductData
from ..utils.exceptions import CollectorError


class XiaohongshuCollector(BaseCollector):
    """小红书商品数据收集器 - Xiaohongshu product data collector."""
    
    def __init__(self):
        super().__init__("小红书")
        self.base_url = "https://www.xiaohongshu.com"
        self.search_url = "https://www.xiaohongshu.com/search_result"
        self.goods_search_url = "https://www.xiaohongshu.com/goods"
        
        # 小红书专用请求头
        self.session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://www.xiaohongshu.com',
            'Referer': 'https://www.xiaohongshu.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })
    
    def search_products(self, query: str, max_results: int = 20) -> List[ProductData]:
        """在小红书搜索商品 - Search products on Xiaohongshu.
        
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
                # 小红书主要通过API接口获取数据
                api_url = "https://edith.xiaohongshu.com/api/sns/web/v1/search/goods"
                
                params = {
                    'keyword': query,
                    'page': page,
                    'page_size': min(20, max_results - len(products)),
                    'sort': 'general',  # 综合排序
                    'source': 'web_search_result'
                }
                
                try:
                    response = self._make_request(api_url, params=params)
                    data = response.json()
                    
                    if 'data' in data and 'items' in data['data']:
                        items = data['data']['items']
                        
                        for item in items:
                            if len(products) >= max_results:
                                break
                                
                            try:
                                product_data = self._extract_product_from_api(item)
                                if product_data and self.validate_product_data(product_data):
                                    products.append(product_data)
                            except Exception as e:
                                self.logger.warning(f"提取商品信息失败: {e}")
                                continue
                    
                    if not items or len(items) == 0:
                        break
                        
                except Exception as api_error:
                    self.logger.warning(f"API请求失败，尝试网页抓取: {api_error}")
                    # 备用方法：网页抓取
                    web_products = self._search_products_web(query, max_results - len(products))
                    products.extend(web_products)
                    break
                
                page += 1
                time.sleep(2)  # 避免请求过快
                
            except Exception as e:
                self.logger.error(f"小红书搜索错误: {e}")
                break
        
        self.logger.info(f"在小红书找到 {len(products)} 个商品，关键词: {query}")
        return products
    
    def _search_products_web(self, query: str, max_results: int) -> List[ProductData]:
        """网页端商品搜索 - Web-based product search."""
        products = []
        
        try:
            search_url = f"{self.base_url}/search_result"
            params = {
                'keyword': query,
                'source': 'web_search_result'
            }
            
            response = self._make_request(search_url, params=params)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找商品卡片
            product_cards = soup.find_all('div', class_='goods-item') or soup.find_all('a', class_='goods-item')
            
            for card in product_cards[:max_results]:
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
            # 商品基本信息
            product_id = str(item_data.get('id', ''))
            name = item_data.get('title', '').strip()
            
            if not product_id or not name:
                return None
            
            # 价格信息
            price = 0.0
            price_info = item_data.get('price_info', {})
            if price_info:
                # 小红书价格可能有区间
                if 'min_price' in price_info:
                    price = float(price_info['min_price']) / 100  # 通常以分为单位
                elif 'price' in price_info:
                    price = float(price_info['price']) / 100
            
            # 图片
            image_url = None
            if 'cover' in item_data:
                cover_info = item_data['cover']
                if isinstance(cover_info, dict) and 'url' in cover_info:
                    image_url = cover_info['url']
                elif isinstance(cover_info, str):
                    image_url = cover_info
            
            # 店铺信息
            seller = None
            if 'shop_info' in item_data:
                shop_info = item_data['shop_info']
                seller = shop_info.get('name', '') or shop_info.get('shop_name', '')
            
            # 评分和评论
            rating = None
            review_count = None
            
            if 'interact_info' in item_data:
                interact_info = item_data['interact_info']
                review_count = interact_info.get('comment_count', 0)
                
            if 'score' in item_data:
                rating = float(item_data['score'])
            
            # 构建商品URL
            url = f"{self.base_url}/goods/{product_id}"
            
            return ProductData(
                platform=self.platform_name,
                product_id=product_id,
                name=name,
                price=price,
                currency="CNY",
                availability="有货",
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
            # 获取商品链接和ID
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
            title_elem = container.find(['h3', 'div'], class_=re.compile('title|name'))
            if not title_elem:
                title_elem = container.find('img')
                if title_elem:
                    name = title_elem.get('alt', '')
                else:
                    return None
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
                    image_url = urljoin(self.base_url, image_url)
            
            return ProductData(
                platform=self.platform_name,
                product_id=product_id,
                name=name,
                price=price,
                currency="CNY",
                availability="有货",
                url=url,
                image_url=image_url
            )
            
        except Exception as e:
            self.logger.error(f"提取网页商品信息失败: {e}")
            return None
    
    def get_product_details(self, product_url: str) -> Optional[ProductData]:
        """获取小红书商品详细信息 - Get detailed Xiaohongshu product information."""
        try:
            product_id = self.extract_product_id(product_url)
            if not product_id:
                return None
            
            # 尝试API获取商品详情
            api_url = f"https://edith.xiaohongshu.com/api/sns/web/v1/goods/{product_id}"
            
            try:
                response = self._make_request(api_url)
                data = response.json()
                
                if 'data' in data:
                    return self._extract_product_details_from_api(data['data'], product_id, product_url)
                    
            except Exception as api_error:
                self.logger.warning(f"API获取详情失败，尝试网页抓取: {api_error}")
            
            # 备用方法：网页抓取
            response = self._make_request(product_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            return self._extract_product_details_from_html(soup, product_id, product_url)
            
        except Exception as e:
            self.logger.error(f"获取小红书商品详情失败: {e}")
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
            
            # 库存状态
            availability = "有货"
            if 'stock_info' in data:
                stock_info = data['stock_info']
                if stock_info.get('stock_status') == 'sold_out':
                    availability = "缺货"
            
            # 图片
            image_url = None
            if 'images' in data and data['images']:
                image_url = data['images'][0].get('url', '')
            
            # 店铺
            seller = None
            if 'shop_info' in data:
                seller = data['shop_info'].get('name', '')
            
            # 描述
            description = data.get('description', '')
            
            return ProductData(
                platform=self.platform_name,
                product_id=product_id,
                name=name,
                price=price,
                currency="CNY",
                availability=availability,
                url=url,
                image_url=image_url,
                seller=seller,
                description=description
            )
            
        except Exception as e:
            self.logger.error(f"从API提取商品详情失败: {e}")
            return None
    
    def _extract_product_details_from_html(self, soup: BeautifulSoup, product_id: str, url: str) -> Optional[ProductData]:
        """从HTML提取商品详情 - Extract detailed product data from HTML."""
        try:
            # 商品名称
            title_elem = soup.find(['h1', 'div'], class_=re.compile('title|name'))
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
                availability="有货",
                url=url
            )
            
        except Exception as e:
            self.logger.error(f"从HTML提取商品详情失败: {e}")
            return None
    
    def extract_product_id(self, url: str) -> Optional[str]:
        """从小红书URL提取商品ID - Extract product ID from Xiaohongshu URL."""
        patterns = [
            r'/goods/([a-f0-9]+)',
            r'goods_id=([a-f0-9]+)',
            r'/item/([a-f0-9]+)'
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