"""京东(JD.com)商品数据收集器 - JD.com product data collector."""

import re
import json
import time
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup

from .base_collector import BaseCollector, ProductData
from ..utils.exceptions import CollectorError


class JDCollector(BaseCollector):
    """京东商品数据收集器 - JD.com product data collector."""
    
    def __init__(self):
        super().__init__("京东")
        self.base_url = "https://www.jd.com"
        self.search_url = "https://search.jd.com/Search"
        self.item_url = "https://item.jd.com"
        
        # 京东专用请求头
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def search_products(self, query: str, max_results: int = 20) -> List[ProductData]:
        """在京东搜索商品 - Search products on JD.com.
        
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
                params = {
                    'keyword': query,
                    'enc': 'utf-8',
                    'page': page,
                    'wq': query,
                    's': (page - 1) * 30 + 1  # 京东分页参数
                }
                
                response = self._make_request(self.search_url, params=params)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 查找商品容器
                product_containers = soup.find_all('div', class_='gl-i-wrap')
                
                if not product_containers:
                    # 尝试其他可能的选择器
                    product_containers = soup.find_all('li', {'data-sku': True})
                
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
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"京东搜索错误: {e}")
                break
        
        self.logger.info(f"在京东找到 {len(products)} 个商品，关键词: {query}")
        return products
    
    def _extract_product_from_search(self, container) -> Optional[ProductData]:
        """从搜索结果容器中提取商品数据 - Extract product data from search result container."""
        try:
            # 商品ID
            product_id = container.get('data-sku')
            if not product_id:
                # 尝试从链接中提取
                link_elem = container.find('a')
                if link_elem:
                    href = link_elem.get('href', '')
                    product_id = self.extract_product_id(href)
            
            if not product_id:
                return None
            
            # 商品名称和链接
            title_elem = container.find('div', class_='p-name') or container.find('em')
            if not title_elem:
                return None
            
            name = title_elem.get_text(strip=True)
            if not name:
                return None
            
            # 清理商品名称
            name = re.sub(r'<[^>]+>', '', name)  # 移除HTML标签
            name = ' '.join(name.split())  # 清理空白字符
            
            # 商品链接
            link_elem = container.find('a')
            url = ""
            if link_elem:
                href = link_elem.get('href', '')
                if href.startswith('//'):
                    url = 'https:' + href
                elif href.startswith('/'):
                    url = urljoin(self.base_url, href)
                else:
                    url = href
            
            if not url:
                url = f"https://item.jd.com/{product_id}.html"
            
            # 价格信息
            price = 0.0
            price_elem = (container.find('div', class_='p-price') or 
                         container.find('span', class_='p-price') or
                         container.find('em', {'data-price': True}))
            
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                if not price_text and price_elem.get('data-price'):
                    price_text = price_elem.get('data-price')
                price = self._parse_price(price_text)
            
            # 评价信息
            rating = None
            review_count = None
            
            # 评分
            rating_elem = container.find('div', class_='p-commit') or container.find('a', class_='p-commit')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                if '万+' in rating_text or '千+' in rating_text or rating_text.replace('+', '').isdigit():
                    # 这是评论数量，尝试找评分
                    review_count = self._parse_review_count(rating_text)
                else:
                    rating_match = re.search(r'(\d+\.?\d*)%', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1)) / 20  # 转换为5分制
            
            # 店铺信息
            seller = None
            shop_elem = container.find('div', class_='p-shop') or container.find('span', class_='p-shop')
            if shop_elem:
                seller_link = shop_elem.find('a')
                if seller_link:
                    seller = seller_link.get_text(strip=True)
            
            # 图片
            image_url = None
            img_elem = container.find('img')
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-lazy-img') or img_elem.get('data-original')
                if image_url and image_url.startswith('//'):
                    image_url = 'https:' + image_url
            
            return ProductData(
                platform=self.platform_name,
                product_id=str(product_id),
                name=name,
                price=price,
                currency="CNY",
                availability="有库存" if price > 0 else "暂无库存",
                url=url,
                image_url=image_url,
                rating=rating,
                review_count=review_count,
                seller=seller
            )
            
        except Exception as e:
            self.logger.error(f"提取京东商品信息失败: {e}")
            return None
    
    def get_product_details(self, product_url: str) -> Optional[ProductData]:
        """获取京东商品详细信息 - Get detailed JD.com product information."""
        try:
            response = self._make_request(product_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            product_id = self.extract_product_id(product_url)
            if not product_id:
                return None
            
            # 商品名称
            name_elem = soup.find('div', class_='sku-name')
            if not name_elem:
                name_elem = soup.find('div', {'id': 'name'}) or soup.find('h1')
            
            if not name_elem:
                return None
            
            name = name_elem.get_text(strip=True)
            name = re.sub(r'<[^>]+>', '', name)
            
            # 价格 - 京东价格通常通过AJAX加载
            price = 0.0
            
            # 尝试从页面直接获取价格
            price_elem = soup.find('span', class_='price') or soup.find('span', {'id': 'jd-price'})
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self._parse_price(price_text)
            
            # 如果页面没有价格，尝试通过API获取
            if price == 0.0:
                try:
                    price_api_url = f"https://p.3.cn/prices/mgets?skuIds=J_{product_id}"
                    price_response = self._make_request(price_api_url)
                    price_data = json.loads(price_response.text)
                    if price_data and len(price_data) > 0:
                        price = float(price_data[0].get('p', 0))
                except Exception:
                    pass
            
            # 库存状态
            availability = "有库存"
            stock_elem = soup.find('div', class_='stock') or soup.find('span', class_='stock-txt')
            if stock_elem:
                stock_text = stock_elem.get_text(strip=True)
                if '无货' in stock_text or '缺货' in stock_text:
                    availability = "暂无库存"
                elif '现货' in stock_text or '有库存' in stock_text:
                    availability = "现货"
            
            # 评分和评论数
            rating = None
            review_count = None
            
            # 评论数量
            comment_elem = soup.find('a', {'id': 'comment-count'})
            if comment_elem:
                comment_text = comment_elem.get_text(strip=True)
                review_count = self._parse_review_count(comment_text)
            
            # 好评率转换为评分
            rating_elem = soup.find('span', class_='percent-con')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'(\d+)%', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1)) / 20  # 转换为5分制
            
            # 品牌
            brand = None
            brand_elem = soup.find('ul', {'id': 'parameter-brand'}) or soup.find('a', {'clstag': re.compile('brand')})
            if brand_elem:
                brand = brand_elem.get_text(strip=True)
            
            # 店铺
            seller = None
            shop_elem = soup.find('div', class_='seller') or soup.find('div', class_='shopName')
            if shop_elem:
                seller_link = shop_elem.find('a')
                if seller_link:
                    seller = seller_link.get_text(strip=True)
            
            # 图片
            image_url = None
            img_elem = soup.find('img', {'id': 'spec-img'}) or soup.find('div', class_='spec-list').find('img') if soup.find('div', class_='spec-list') else None
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-origin')
                if image_url and image_url.startswith('//'):
                    image_url = 'https:' + image_url
            
            # 分类
            category = None
            breadcrumb = soup.find('div', class_='crumb-wrap')
            if breadcrumb:
                category_links = breadcrumb.find_all('a')
                if category_links:
                    category = category_links[-1].get_text(strip=True)
            
            return ProductData(
                platform=self.platform_name,
                product_id=str(product_id),
                name=name,
                price=price,
                currency="CNY",
                availability=availability,
                url=product_url,
                image_url=image_url,
                rating=rating,
                review_count=review_count,
                seller=seller,
                category=category,
                brand=brand
            )
            
        except Exception as e:
            self.logger.error(f"获取京东商品详情失败: {e}")
            return None
    
    def extract_product_id(self, url: str) -> Optional[str]:
        """从京东URL提取商品ID - Extract product ID from JD.com URL."""
        patterns = [
            r'/(\d+)\.html',
            r'item\.jd\.com/(\d+)',
            r'sku[/=](\d+)',
            r'product[/=](\d+)'
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
        price_clean = re.sub(r'[^\d.,]', '', price_text)
        price_clean = price_clean.replace(',', '')
        
        try:
            return float(price_clean)
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_review_count(self, review_text: str) -> Optional[int]:
        """解析评论数量 - Parse review count."""
        if not review_text:
            return None
        
        try:
            # 处理万+ 千+ 等格式
            if '万+' in review_text:
                num = re.search(r'(\d+\.?\d*)万', review_text)
                if num:
                    return int(float(num.group(1)) * 10000)
            elif '千+' in review_text:
                num = re.search(r'(\d+\.?\d*)千', review_text)
                if num:
                    return int(float(num.group(1)) * 1000)
            else:
                # 直接数字
                num = re.search(r'(\d+)', review_text.replace('+', ''))
                if num:
                    return int(num.group(1))
        except (ValueError, TypeError):
            pass
        
        return None