"""Base analyzer class for all price analysis modules."""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import pandas as pd

from ..collectors.base_collector import ProductData
from ..config import config_manager
from ..utils.exceptions import AnalyzerError


class AnalysisResult:
    """Container for analysis results."""
    
    def __init__(
        self,
        analysis_type: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize analysis result.
        
        Args:
            analysis_type: Type of analysis performed
            data: Analysis result data
            timestamp: When analysis was performed
            metadata: Additional metadata about the analysis
        """
        self.analysis_type = analysis_type
        self.data = data
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'analysis_type': self.analysis_type,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class BaseAnalyzer(ABC):
    """Abstract base class for all analyzers."""
    
    def __init__(self):
        """Initialize the base analyzer."""
        self.config = config_manager.load_config()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def analyze(
        self, 
        data: Union[List[ProductData], pd.DataFrame], 
        **kwargs
    ) -> AnalysisResult:
        """Perform analysis on the provided data.
        
        Args:
            data: Data to analyze (products or DataFrame)
            **kwargs: Additional analysis parameters
            
        Returns:
            Analysis results
        """
        pass
    
    def prepare_dataframe(self, products: List[ProductData]) -> pd.DataFrame:
        """Convert list of ProductData to pandas DataFrame.
        
        Args:
            products: List of product data
            
        Returns:
            DataFrame with product data
        """
        if not products:
            return pd.DataFrame()
        
        data = []
        for product in products:
            row = {
                'platform': product.platform,
                'product_id': product.product_id,
                'name': product.name,
                'price': product.price,
                'currency': product.currency,
                'availability': product.availability,
                'url': product.url,
                'image_url': product.image_url,
                'rating': product.rating,
                'review_count': product.review_count,
                'seller': product.seller,
                'category': product.category,
                'brand': product.brand,
                'description': product.description,
                'timestamp': product.timestamp
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Convert timestamp to datetime if not already
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    def validate_data(self, data: Union[List[ProductData], pd.DataFrame]) -> bool:
        """Validate input data for analysis.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            if isinstance(data, list):
                if not data:
                    self.logger.warning("Empty product list provided")
                    return False
                
                # Check if all items are ProductData instances
                if not all(isinstance(item, ProductData) for item in data):
                    self.logger.error("Invalid data type in product list")
                    return False
                
            elif isinstance(data, pd.DataFrame):
                if data.empty:
                    self.logger.warning("Empty DataFrame provided")
                    return False
                
                # Check for required columns
                required_columns = ['price', 'timestamp']
                missing_columns = [col for col in required_columns if col not in data.columns]
                if missing_columns:
                    self.logger.error(f"Missing required columns: {missing_columns}")
                    return False
            
            else:
                self.logger.error(f"Unsupported data type: {type(data)}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Data validation error: {e}")
            return False
    
    def filter_by_date_range(
        self, 
        df: pd.DataFrame, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Filter DataFrame by date range.
        
        Args:
            df: DataFrame to filter
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            Filtered DataFrame
        """
        if 'timestamp' not in df.columns:
            self.logger.warning("No timestamp column found for date filtering")
            return df
        
        filtered_df = df.copy()
        
        if start_date is not None:
            filtered_df = filtered_df[filtered_df['timestamp'] >= start_date]
        
        if end_date is not None:
            filtered_df = filtered_df[filtered_df['timestamp'] <= end_date]
        
        return filtered_df
    
    def filter_by_platform(self, df: pd.DataFrame, platforms: List[str]) -> pd.DataFrame:
        """Filter DataFrame by platforms.
        
        Args:
            df: DataFrame to filter
            platforms: List of platform names to include
            
        Returns:
            Filtered DataFrame
        """
        if 'platform' not in df.columns:
            self.logger.warning("No platform column found for platform filtering")
            return df
        
        return df[df['platform'].isin(platforms)]
    
    def filter_by_price_range(
        self, 
        df: pd.DataFrame, 
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> pd.DataFrame:
        """Filter DataFrame by price range.
        
        Args:
            df: DataFrame to filter
            min_price: Minimum price (inclusive)
            max_price: Maximum price (inclusive)
            
        Returns:
            Filtered DataFrame
        """
        if 'price' not in df.columns:
            self.logger.warning("No price column found for price filtering")
            return df
        
        filtered_df = df.copy()
        
        if min_price is not None:
            filtered_df = filtered_df[filtered_df['price'] >= min_price]
        
        if max_price is not None:
            filtered_df = filtered_df[filtered_df['price'] <= max_price]
        
        return filtered_df
    
    def calculate_basic_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics for numerical columns.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with basic statistics
        """
        if df.empty:
            return {}
        
        stats = {}
        numerical_columns = df.select_dtypes(include=['number']).columns
        
        for column in numerical_columns:
            if df[column].notna().any():  # Check if there are non-null values
                stats[column] = {
                    'count': df[column].count(),
                    'mean': df[column].mean(),
                    'median': df[column].median(),
                    'std': df[column].std(),
                    'min': df[column].min(),
                    'max': df[column].max(),
                    'q25': df[column].quantile(0.25),
                    'q75': df[column].quantile(0.75)
                }
        
        return stats