"""Comparison analyzer for cross-platform price analysis."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Union, Optional
from collections import defaultdict

from .base_analyzer import BaseAnalyzer, AnalysisResult
from ..collectors.base_collector import ProductData
from ..utils.helpers import calculate_percentage_change, normalize_product_name


class ComparisonAnalyzer(BaseAnalyzer):
    """Analyzer for comparing prices and features across platforms."""
    
    def analyze(
        self, 
        data: Union[List[ProductData], pd.DataFrame], 
        **kwargs
    ) -> AnalysisResult:
        """Perform cross-platform comparison analysis.
        
        Args:
            data: Product data from multiple platforms
            **kwargs: Additional parameters
                - similarity_threshold: Threshold for product matching (default: 0.8)
                - include_shipping: Whether to include shipping costs (default: False)
                
        Returns:
            Comparison analysis results
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data provided for comparison analysis")
        
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = self.prepare_dataframe(data)
        else:
            df = data.copy()
        
        similarity_threshold = kwargs.get('similarity_threshold', 0.8)
        include_shipping = kwargs.get('include_shipping', False)
        
        analysis_results = {}
        
        try:
            # Platform overview comparison
            analysis_results['platform_overview'] = self._compare_platform_overview(df)
            
            # Price comparison across platforms
            analysis_results['price_comparison'] = self._compare_prices(df)
            
            # Feature comparison (ratings, availability, etc.)
            analysis_results['feature_comparison'] = self._compare_features(df)
            
            # Product matching across platforms
            analysis_results['matched_products'] = self._find_matching_products(df, similarity_threshold)
            
            # Market positioning analysis
            analysis_results['market_positioning'] = self._analyze_market_positioning(df)
            
            # Best value analysis
            analysis_results['value_analysis'] = self._analyze_value_proposition(df)
            
            # Platform strengths and weaknesses
            analysis_results['platform_analysis'] = self._analyze_platform_strengths(df)
            
            return AnalysisResult(
                analysis_type='comparison_analysis',
                data=analysis_results,
                metadata={
                    'platforms_compared': df['platform'].nunique() if 'platform' in df.columns else 0,
                    'total_products': len(df),
                    'similarity_threshold': similarity_threshold
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error during comparison analysis: {e}")
            raise AnalyzerError(f"Comparison analysis failed: {e}")
    
    def _compare_platform_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compare basic metrics across platforms."""
        if 'platform' not in df.columns:
            return {}
        
        overview = {}
        
        for platform in df['platform'].unique():
            platform_data = df[df['platform'] == platform]
            
            overview[platform] = {
                'total_products': len(platform_data),
                'avg_price': float(platform_data[platform_data['price'] > 0]['price'].mean()) 
                           if len(platform_data[platform_data['price'] > 0]) > 0 else 0,
                'price_range': {
                    'min': float(platform_data[platform_data['price'] > 0]['price'].min()) 
                          if len(platform_data[platform_data['price'] > 0]) > 0 else 0,
                    'max': float(platform_data[platform_data['price'] > 0]['price'].max()) 
                          if len(platform_data[platform_data['price'] > 0]) > 0 else 0
                },
                'market_share': float(len(platform_data) / len(df) * 100)
            }
            
            # Add rating info if available
            if 'rating' in df.columns:
                platform_ratings = platform_data.dropna(subset=['rating'])
                if len(platform_ratings) > 0:
                    overview[platform]['avg_rating'] = float(platform_ratings['rating'].mean())
                    overview[platform]['rating_count'] = len(platform_ratings)
        
        # Calculate relative metrics
        if len(overview) > 1:
            avg_prices = [data['avg_price'] for data in overview.values() if data['avg_price'] > 0]
            if avg_prices:
                cheapest_platform = min(overview.keys(), key=lambda x: overview[x]['avg_price'] if overview[x]['avg_price'] > 0 else float('inf'))
                most_expensive_platform = max(overview.keys(), key=lambda x: overview[x]['avg_price'])
                
                overview['summary'] = {
                    'cheapest_platform': cheapest_platform,
                    'most_expensive_platform': most_expensive_platform,
                    'price_spread_percent': calculate_percentage_change(
                        overview[cheapest_platform]['avg_price'],
                        overview[most_expensive_platform]['avg_price']
                    ) if overview[cheapest_platform]['avg_price'] > 0 else 0
                }
        
        return overview
    
    def _compare_prices(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detailed price comparison analysis."""
        if 'platform' not in df.columns or 'price' not in df.columns:
            return {}
        
        price_comparison = {}
        
        # Price distribution by platform
        platform_price_stats = {}
        for platform in df['platform'].unique():
            platform_prices = df[df['platform'] == platform]['price']
            valid_prices = platform_prices[platform_prices > 0]
            
            if len(valid_prices) > 0:
                platform_price_stats[platform] = {
                    'mean': float(valid_prices.mean()),
                    'median': float(valid_prices.median()),
                    'std': float(valid_prices.std()),
                    'min': float(valid_prices.min()),
                    'max': float(valid_prices.max()),
                    'q25': float(valid_prices.quantile(0.25)),
                    'q75': float(valid_prices.quantile(0.75))
                }
        
        price_comparison['platform_price_stats'] = platform_price_stats
        
        # Price competitiveness analysis
        if len(platform_price_stats) > 1:
            mean_prices = {platform: stats['mean'] for platform, stats in platform_price_stats.items()}
            
            # Find most competitive platform (lowest average price)
            most_competitive = min(mean_prices.keys(), key=lambda x: mean_prices[x])
            
            # Calculate potential savings
            savings_analysis = {}
            for platform in mean_prices.keys():
                if platform != most_competitive:
                    savings = mean_prices[platform] - mean_prices[most_competitive]
                    savings_percent = calculate_percentage_change(mean_prices[most_competitive], mean_prices[platform])
                    savings_analysis[platform] = {
                        'absolute_savings': float(savings),
                        'percent_savings': float(savings_percent)
                    }
            
            price_comparison['competitiveness'] = {
                'most_competitive_platform': most_competitive,
                'potential_savings': savings_analysis
            }
        
        # Price brackets comparison
        price_comparison['price_brackets'] = self._analyze_price_brackets_by_platform(df)
        
        return price_comparison
    
    def _analyze_price_brackets_by_platform(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price bracket distribution by platform."""
        valid_price_df = df[df['price'] > 0].copy()
        if valid_price_df.empty:
            return {}
        
        # Define price brackets
        min_price = valid_price_df['price'].min()
        max_price = valid_price_df['price'].max()
        
        # Create 5 price brackets
        bracket_size = (max_price - min_price) / 5
        brackets = []
        for i in range(5):
            start_price = min_price + i * bracket_size
            end_price = min_price + (i + 1) * bracket_size
            brackets.append((start_price, end_price, f"${start_price:.0f}-${end_price:.0f}"))
        
        # Count products in each bracket by platform
        bracket_analysis = {}
        for platform in valid_price_df['platform'].unique():
            platform_data = valid_price_df[valid_price_df['platform'] == platform]
            platform_brackets = {}
            
            for start_price, end_price, bracket_name in brackets:
                count = len(platform_data[(platform_data['price'] >= start_price) & 
                                        (platform_data['price'] < end_price)])
                platform_brackets[bracket_name] = {
                    'count': count,
                    'percentage': (count / len(platform_data)) * 100 if len(platform_data) > 0 else 0
                }
            
            bracket_analysis[platform] = platform_brackets
        
        return bracket_analysis
    
    def _compare_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compare non-price features across platforms."""
        feature_comparison = {}
        
        # Rating comparison
        if 'rating' in df.columns:
            rating_stats = {}
            for platform in df['platform'].unique():
                platform_data = df[df['platform'] == platform]
                platform_ratings = platform_data.dropna(subset=['rating'])
                
                if len(platform_ratings) > 0:
                    rating_stats[platform] = {
                        'avg_rating': float(platform_ratings['rating'].mean()),
                        'median_rating': float(platform_ratings['rating'].median()),
                        'rating_count': len(platform_ratings),
                        'high_rated_products': len(platform_ratings[platform_ratings['rating'] >= 4.0]),
                        'low_rated_products': len(platform_ratings[platform_ratings['rating'] <= 2.0])
                    }
            
            feature_comparison['ratings'] = rating_stats
        
        # Availability comparison
        if 'availability' in df.columns:
            availability_stats = {}
            for platform in df['platform'].unique():
                platform_data = df[df['platform'] == platform]
                availability_counts = platform_data['availability'].value_counts()
                
                availability_stats[platform] = {
                    'total_products': len(platform_data),
                    'availability_distribution': availability_counts.to_dict(),
                    'in_stock_percentage': (availability_counts.get('Available', 0) + 
                                          availability_counts.get('In Stock', 0)) / len(platform_data) * 100
                }
            
            feature_comparison['availability'] = availability_stats
        
        # Brand diversity comparison
        if 'brand' in df.columns:
            brand_stats = {}
            for platform in df['platform'].unique():
                platform_data = df[df['platform'] == platform]
                platform_brands = platform_data.dropna(subset=['brand'])
                
                if len(platform_brands) > 0:
                    brand_counts = platform_brands['brand'].value_counts()
                    brand_stats[platform] = {
                        'unique_brands': len(brand_counts),
                        'products_with_brand_info': len(platform_brands),
                        'top_brands': brand_counts.head(5).to_dict()
                    }
            
            feature_comparison['brands'] = brand_stats
        
        return feature_comparison
    
    def _find_matching_products(self, df: pd.DataFrame, similarity_threshold: float) -> Dict[str, Any]:
        """Find similar products across platforms for direct comparison."""
        if len(df) < 2:
            return {'matches': [], 'match_count': 0}
        
        matches = []
        processed_indices = set()
        
        # Compare each product with all others
        for i, product1 in df.iterrows():
            if i in processed_indices:
                continue
            
            similar_products = [product1.to_dict()]
            similar_indices = {i}
            
            for j, product2 in df.iterrows():
                if j <= i or j in processed_indices:
                    continue
                
                # Calculate similarity based on product name
                similarity = self._calculate_product_similarity(
                    product1['name'], product2['name']
                )
                
                if similarity >= similarity_threshold:
                    similar_products.append(product2.to_dict())
                    similar_indices.add(j)
            
            # If we found matches across different platforms
            if len(similar_products) > 1:
                platforms_involved = set(p['platform'] for p in similar_products)
                if len(platforms_involved) > 1:
                    # Analyze the match
                    match_analysis = self._analyze_product_match(similar_products)
                    matches.append(match_analysis)
                    processed_indices.update(similar_indices)
        
        return {
            'matches': matches,
            'match_count': len(matches)
        }
    
    def _calculate_product_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two product names."""
        if not name1 or not name2:
            return 0.0
        
        # Normalize names
        norm1 = normalize_product_name(name1)
        norm2 = normalize_product_name(name2)
        
        # Simple similarity calculation based on common words
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return 0.0
        
        common_words = words1.intersection(words2)
        total_words = words1.union(words2)
        
        return len(common_words) / len(total_words)
    
    def _analyze_product_match(self, similar_products: List[Dict]) -> Dict[str, Any]:
        """Analyze a group of similar products across platforms."""
        # Extract basic info
        product_name = similar_products[0]['name']
        platforms = [p['platform'] for p in similar_products]
        prices = [p['price'] for p in similar_products if p['price'] > 0]
        
        match_analysis = {
            'product_name': product_name,
            'platforms': platforms,
            'platform_count': len(set(platforms)),
            'products': similar_products
        }
        
        # Price analysis
        if prices:
            min_price = min(prices)
            max_price = max(prices)
            
            match_analysis['price_analysis'] = {
                'min_price': float(min_price),
                'max_price': float(max_price),
                'price_difference': float(max_price - min_price),
                'price_difference_percent': calculate_percentage_change(min_price, max_price),
                'cheapest_platform': next(p['platform'] for p in similar_products if p['price'] == min_price),
                'most_expensive_platform': next(p['platform'] for p in similar_products if p['price'] == max_price)
            }
        
        # Rating analysis
        ratings = [p['rating'] for p in similar_products if p.get('rating') is not None]
        if ratings:
            match_analysis['rating_analysis'] = {
                'avg_rating': float(np.mean(ratings)),
                'rating_range': float(max(ratings) - min(ratings)),
                'highest_rated_platform': next(p['platform'] for p in similar_products 
                                             if p.get('rating') == max(ratings))
            }
        
        return match_analysis
    
    def _analyze_market_positioning(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze how each platform positions itself in the market."""
        if 'platform' not in df.columns:
            return {}
        
        positioning = {}
        
        for platform in df['platform'].unique():
            platform_data = df[df['platform'] == platform]
            
            # Price positioning
            platform_prices = platform_data[platform_data['price'] > 0]['price']
            overall_prices = df[df['price'] > 0]['price']
            
            price_position = "unknown"
            if len(platform_prices) > 0 and len(overall_prices) > 0:
                platform_avg = platform_prices.mean()
                market_avg = overall_prices.mean()
                
                if platform_avg < market_avg * 0.9:
                    price_position = "budget"
                elif platform_avg > market_avg * 1.1:
                    price_position = "premium"
                else:
                    price_position = "mainstream"
            
            positioning[platform] = {
                'price_positioning': price_position
            }
            
            # Quality positioning (if ratings available)
            if 'rating' in df.columns:
                platform_ratings = platform_data.dropna(subset=['rating'])['rating']
                overall_ratings = df.dropna(subset=['rating'])['rating']
                
                if len(platform_ratings) > 0 and len(overall_ratings) > 0:
                    platform_rating_avg = platform_ratings.mean()
                    market_rating_avg = overall_ratings.mean()
                    
                    quality_position = "average"
                    if platform_rating_avg > market_rating_avg + 0.2:
                        quality_position = "high_quality"
                    elif platform_rating_avg < market_rating_avg - 0.2:
                        quality_position = "low_quality"
                    
                    positioning[platform]['quality_positioning'] = quality_position
        
        return positioning
    
    def _analyze_value_proposition(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze value proposition of each platform."""
        if 'platform' not in df.columns:
            return {}
        
        value_analysis = {}
        
        for platform in df['platform'].unique():
            platform_data = df[df['platform'] == platform]
            
            # Price value
            valid_prices = platform_data[platform_data['price'] > 0]['price']
            price_value = {
                'competitive_pricing': len(valid_prices) > 0 and valid_prices.mean() < df[df['price'] > 0]['price'].mean(),
                'price_consistency': float(valid_prices.std() / valid_prices.mean()) < 0.3 if len(valid_prices) > 0 else False
            }
            
            # Quality value (if ratings available)
            quality_value = {}
            if 'rating' in df.columns:
                platform_ratings = platform_data.dropna(subset=['rating'])['rating']
                if len(platform_ratings) > 0:
                    quality_value = {
                        'high_quality_products': len(platform_ratings[platform_ratings >= 4.0]) / len(platform_ratings) > 0.6,
                        'consistent_quality': platform_ratings.std() < 0.5
                    }
            
            # Overall value score
            value_score = 0
            if price_value['competitive_pricing']:
                value_score += 30
            if price_value['price_consistency']:
                value_score += 20
            if quality_value.get('high_quality_products'):
                value_score += 30
            if quality_value.get('consistent_quality'):
                value_score += 20
            
            value_analysis[platform] = {
                'price_value': price_value,
                'quality_value': quality_value,
                'overall_value_score': value_score,
                'value_tier': 'high' if value_score >= 70 else 'medium' if value_score >= 40 else 'low'
            }
        
        return value_analysis
    
    def _analyze_platform_strengths(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify strengths and weaknesses of each platform."""
        if 'platform' not in df.columns:
            return {}
        
        platform_analysis = {}
        
        for platform in df['platform'].unique():
            platform_data = df[df['platform'] == platform]
            strengths = []
            weaknesses = []
            
            # Analyze pricing
            platform_prices = platform_data[platform_data['price'] > 0]['price']
            market_prices = df[df['price'] > 0]['price']
            
            if len(platform_prices) > 0 and len(market_prices) > 0:
                if platform_prices.mean() < market_prices.mean():
                    strengths.append("Competitive pricing")
                elif platform_prices.mean() > market_prices.mean() * 1.2:
                    weaknesses.append("Higher prices than market average")
            
            # Analyze product variety
            if len(platform_data) > len(df) / len(df['platform'].unique()) * 1.2:
                strengths.append("Large product selection")
            elif len(platform_data) < len(df) / len(df['platform'].unique()) * 0.8:
                weaknesses.append("Limited product selection")
            
            # Analyze ratings (if available)
            if 'rating' in df.columns:
                platform_ratings = platform_data.dropna(subset=['rating'])['rating']
                market_ratings = df.dropna(subset=['rating'])['rating']
                
                if len(platform_ratings) > 0 and len(market_ratings) > 0:
                    if platform_ratings.mean() > market_ratings.mean():
                        strengths.append("Higher quality products")
                    elif platform_ratings.mean() < market_ratings.mean() - 0.3:
                        weaknesses.append("Lower quality products")
            
            # Analyze availability
            if 'availability' in df.columns:
                in_stock_rate = len(platform_data[platform_data['availability'].str.contains('Available|In Stock', case=False, na=False)]) / len(platform_data)
                market_in_stock_rate = len(df[df['availability'].str.contains('Available|In Stock', case=False, na=False)]) / len(df)
                
                if in_stock_rate > market_in_stock_rate:
                    strengths.append("Good product availability")
                elif in_stock_rate < market_in_stock_rate - 0.1:
                    weaknesses.append("Poor product availability")
            
            platform_analysis[platform] = {
                'strengths': strengths,
                'weaknesses': weaknesses,
                'overall_score': len(strengths) - len(weaknesses)
            }
        
        return platform_analysis