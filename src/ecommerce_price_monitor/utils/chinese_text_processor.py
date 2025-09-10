"""中文文本处理工具 - Chinese text processing utilities."""

import re
import unicodedata
from typing import List, Dict, Optional, Set
import jieba
from zhconv import convert


class ChineseTextProcessor:
    """中文文本处理器 - Chinese text processor."""
    
    def __init__(self):
        """初始化中文文本处理器。"""
        # 常用停用词
        self.stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', 
            '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '现在', '可以',
            '但是', '因为', '所以', '如果', '虽然', '然后', '还是', '或者', '已经', '应该', '可能', '只是',
            '正品', '包邮', '特价', '促销', '折扣', '优惠', '限时', '秒杀', '抢购', '新品', '热销'
        }
        
        # 商品相关停用词
        self.product_stopwords = {
            '商品', '产品', '物品', '货物', '东西', '用品', '器具', '设备', '装置', '工具', '配件',
            '正品', '全新', '原装', '品牌', '专柜', '官方', '授权', '直营', '旗舰店', '专营店',
            '包邮', '现货', '库存', '有货', '缺货', '预售', '定制'
        }
        
        # 品牌名称模式（英文品牌通常保留）
        self.brand_pattern = re.compile(r'[A-Za-z]+')
        
        # 规格参数模式
        self.spec_pattern = re.compile(r'\d+[a-zA-Z]*(?:\.\d+)?[a-zA-Z]*|[0-9]+[xX×]\d+')
    
    def normalize_product_name(self, name: str) -> str:
        """标准化商品名称 - Normalize product name for comparison.
        
        Args:
            name: 原始商品名称
            
        Returns:
            标准化后的商品名称
        """
        if not name:
            return ""
        
        # 1. 繁体转简体
        name = convert(name, 'zh-cn')
        
        # 2. 清理HTML标签和特殊字符
        name = re.sub(r'<[^>]+>', '', name)
        name = re.sub(r'&[a-zA-Z]+;', '', name)
        
        # 3. 移除多余的空格和标点
        name = re.sub(r'[【】\[\]()（）<>《》""''『』「」]', ' ', name)
        name = re.sub(r'[,，.。;；:：!！?？~～@#$%^&*+=|\\\/]', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        name = name.strip()
        
        # 4. 分词处理
        words = list(jieba.cut(name))
        
        # 5. 过滤停用词和无意义词汇
        filtered_words = []
        for word in words:
            word = word.strip()
            if (len(word) > 1 and 
                word not in self.stopwords and 
                word not in self.product_stopwords and
                not self._is_meaningless_word(word)):
                filtered_words.append(word)
        
        # 6. 重新组合
        return ' '.join(filtered_words)
    
    def extract_key_features(self, name: str) -> Dict[str, List[str]]:
        """提取商品名称中的关键特征 - Extract key features from product name.
        
        Args:
            name: 商品名称
            
        Returns:
            包含不同类型特征的字典
        """
        features = {
            'brands': [],      # 品牌
            'models': [],      # 型号
            'specs': [],       # 规格参数
            'colors': [],      # 颜色
            'materials': [],   # 材质
            'categories': [],  # 分类
            'keywords': []     # 其他关键词
        }
        
        if not name:
            return features
        
        # 分词
        words = list(jieba.cut(name))
        
        # 颜色词库
        colors = {
            '黑', '白', '红', '蓝', '绿', '黄', '紫', '粉', '灰', '橙', '棕', '银', '金',
            '黑色', '白色', '红色', '蓝色', '绿色', '黄色', '紫色', '粉色', '灰色', 
            '橙色', '棕色', '银色', '金色', '透明', '彩色'
        }
        
        # 材质词库
        materials = {
            '塑料', '金属', '不锈钢', '铝合金', '碳纤维', '玻璃', '陶瓷', '硅胶', '橡胶',
            '皮革', '真皮', '人造革', '布料', '棉', '丝绸', '尼龙', '聚酯', '木质', '竹制'
        }
        
        for word in words:
            word = word.strip()
            if len(word) < 2:
                continue
                
            # 品牌识别（英文）
            if self.brand_pattern.match(word) and len(word) > 2:
                features['brands'].append(word)
            
            # 规格参数
            elif self.spec_pattern.search(word):
                features['specs'].append(word)
            
            # 颜色
            elif word in colors or any(color in word for color in colors):
                features['colors'].append(word)
            
            # 材质
            elif word in materials or any(material in word for material in materials):
                features['materials'].append(word)
            
            # 其他关键词
            elif (word not in self.stopwords and 
                  word not in self.product_stopwords):
                features['keywords'].append(word)
        
        return features
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """计算两个商品名称的相似度 - Calculate similarity between two product names.
        
        Args:
            name1: 商品名称1
            name2: 商品名称2
            
        Returns:
            相似度分数 (0-1之间)
        """
        if not name1 or not name2:
            return 0.0
        
        # 标准化名称
        norm1 = self.normalize_product_name(name1)
        norm2 = self.normalize_product_name(name2)
        
        # 提取特征
        features1 = self.extract_key_features(name1)
        features2 = self.extract_key_features(name2)
        
        # 计算各种相似度
        similarities = []
        
        # 1. 文本相似度
        text_sim = self._jaccard_similarity(norm1.split(), norm2.split())
        similarities.append(text_sim * 0.4)  # 权重40%
        
        # 2. 品牌相似度
        brand_sim = self._jaccard_similarity(features1['brands'], features2['brands'])
        similarities.append(brand_sim * 0.2)  # 权重20%
        
        # 3. 关键词相似度
        keyword_sim = self._jaccard_similarity(features1['keywords'], features2['keywords'])
        similarities.append(keyword_sim * 0.3)  # 权重30%
        
        # 4. 规格相似度
        spec_sim = self._jaccard_similarity(features1['specs'], features2['specs'])
        similarities.append(spec_sim * 0.1)  # 权重10%
        
        return sum(similarities)
    
    def _jaccard_similarity(self, set1: List[str], set2: List[str]) -> float:
        """计算Jaccard相似度 - Calculate Jaccard similarity."""
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        s1 = set(set1)
        s2 = set(set2)
        
        intersection = len(s1.intersection(s2))
        union = len(s1.union(s2))
        
        return intersection / union if union > 0 else 0.0
    
    def _is_meaningless_word(self, word: str) -> bool:
        """判断是否为无意义词汇 - Check if word is meaningless."""
        if len(word) < 2:
            return True
        
        # 检查是否为纯数字或特殊字符
        if word.isdigit() or re.match(r'^[^\u4e00-\u9fa5a-zA-Z]+$', word):
            return True
        
        # 检查是否为重复字符
        if len(set(word)) == 1:
            return True
        
        return False
    
    def segment_text(self, text: str) -> List[str]:
        """中文分词 - Chinese word segmentation.
        
        Args:
            text: 待分词的文本
            
        Returns:
            分词结果列表
        """
        if not text:
            return []
        
        # 使用jieba分词
        words = list(jieba.cut(text))
        
        # 过滤空白和停用词
        return [word.strip() for word in words 
                if word.strip() and word.strip() not in self.stopwords]
    
    def extract_price_info(self, text: str) -> Dict[str, Optional[float]]:
        """从文本中提取价格信息 - Extract price information from text.
        
        Args:
            text: 包含价格信息的文本
            
        Returns:
            价格信息字典
        """
        price_info = {
            'current_price': None,
            'original_price': None,
            'discount_price': None
        }
        
        # 价格模式匹配
        price_patterns = [
            r'￥(\d+(?:\.\d{2})?)',
            r'¥(\d+(?:\.\d{2})?)',  
            r'(\d+(?:\.\d{2})?)\s*元',
            r'价格[：:]?\s*(\d+(?:\.\d{2})?)',
            r'售价[：:]?\s*(\d+(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    price = float(match.replace(',', ''))
                    prices.append(price)
                except ValueError:
                    continue
        
        if prices:
            prices.sort()
            price_info['current_price'] = prices[0]  # 最低价格作为当前价格
            if len(prices) > 1:
                price_info['original_price'] = prices[-1]  # 最高价格作为原价
        
        return price_info


# 全局实例
chinese_processor = ChineseTextProcessor()