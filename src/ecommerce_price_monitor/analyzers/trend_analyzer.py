"""Trend analysis for price data over time."""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Union, Optional
from datetime import datetime, timedelta
from scipy import stats
from scipy.signal import find_peaks

from .base_analyzer import BaseAnalyzer, AnalysisResult
from ..collectors.base_collector import ProductData
from ..utils.helpers import calculate_percentage_change


class TrendAnalyzer(BaseAnalyzer):
    """Analyzer for identifying price trends and patterns over time."""
    
    def analyze(
        self, 
        data: Union[List[ProductData], pd.DataFrame], 
        **kwargs
    ) -> AnalysisResult:
        """Analyze price trends over time.
        
        Args:
            data: Time-series price data
            **kwargs: Additional parameters
                - window_size: Moving average window size (default: 7)
                - trend_threshold: Minimum slope for trend detection (default: 0.05)
                
        Returns:
            Trend analysis results
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data provided for trend analysis")
        
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = self.prepare_dataframe(data)
        else:
            df = data.copy()
        
        if 'timestamp' not in df.columns or 'price' not in df.columns:
            raise ValueError("Timestamp and price columns are required for trend analysis")
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        window_size = kwargs.get('window_size', 7)
        trend_threshold = kwargs.get('trend_threshold', 0.05)
        
        analysis_results = {}
        
        try:
            # Overall trend analysis
            analysis_results['overall_trend'] = self._analyze_overall_trend(df, trend_threshold)
            
            # Moving averages
            analysis_results['moving_averages'] = self._calculate_moving_averages(df, window_size)
            
            # Volatility analysis
            analysis_results['volatility'] = self._analyze_volatility(df, window_size)
            
            # Seasonal patterns
            analysis_results['seasonality'] = self._analyze_seasonality(df)
            
            # Peak and trough detection
            analysis_results['peaks_troughs'] = self._detect_peaks_troughs(df)
            
            # Future trend prediction (simple)
            analysis_results['trend_prediction'] = self._predict_trend(df)
            
            # Platform-specific trends
            if 'platform' in df.columns:
                analysis_results['platform_trends'] = self._analyze_platform_trends(df, trend_threshold)
            
            return AnalysisResult(
                analysis_type='trend_analysis',
                data=analysis_results,
                metadata={
                    'data_points': len(df),
                    'time_span_days': (df['timestamp'].max() - df['timestamp'].min()).days,
                    'window_size': window_size
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error during trend analysis: {e}")
            raise AnalyzerError(f"Trend analysis failed: {e}")
    
    def _analyze_overall_trend(self, df: pd.DataFrame, threshold: float) -> Dict[str, Any]:
        """Analyze overall price trend."""
        prices = df['price'].values
        timestamps = pd.to_numeric(df['timestamp']) / 1e9  # Convert to seconds
        
        # Linear regression to find trend
        slope, intercept, r_value, p_value, std_err = stats.linregress(timestamps, prices)
        
        # Determine trend direction
        trend_direction = "stable"
        if abs(slope) > threshold:
            trend_direction = "increasing" if slope > 0 else "decreasing"
        
        # Calculate trend strength
        trend_strength = min(abs(r_value), 1.0)  # Correlation coefficient as strength
        
        # Calculate percentage change over period
        if len(prices) > 1:
            total_change = calculate_percentage_change(prices[0], prices[-1])
        else:
            total_change = 0.0
        
        return {
            'direction': trend_direction,
            'slope': float(slope),
            'strength': float(trend_strength),
            'r_squared': float(r_value ** 2),
            'p_value': float(p_value),
            'total_change_percent': float(total_change),
            'confidence': 'high' if p_value < 0.05 else 'medium' if p_value < 0.1 else 'low'
        }
    
    def _calculate_moving_averages(self, df: pd.DataFrame, window: int) -> Dict[str, Any]:
        """Calculate various moving averages."""
        prices = df['price']
        
        # Simple moving average
        sma = prices.rolling(window=window, min_periods=1).mean()
        
        # Exponential moving average
        ema = prices.ewm(span=window).mean()
        
        # Current position relative to moving averages
        current_price = prices.iloc[-1] if len(prices) > 0 else 0
        current_sma = sma.iloc[-1] if len(sma) > 0 else 0
        current_ema = ema.iloc[-1] if len(ema) > 0 else 0
        
        return {
            'simple_moving_average': {
                'current': float(current_sma),
                'values': sma.tolist(),
                'price_vs_sma': calculate_percentage_change(current_sma, current_price)
            },
            'exponential_moving_average': {
                'current': float(current_ema),
                'values': ema.tolist(),
                'price_vs_ema': calculate_percentage_change(current_ema, current_price)
            }
        }
    
    def _analyze_volatility(self, df: pd.DataFrame, window: int) -> Dict[str, Any]:
        """Analyze price volatility."""
        prices = df['price']
        
        # Calculate returns (percentage change)
        returns = prices.pct_change().dropna()
        
        # Rolling volatility (standard deviation of returns)
        rolling_volatility = returns.rolling(window=window, min_periods=1).std()
        
        # Average volatility
        avg_volatility = returns.std() if len(returns) > 0 else 0
        
        # Volatility classification
        volatility_level = "low"
        if avg_volatility > 0.1:
            volatility_level = "high"
        elif avg_volatility > 0.05:
            volatility_level = "medium"
        
        # VaR (Value at Risk) - 95% confidence
        var_95 = returns.quantile(0.05) if len(returns) > 0 else 0
        
        return {
            'average_volatility': float(avg_volatility),
            'volatility_level': volatility_level,
            'rolling_volatility': rolling_volatility.tolist(),
            'value_at_risk_95': float(var_95),
            'max_drawdown': self._calculate_max_drawdown(prices)
        }
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown."""
        if len(prices) < 2:
            return 0.0
        
        # Calculate running maximum
        running_max = prices.expanding().max()
        
        # Calculate drawdown
        drawdown = (prices - running_max) / running_max
        
        # Return maximum drawdown (most negative value)
        return float(drawdown.min())
    
    def _analyze_seasonality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze seasonal patterns in price data."""
        if len(df) < 7:  # Need at least a week of data
            return {'detected': False, 'reason': 'Insufficient data'}
        
        # Extract time components
        df_copy = df.copy()
        df_copy['hour'] = df_copy['timestamp'].dt.hour
        df_copy['day_of_week'] = df_copy['timestamp'].dt.dayofweek
        df_copy['day_of_month'] = df_copy['timestamp'].dt.day
        df_copy['month'] = df_copy['timestamp'].dt.month
        
        seasonality = {}
        
        # Hourly patterns (if we have intraday data)
        if df_copy['hour'].nunique() > 1:
            hourly_avg = df_copy.groupby('hour')['price'].mean()
            seasonality['hourly'] = {
                'average_by_hour': hourly_avg.to_dict(),
                'best_hour': int(hourly_avg.idxmin()),
                'worst_hour': int(hourly_avg.idxmax())
            }
        
        # Day of week patterns
        if df_copy['day_of_week'].nunique() > 1:
            dow_avg = df_copy.groupby('day_of_week')['price'].mean()
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            seasonality['day_of_week'] = {
                'average_by_day': {day_names[i]: float(dow_avg.get(i, 0)) for i in range(7)},
                'best_day': day_names[int(dow_avg.idxmin())],
                'worst_day': day_names[int(dow_avg.idxmax())]
            }
        
        # Monthly patterns (if we have enough data)
        if df_copy['month'].nunique() > 1:
            monthly_avg = df_copy.groupby('month')['price'].mean()
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            seasonality['monthly'] = {
                'average_by_month': {month_names[i-1]: float(monthly_avg.get(i, 0)) for i in range(1, 13) if i in monthly_avg.index},
                'best_month': month_names[int(monthly_avg.idxmin()) - 1],
                'worst_month': month_names[int(monthly_avg.idxmax()) - 1]
            }
        
        seasonality['detected'] = len(seasonality) > 0
        return seasonality
    
    def _detect_peaks_troughs(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect significant peaks and troughs in price data."""
        prices = df['price'].values
        timestamps = df['timestamp'].values
        
        if len(prices) < 5:  # Need minimum data points
            return {'peaks': [], 'troughs': []}
        
        # Detect peaks (local maxima)
        peaks, _ = find_peaks(prices, height=np.percentile(prices, 75))
        
        # Detect troughs (local minima) by inverting the data
        troughs, _ = find_peaks(-prices, height=-np.percentile(prices, 25))
        
        peak_data = []
        for peak_idx in peaks:
            peak_data.append({
                'timestamp': timestamps[peak_idx].isoformat(),
                'price': float(prices[peak_idx]),
                'index': int(peak_idx)
            })
        
        trough_data = []
        for trough_idx in troughs:
            trough_data.append({
                'timestamp': timestamps[trough_idx].isoformat(),
                'price': float(prices[trough_idx]),
                'index': int(trough_idx)
            })
        
        return {
            'peaks': peak_data,
            'troughs': trough_data,
            'peak_count': len(peak_data),
            'trough_count': len(trough_data)
        }
    
    def _predict_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Simple trend prediction based on recent data."""
        if len(df) < 3:
            return {'prediction': 'insufficient_data'}
        
        # Use last few data points for prediction
        recent_data = df.tail(min(10, len(df)))
        prices = recent_data['price'].values
        timestamps = pd.to_numeric(recent_data['timestamp']) / 1e9
        
        # Linear regression on recent data
        slope, intercept, r_value, p_value, std_err = stats.linregress(timestamps, prices)
        
        # Predict next few periods
        last_timestamp = timestamps[-1]
        prediction_periods = 3  # Predict 3 periods ahead
        predictions = []
        
        for i in range(1, prediction_periods + 1):
            future_timestamp = last_timestamp + (i * 86400)  # Assume daily data
            predicted_price = slope * future_timestamp + intercept
            predictions.append({
                'period': i,
                'predicted_price': float(max(0, predicted_price)),  # Ensure non-negative
                'confidence': float(max(0, min(1, abs(r_value))))
            })
        
        trend_direction = "stable"
        if abs(slope) > 0.01:  # Small threshold for predictions
            trend_direction = "increasing" if slope > 0 else "decreasing"
        
        return {
            'trend_direction': trend_direction,
            'predictions': predictions,
            'model_confidence': float(abs(r_value)),
            'note': 'Predictions based on linear trend extrapolation'
        }
    
    def _analyze_platform_trends(self, df: pd.DataFrame, threshold: float) -> Dict[str, Any]:
        """Analyze trends for each platform separately."""
        platform_trends = {}
        
        for platform in df['platform'].unique():
            platform_data = df[df['platform'] == platform].sort_values('timestamp')
            
            if len(platform_data) < 2:
                continue
            
            prices = platform_data['price'].values
            timestamps = pd.to_numeric(platform_data['timestamp']) / 1e9
            
            # Linear regression for this platform
            slope, intercept, r_value, p_value, std_err = stats.linregress(timestamps, prices)
            
            trend_direction = "stable"
            if abs(slope) > threshold:
                trend_direction = "increasing" if slope > 0 else "decreasing"
            
            platform_trends[platform] = {
                'direction': trend_direction,
                'slope': float(slope),
                'strength': float(abs(r_value)),
                'data_points': len(platform_data),
                'price_change_percent': calculate_percentage_change(prices[0], prices[-1]) if len(prices) > 1 else 0
            }
        
        return platform_trends