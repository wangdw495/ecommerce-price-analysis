"""数据库管理模块 - Database management module."""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd

from ..config import config_manager
from .exceptions import DatabaseError


class DatabaseManager:
    """数据库管理器 - Database manager for storing price data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """初始化数据库管理器.
        
        Args:
            db_path: 数据库文件路径，如果为None则使用配置文件中的路径
        """
        self.config = config_manager.load_config()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 确定数据库路径
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path(self.config.database.path)
        
        # 创建数据库目录
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # 创建商品表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        platform TEXT NOT NULL,
                        product_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        price REAL,
                        currency TEXT DEFAULT 'USD',
                        availability TEXT,
                        url TEXT,
                        image_url TEXT,
                        rating REAL,
                        review_count INTEGER,
                        seller TEXT,
                        category TEXT,
                        brand TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(platform, product_id)
                    )
                ''')
                
                # 创建价格历史表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS price_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        platform TEXT NOT NULL,
                        product_id TEXT NOT NULL,
                        price REAL NOT NULL,
                        currency TEXT DEFAULT 'USD',
                        availability TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (platform, product_id) REFERENCES products (platform, product_id)
                    )
                ''')
                
                # 创建搜索历史表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS search_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        platform TEXT,
                        results_count INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_platform_id ON products (platform, product_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_platform_id ON price_history (platform, product_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_timestamp ON price_history (timestamp)')
                
                conn.commit()
                self.logger.info(f"数据库初始化完成: {self.db_path}")
                
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    def save_product(self, product_data: Dict[str, Any]) -> bool:
        """保存商品数据.
        
        Args:
            product_data: 商品数据字典
            
        Returns:
            保存成功返回True，否则返回False
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # 插入或更新商品数据
                cursor.execute('''
                    INSERT OR REPLACE INTO products (
                        platform, product_id, name, price, currency, availability,
                        url, image_url, rating, review_count, seller, category,
                        brand, description, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product_data.get('platform'),
                    product_data.get('product_id'),
                    product_data.get('name'),
                    product_data.get('price'),
                    product_data.get('currency', 'USD'),
                    product_data.get('availability'),
                    product_data.get('url'),
                    product_data.get('image_url'),
                    product_data.get('rating'),
                    product_data.get('review_count'),
                    product_data.get('seller'),
                    product_data.get('category'),
                    product_data.get('brand'),
                    product_data.get('description'),
                    datetime.now()
                ))
                
                # 保存价格历史
                if product_data.get('price') is not None:
                    cursor.execute('''
                        INSERT INTO price_history (platform, product_id, price, currency, availability)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        product_data.get('platform'),
                        product_data.get('product_id'),
                        product_data.get('price'),
                        product_data.get('currency', 'USD'),
                        product_data.get('availability')
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"保存商品数据失败: {e}")
            return False
    
    def save_products_batch(self, products_data: List[Dict[str, Any]]) -> int:
        """批量保存商品数据.
        
        Args:
            products_data: 商品数据列表
            
        Returns:
            成功保存的商品数量
        """
        saved_count = 0
        
        for product_data in products_data:
            if self.save_product(product_data):
                saved_count += 1
        
        self.logger.info(f"批量保存完成: {saved_count}/{len(products_data)} 个商品")
        return saved_count
    
    def get_product(self, platform: str, product_id: str) -> Optional[Dict[str, Any]]:
        """获取商品数据.
        
        Args:
            platform: 平台名称
            product_id: 商品ID
            
        Returns:
            商品数据字典，如果不存在返回None
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM products 
                    WHERE platform = ? AND product_id = ?
                ''', (platform, product_id))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            self.logger.error(f"获取商品数据失败: {e}")
            return None
    
    def get_price_history(self, platform: str, product_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """获取商品价格历史.
        
        Args:
            platform: 平台名称
            product_id: 商品ID
            days: 获取最近多少天的数据
            
        Returns:
            价格历史列表
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM price_history 
                    WHERE platform = ? AND product_id = ?
                    AND timestamp >= datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                '''.format(days), (platform, product_id))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"获取价格历史失败: {e}")
            return []
    
    def search_products(self, query: str, platform: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """搜索商品.
        
        Args:
            query: 搜索关键词
            platform: 平台名称（可选）
            limit: 最大返回数量
            
        Returns:
            匹配的商品列表
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                sql = '''
                    SELECT * FROM products 
                    WHERE name LIKE ?
                '''
                params = [f'%{query}%']
                
                if platform:
                    sql += ' AND platform = ?'
                    params.append(platform)
                
                sql += ' ORDER BY updated_at DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(sql, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"搜索商品失败: {e}")
            return []
    
    def save_search_history(self, query: str, platform: Optional[str], results_count: int):
        """保存搜索历史.
        
        Args:
            query: 搜索关键词
            platform: 平台名称
            results_count: 结果数量
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO search_history (query, platform, results_count)
                    VALUES (?, ?, ?)
                ''', (query, platform, results_count))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"保存搜索历史失败: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息.
        
        Returns:
            统计信息字典
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # 商品总数
                cursor.execute('SELECT COUNT(*) FROM products')
                stats['total_products'] = cursor.fetchone()[0]
                
                # 各平台商品数量
                cursor.execute('SELECT platform, COUNT(*) FROM products GROUP BY platform')
                stats['products_by_platform'] = dict(cursor.fetchall())
                
                # 价格历史记录数
                cursor.execute('SELECT COUNT(*) FROM price_history')
                stats['total_price_records'] = cursor.fetchone()[0]
                
                # 搜索历史数
                cursor.execute('SELECT COUNT(*) FROM search_history')
                stats['total_searches'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def export_to_csv(self, output_path: str, table: str = 'products') -> bool:
        """导出数据到CSV文件.
        
        Args:
            output_path: 输出文件路径
            table: 要导出的表名
            
        Returns:
            导出成功返回True
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
                df.to_csv(output_path, index=False, encoding='utf-8')
                
                self.logger.info(f"数据已导出到: {output_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            return False
    
    def cleanup_old_data(self, days: int = 90):
        """清理旧数据.
        
        Args:
            days: 保留最近多少天的数据
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # 清理旧的价格历史记录
                cursor.execute('''
                    DELETE FROM price_history 
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(days))
                
                # 清理旧的搜索历史
                cursor.execute('''
                    DELETE FROM search_history 
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(days))
                
                conn.commit()
                
                self.logger.info(f"清理了超过 {days} 天的旧数据")
                
        except Exception as e:
            self.logger.error(f"清理数据失败: {e}")
    
    def close(self):
        """关闭数据库连接."""
        self.logger.info("数据库管理器已关闭")


# 全局数据库管理器实例
db_manager = DatabaseManager()