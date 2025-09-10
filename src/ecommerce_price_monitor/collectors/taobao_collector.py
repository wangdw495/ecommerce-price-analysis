"""淘宝(Taobao)商品数据收集器 - Taobao product data collector."""

import re
import json
import time
import base64
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, quote, unquote
from bs4 import BeautifulSoup

from .base_collector import BaseCollector, ProductData
from ..utils.exceptions import CollectorError


class TaobaoCollector(BaseCollector):
    """淘宝商品数据收集器 - Taobao product data collector."""
    
    def __init__(self):
        super().__init__("淘宝")
        self.base_url = "https://www.taobao.com"
        self.search_url = "https://s.taobao.com/search"
        self.item_url = "https://item.taobao.com/item.htm"
        
        # 淘宝专用请求头
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.taobao.com/'
        })
    
    def search_products(self, query: str, max_results: int = 20) -> List[ProductData]:
        """在淘宝搜索商品 - Search products on Taobao.
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数量
            
        Returns:
            商品数据列表
        """
        products = []
        page = 0
        
        while len(products) < max_results:
            try:
                params = {
                    'q': query,
                    's': page * 44,  # 淘宝分页参数
                    'imgfile': '',
                    'initiative_id': 'staobaoz_20231201',
                    'ie': 'utf8'
                }
                
                response = self._make_request(self.search_url, params=params)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 查找商品容器 - 淘宝的HTML结构经常变化
                product_containers = (soup.find_all('div', class_='item J_MouserOnverReq') or 
                                    soup.find_all('div', class_='item') or
                                    soup.find_all('div', {'data-category': 'auctions'}))
                
                # 尝试从JSON数据中获取商品信息
                if not product_containers:
                    json_data = self._extract_json_data(response.text)
                    if json_data:
                        products.extend(self._parse_json_products(json_data, max_results - len(products)))
                        break
                
                if not product_containers:
                    self.logger.info("未找到更多商品")
                    break
                
                for container in product_containers:
                    if len(products) >= max_results:
                        break
                        
                    try:
                        product_data = self._extract_product_from_search(container)
                        if product_data and self.validate_product_data(product_data):
                            products.append(product_data)
                    except Exception as e:
                        self.logger.warning(f"提取商品信息失败: {e}")
                        continue
                
                page += 1
                # 增加延迟避免反爬
                time.sleep(3)
                
            except Exception as e:
                self.logger.error(f"淘宝搜索错误: {e}")
                break
        
        self.logger.info(f"在淘宝找到 {len(products)} 个商品，关键词: {query}")
        return products
    
    def _extract_json_data(self, html_content: str) -> Optional[Dict]:
        """从HTML中提取JSON数据 - Extract JSON data from HTML."""
        try:
            # 查找包含商品数据的JavaScript变量
            patterns = [
                r'g_page_config\s*=\s*({.+?});',
                r'window\.g_config\s*=\s*({.+?});',
                r'__sea\.data\s*=\s*({.+?});'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html_content, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _parse_json_products(self, json_data: Dict, max_count: int) -> List[ProductData]:
        """解析JSON数据中的商品信息 - Parse products from JSON data."""
        products = []
        
        try:
            # 淘宝JSON结构可能包含商品列表
            if 'mods' in json_data:
                for mod in json_data['mods'].values():
                    if isinstance(mod, dict) and 'data' in mod:
                        if 'auctions' in mod['data']:
                            for auction in mod['data']['auctions']:
                                if len(products) >= max_count:
                                    break
                                product = self._parse_auction_data(auction)
                                if product:
                                    products.append(product)
        except Exception as e:
            self.logger.error(f"解析JSON商品数据失败: {e}")
        
        return products
    
    def _parse_auction_data(self, auction_data: Dict) -> Optional[ProductData]:
        """解析拍卖商品数据 - Parse auction product data."""
        try:
            product_id = str(auction_data.get('nid', ''))
            name = auction_data.get('title', '').strip()
            
            if not product_id or not name:
                return None
            
            # 价格
            price = 0.0
            if 'view_price' in auction_data:
                price = self._parse_price(auction_data['view_price'])
            elif 'price' in auction_data:
                price = float(auction_data['price'])
            
            # URL
            url = auction_data.get('detail_url', '')
            if url and not url.startswith('http'):
                url = 'https:' + url if url.startswith('//') else self.base_url + url
            
            # 图片
            image_url = auction_data.get('pic_url', '')
            if image_url and not image_url.startswith('http'):
                image_url = 'https:' + image_url if image_url.startswith('//') else None
            
            # 店铺
            seller = auction_data.get('nick', '') or auction_data.get('shopname', '')
            
            # 销量
            sales_count = None
            if 'view_sales' in auction_data:
                sales_text = str(auction_data['view_sales'])
                sales_count = self._parse_sales_count(sales_text)
            
            return ProductData(
                platform=self.platform_name,
                product_id=product_id,
                name=name,
                price=price,
                currency="CNY",
                availability="有货",
                url=url,
                image_url=image_url,
                seller=seller,
                review_count=sales_count
            )
            
        except Exception as e:
            self.logger.error(f"解析拍卖数据失败: {e}")
            return None
    
    def _extract_product_from_search(self, container) -> Optional[ProductData]:
        """从搜索结果容器中提取商品数据 - Extract product data from search result container."""
        try:
            # 商品ID和链接
            link_elem = container.find('a', class_='J_ClickStat') or container.find('a')
            if not link_elem:
                return None
            
            url = link_elem.get('href', '')
            if url.startswith('//'):
                url = 'https:' + url
            elif not url.startswith('http'):
                url = urljoin(self.base_url, url)
            
            product_id = self.extract_product_id(url)
            if not product_id:
                return None
            
            # 商品名称
            title_elem = (container.find('div', class_='title') or 
                         container.find('a', class_='J_ClickStat'))
            
            if not title_elem:
                return None
            
            name = title_elem.get_text(strip=True)
            if not name:
                return None
            
            # 清理HTML标签和特殊字符
            name = re.sub(r'<[^>]+>', '', name)
            name = ' '.join(name.split())
            
            # 价格
            price = 0.0
            price_elem = (container.find('strong', class_='price') or 
                         container.find('div', class_='price') or
                         container.find('span', class_='price'))
            
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self._parse_price(price_text)
            
            # 销量/评论数
            review_count = None
            sales_elem = (container.find('div', class_='deal-cnt') or 
                         container.find('span', class_='deal-cnt'))
            
            if sales_elem:
                sales_text = sales_elem.get_text(strip=True)
                review_count = self._parse_sales_count(sales_text)
            
            # 店铺
            seller = None
            shop_elem = (container.find('div', class_='shop') or 
                        container.find('a', class_='shopname'))
            
            if shop_elem:
                seller = shop_elem.get_text(strip=True)
            
            # 图片
            image_url = None
            img_elem = container.find('img')
            if img_elem:
                image_url = (img_elem.get('src') or 
                           img_elem.get('data-src') or 
                           img_elem.get('data-ks-lazyload'))
                
                if image_url and image_url.startswith('//'):
                    image_url = 'https:' + image_url
            
            return ProductData(
                platform=self.platform_name,
                product_id=str(product_id),
                name=name,
                price=price,
                currency="CNY",
                availability="有货",
                url=url,
                image_url=image_url,
                seller=seller,
                review_count=review_count
            )
            
        except Exception as e:
            self.logger.error(f"提取淘宝商品信息失败: {e}")
            return None
    
    def get_product_details(self, product_url: str) -> Optional[ProductData]:
        """获取淘宝商品详细信息 - Get detailed Taobao product information."""
        try:
            response = self._make_request(product_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            product_id = self.extract_product_id(product_url)
            if not product_id:
                return None
            
            # 尝试从JSON数据获取商品信息
            json_data = self._extract_json_data(response.text)
            if json_data:
                product_info = self._extract_product_from_json(json_data, product_id)
                if product_info:
                    return product_info
            
            # 备用HTML解析方法
            return self._extract_product_from_html(soup, product_id, product_url)
            
        except Exception as e:
            self.logger.error(f"获取淘宝商品详情失败: {e}")
            return None
    
    def _extract_product_from_json(self, json_data: Dict, product_id: str) -> Optional[ProductData]:
        """从JSON数据提取商品详情 - Extract product details from JSON data."""
        try:
            # 查找商品信息
            if 'item' in json_data:
                item_data = json_data['item']
                
                name = item_data.get('title', '').strip()
                if not name:
                    return None
                
                # 价格信息
                price = 0.0
                if 'price' in item_data:
                    price = float(item_data['price'])
                elif 'priceRange' in item_data:
                    price_range = item_data['priceRange']
                    if isinstance(price_range, list) and len(price_range) > 0:
                        price = float(price_range[0])
                
                # 图片
                image_url = None
                if 'images' in item_data and item_data['images']:
                    image_url = item_data['images'][0]
                    if image_url.startswith('//'):
                        image_url = 'https:' + image_url
                
                # 店铺信息
                seller = item_data.get('shopName', '')
                
                return ProductData(
                    platform=self.platform_name,
                    product_id=product_id,
                    name=name,
                    price=price,
                    currency="CNY",
                    availability="有货",
                    url=f"https://item.taobao.com/item.htm?id={product_id}",
                    image_url=image_url,
                    seller=seller
                )
                
        except Exception as e:
            self.logger.error(f"从JSON提取商品信息失败: {e}")
        
        return None
    
    def _extract_product_from_html(self, soup: BeautifulSoup, product_id: str, url: str) -> Optional[ProductData]:
        """从HTML提取商品详情 - Extract product details from HTML."""
        try:
            # 商品标题
            title_elem = (soup.find('div', class_='tb-detail-hd') or 
                         soup.find('h1', class_='tb-main-title') or
                         soup.find('title'))
            
            if not title_elem:
                return None
            
            name = title_elem.get_text(strip=True)
            if not name:
                return None
            
            # 价格 - 淘宝价格通常通过AJAX加载
            price = 0.0
            price_elem = soup.find('span', class_='tb-rmb-num')
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
            self.logger.error(f"从HTML提取商品信息失败: {e}")
            return None
    
    def extract_product_id(self, url: str) -> Optional[str]:
        """从淘宝URL提取商品ID - Extract product ID from Taobao URL."""
        patterns = [
            r'id=(\d+)',
            r'/item\.htm.*?id[=:](\d+)',
            r'item\.taobao\.com/item\.htm.*?id[=:](\d+)',
            r'/(\d+)\.htm'
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
            sales_text = sales_text.replace('人付款', '').replace('笔交易', '').strip()
            
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