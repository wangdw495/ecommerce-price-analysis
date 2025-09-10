"""Main price analyzer that combines multiple analysis types."""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Union, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from .base_analyzer import BaseAnalyzer, AnalysisResult
from .trend_analyzer import TrendAnalyzer
from .comparison_analyzer import ComparisonAnalyzer
from .statistical_analyzer import StatisticalAnalyzer
from ..collectors.base_collector import ProductData
from ..utils.helpers import calculate_percentage_change, format_currency


class PriceAnalyzer(BaseAnalyzer):
    """Main analyzer that provides comprehensive price analysis."""
    
    def __init__(self):
        """Initialize the price analyzer."""
        super().__init__()
        self.trend_analyzer = TrendAnalyzer()
        self.comparison_analyzer = ComparisonAnalyzer()
        self.statistical_analyzer = StatisticalAnalyzer()
    
    def analyze(
        self, 
        data: Union[List[ProductData], pd.DataFrame], 
        **kwargs
    ) -> AnalysisResult:
        """Perform comprehensive price analysis.
        
        Args:
            data: Product data to analyze
            **kwargs: Additional parameters for analysis
            
        Returns:
            Comprehensive analysis results
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data provided for analysis")
        
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = self.prepare_dataframe(data)
        else:
            df = data.copy()
        
        analysis_results = {}
        
        try:
            # Basic overview statistics
            analysis_results['overview'] = self._analyze_overview(df)
            
            # Platform comparison
            analysis_results['platform_comparison'] = self._analyze_platforms(df)
            
            # Price distribution analysis
            analysis_results['price_distribution'] = self._analyze_price_distribution(df)
            
            # Best deals identification
            analysis_results['best_deals'] = self._identify_best_deals(df)
            
            # Market insights
            analysis_results['market_insights'] = self._generate_market_insights(df)
            
            # Recommendations
            analysis_results['recommendations'] = self._generate_recommendations(df)
            
            # If historical data is available, perform trend analysis
            if self._has_temporal_data(df):
                trend_result = self.trend_analyzer.analyze(df)
                analysis_results['trends'] = trend_result.data
            
            # Statistical analysis
            stats_result = self.statistical_analyzer.analyze(df)
            analysis_results['statistics'] = stats_result.data
            
            return AnalysisResult(
                analysis_type='comprehensive_price_analysis',
                data=analysis_results,
                metadata={
                    'total_products': len(df),
                    'platforms': df['platform'].unique().tolist() if 'platform' in df.columns else [],
                    'price_range': {
                        'min': float(df['price'].min()) if 'price' in df.columns else 0,
                        'max': float(df['price'].max()) if 'price' in df.columns else 0
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error during price analysis: {e}")
            raise AnalyzerError(f"Price analysis failed: {e}")
    
    def _analyze_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate overview statistics."""
        overview = {
            'total_products': len(df),
            'platforms_count': df['platform'].nunique() if 'platform' in df.columns else 0,
            'price_stats': {}
        }
        
        if 'price' in df.columns and not df['price'].empty:
            valid_prices = df[df['price'] > 0]['price']
            if not valid_prices.empty:
                overview['price_stats'] = {
                    'average': float(valid_prices.mean()),
                    'median': float(valid_prices.median()),
                    'min': float(valid_prices.min()),
                    'max': float(valid_prices.max()),
                    'std': float(valid_prices.std()) if len(valid_prices) > 1 else 0
                }
        
        # Availability analysis
        if 'availability' in df.columns:
            availability_counts = df['availability'].value_counts().to_dict()
            overview['availability'] = availability_counts
        
        # Rating analysis
        if 'rating' in df.columns:
            valid_ratings = df.dropna(subset=['rating'])
            if not valid_ratings.empty:
                overview['rating_stats'] = {
                    'average': float(valid_ratings['rating'].mean()),
                    'products_with_rating': len(valid_ratings),
                    'rating_distribution': valid_ratings['rating'].value_counts().to_dict()
                }
        
        return overview
    
    def _analyze_platforms(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price differences across platforms."""
        if 'platform' not in df.columns:
            return {}
        
        platform_stats = {}
        
        for platform in df['platform'].unique():
            platform_data = df[df['platform'] == platform]
            valid_prices = platform_data[platform_data['price'] > 0]['price']
            
            if not valid_prices.empty:
                platform_stats[platform] = {
                    'product_count': len(platform_data),
                    'average_price': float(valid_prices.mean()),
                    'median_price': float(valid_prices.median()),
                    'min_price': float(valid_prices.min()),
                    'max_price': float(valid_prices.max()),
                    'price_std': float(valid_prices.std()) if len(valid_prices) > 1 else 0
                }
                
                # Calculate rating stats if available
                if 'rating' in platform_data.columns:
                    valid_ratings = platform_data.dropna(subset=['rating'])
                    if not valid_ratings.empty:
                        platform_stats[platform]['average_rating'] = float(valid_ratings['rating'].mean())
                        platform_stats[platform]['rating_count'] = len(valid_ratings)
        
        # Find best and worst platforms by price
        if platform_stats:
            best_platform = min(platform_stats.keys(), 
                              key=lambda x: platform_stats[x]['average_price'])
            worst_platform = max(platform_stats.keys(), 
                               key=lambda x: platform_stats[x]['average_price'])
            
            platform_stats['summary'] = {
                'cheapest_platform': best_platform,
                'most_expensive_platform': worst_platform,
                'price_difference': platform_stats[worst_platform]['average_price'] - 
                                  platform_stats[best_platform]['average_price']
            }
        
        return platform_stats
    
    def _analyze_price_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price distribution patterns."""
        if 'price' not in df.columns:
            return {}
        
        valid_prices = df[df['price'] > 0]['price']
        if valid_prices.empty:
            return {}
        
        # Create price brackets
        price_brackets = self._create_price_brackets(valid_prices)
        
        # Calculate distribution
        distribution = {}
        for bracket_name, (min_price, max_price) in price_brackets.items():
            count = len(valid_prices[(valid_prices >= min_price) & (valid_prices < max_price)])
            distribution[bracket_name] = {
                'count': count,
                'percentage': (count / len(valid_prices)) * 100,
                'price_range': f"{format_currency(min_price)} - {format_currency(max_price)}"
            }
        
        # Identify price outliers
        q1 = valid_prices.quantile(0.25)
        q3 = valid_prices.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = valid_prices[(valid_prices < lower_bound) | (valid_prices > upper_bound)]
        
        return {
            'distribution': distribution,
            'outliers': {
                'count': len(outliers),
                'percentage': (len(outliers) / len(valid_prices)) * 100,
                'values': outliers.tolist()
            },
            'quartiles': {
                'q1': float(q1),
                'q2': float(valid_prices.median()),
                'q3': float(q3),
                'iqr': float(iqr)
            }
        }
    
    def _create_price_brackets(self, prices: pd.Series) -> Dict[str, tuple]:
        """Create price brackets for distribution analysis."""
        min_price = prices.min()
        max_price = prices.max()
        price_range = max_price - min_price
        
        if price_range < 50:
            bracket_size = 10
        elif price_range < 200:
            bracket_size = 25
        elif price_range < 1000:
            bracket_size = 100
        else:
            bracket_size = 250
        
        brackets = {}
        current_price = min_price
        bracket_num = 1
        
        while current_price < max_price:
            next_price = min(current_price + bracket_size, max_price)
            bracket_name = f"Bracket_{bracket_num}"
            brackets[bracket_name] = (current_price, next_price)
            current_price = next_price
            bracket_num += 1
        
        return brackets
    
    def _identify_best_deals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify the best deals based on various criteria."""
        if df.empty:
            return {}
        
        best_deals = {}
        
        # Best deals by price
        valid_price_df = df[df['price'] > 0].copy()
        if not valid_price_df.empty:
            cheapest_products = valid_price_df.nsmallest(5, 'price')
            best_deals['cheapest'] = []
            
            for _, product in cheapest_products.iterrows():
                best_deals['cheapest'].append({
                    'name': product['name'],
                    'platform': product['platform'],
                    'price': float(product['price']),
                    'formatted_price': format_currency(product['price']),
                    'url': product.get('url', ''),
                    'rating': float(product['rating']) if pd.notna(product.get('rating')) else None
                })
        
        # Best deals by rating (if available)
        if 'rating' in df.columns:
            valid_rating_df = df.dropna(subset=['rating'])
            if not valid_rating_df.empty:
                highest_rated = valid_rating_df.nlargest(5, 'rating')
                best_deals['highest_rated'] = []
                
                for _, product in highest_rated.iterrows():
                    best_deals['highest_rated'].append({
                        'name': product['name'],
                        'platform': product['platform'],
                        'price': float(product['price']),
                        'formatted_price': format_currency(product['price']),
                        'rating': float(product['rating']),
                        'url': product.get('url', '')
                    })
        
        # Best value deals (good rating + reasonable price)
        if 'rating' in df.columns:
            value_df = df[(df['price'] > 0) & df['rating'].notna()].copy()
            if not value_df.empty:
                # Calculate value score (higher rating, lower price = better value)
                max_price = value_df['price'].max()
                value_df['value_score'] = (value_df['rating'] / 5.0) * (1 - value_df['price'] / max_price)
                
                best_value = value_df.nlargest(5, 'value_score')
                best_deals['best_value'] = []
                
                for _, product in best_value.iterrows():
                    best_deals['best_value'].append({
                        'name': product['name'],
                        'platform': product['platform'],
                        'price': float(product['price']),
                        'formatted_price': format_currency(product['price']),
                        'rating': float(product['rating']),
                        'value_score': float(product['value_score']),
                        'url': product.get('url', '')
                    })
        
        return best_deals
    
    def _generate_market_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate market insights from the data."""
        insights = {}
        
        if df.empty:
            return insights
        
        # Market concentration
        if 'platform' in df.columns:
            platform_counts = df['platform'].value_counts()
            total_products = len(df)
            
            insights['market_concentration'] = {
                'dominant_platform': platform_counts.index[0],
                'dominant_platform_share': (platform_counts.iloc[0] / total_products) * 100,
                'market_fragmentation': len(platform_counts)
            }
        
        # Price competitiveness
        if 'price' in df.columns:
            valid_prices = df[df['price'] > 0]['price']
            if not valid_prices.empty:
                price_cv = valid_prices.std() / valid_prices.mean()  # Coefficient of variation
                
                competitiveness_level = "Low"
                if price_cv > 0.3:
                    competitiveness_level = "High"
                elif price_cv > 0.15:
                    competitiveness_level = "Medium"
                
                insights['price_competitiveness'] = {
                    'level': competitiveness_level,
                    'coefficient_of_variation': float(price_cv),
                    'price_spread': float(valid_prices.max() - valid_prices.min())
                }
        
        # Rating patterns
        if 'rating' in df.columns:
            valid_ratings = df.dropna(subset=['rating'])
            if not valid_ratings.empty:
                avg_rating = valid_ratings['rating'].mean()
                rating_std = valid_ratings['rating'].std()
                
                quality_level = "Low"
                if avg_rating >= 4.0:
                    quality_level = "High"
                elif avg_rating >= 3.0:
                    quality_level = "Medium"
                
                insights['quality_patterns'] = {
                    'average_quality': quality_level,
                    'average_rating': float(avg_rating),
                    'rating_consistency': float(1 / (rating_std + 0.1))  # Higher = more consistent
                }
        
        return insights
    
    def _generate_recommendations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate purchase recommendations based on analysis."""
        recommendations = []
        
        if df.empty:
            return recommendations
        
        # Price-based recommendations
        if 'price' in df.columns:
            valid_price_df = df[df['price'] > 0]
            if not valid_price_df.empty:
                cheapest_platform = valid_price_df.groupby('platform')['price'].mean().idxmin()
                avg_savings = valid_price_df.groupby('platform')['price'].mean().max() - \
                            valid_price_df.groupby('platform')['price'].mean().min()
                
                recommendations.append({
                    'type': 'price_optimization',
                    'title': f'Shop on {cheapest_platform} for best prices',
                    'description': f'On average, you can save ${avg_savings:.2f} by choosing {cheapest_platform}',
                    'confidence': 'high'
                })
        
        # Quality-based recommendations
        if 'rating' in df.columns:
            platform_ratings = df.groupby('platform')['rating'].mean()
            if not platform_ratings.empty:
                best_quality_platform = platform_ratings.idxmax()
                
                recommendations.append({
                    'type': 'quality_optimization',
                    'title': f'Consider {best_quality_platform} for highest quality products',
                    'description': f'{best_quality_platform} has the highest average rating of {platform_ratings.max():.1f}',
                    'confidence': 'medium'
                })
        
        # Market timing recommendations
        recommendations.append({
            'type': 'market_timing',
            'title': 'Monitor prices for better deals',
            'description': 'Price monitoring can help you identify the best time to buy',
            'confidence': 'medium'
        })
        
        return recommendations
    
    def _has_temporal_data(self, df: pd.DataFrame) -> bool:
        """Check if data has temporal component for trend analysis."""
        if 'timestamp' not in df.columns:
            return False
        
        # Check if there are multiple time points
        unique_timestamps = df['timestamp'].nunique()
        return unique_timestamps > 1