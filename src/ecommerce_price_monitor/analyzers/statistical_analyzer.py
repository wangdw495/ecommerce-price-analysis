"""Statistical analysis for price data."""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Union, Optional
from scipy import stats
from scipy.stats import normaltest, jarque_bera, shapiro
import warnings
warnings.filterwarnings('ignore')

from .base_analyzer import BaseAnalyzer, AnalysisResult
from ..collectors.base_collector import ProductData


class StatisticalAnalyzer(BaseAnalyzer):
    """Analyzer for statistical analysis of price data."""
    
    def analyze(
        self, 
        data: Union[List[ProductData], pd.DataFrame], 
        **kwargs
    ) -> AnalysisResult:
        """Perform statistical analysis on price data.
        
        Args:
            data: Price data to analyze
            **kwargs: Additional parameters
                - confidence_level: Confidence level for intervals (default: 0.95)
                - outlier_method: Method for outlier detection ('iqr', 'zscore', 'modified_zscore')
                
        Returns:
            Statistical analysis results
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data provided for statistical analysis")
        
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = self.prepare_dataframe(data)
        else:
            df = data.copy()
        
        confidence_level = kwargs.get('confidence_level', 0.95)
        outlier_method = kwargs.get('outlier_method', 'iqr')
        
        analysis_results = {}
        
        try:
            # Descriptive statistics
            analysis_results['descriptive_stats'] = self._calculate_descriptive_stats(df)
            
            # Distribution analysis
            analysis_results['distribution_analysis'] = self._analyze_distribution(df)
            
            # Outlier detection
            analysis_results['outlier_analysis'] = self._detect_outliers(df, outlier_method)
            
            # Correlation analysis
            analysis_results['correlation_analysis'] = self._analyze_correlations(df)
            
            # Confidence intervals
            analysis_results['confidence_intervals'] = self._calculate_confidence_intervals(df, confidence_level)
            
            # Hypothesis testing
            analysis_results['hypothesis_tests'] = self._perform_hypothesis_tests(df)
            
            # Platform comparison (if multiple platforms)
            if 'platform' in df.columns and df['platform'].nunique() > 1:
                analysis_results['platform_statistics'] = self._compare_platforms_statistically(df)
            
            return AnalysisResult(
                analysis_type='statistical_analysis',
                data=analysis_results,
                metadata={
                    'sample_size': len(df),
                    'confidence_level': confidence_level,
                    'outlier_method': outlier_method
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error during statistical analysis: {e}")
            raise AnalyzerError(f"Statistical analysis failed: {e}")
    
    def _calculate_descriptive_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive descriptive statistics."""
        if 'price' not in df.columns:
            return {}
        
        prices = df[df['price'] > 0]['price']
        if prices.empty:
            return {}
        
        # Basic statistics
        stats_dict = {
            'count': len(prices),
            'mean': float(prices.mean()),
            'median': float(prices.median()),
            'mode': float(prices.mode().iloc[0]) if not prices.mode().empty else None,
            'std': float(prices.std()),
            'variance': float(prices.var()),
            'min': float(prices.min()),
            'max': float(prices.max()),
            'range': float(prices.max() - prices.min())
        }
        
        # Percentiles
        percentiles = [5, 10, 25, 50, 75, 90, 95]
        stats_dict['percentiles'] = {
            f'p{p}': float(prices.quantile(p/100)) for p in percentiles
        }
        
        # Measures of shape
        stats_dict['skewness'] = float(prices.skew())
        stats_dict['kurtosis'] = float(prices.kurtosis())
        
        # Coefficient of variation
        stats_dict['coefficient_of_variation'] = float(prices.std() / prices.mean()) if prices.mean() > 0 else 0
        
        # Interquartile range
        q1 = prices.quantile(0.25)
        q3 = prices.quantile(0.75)
        stats_dict['iqr'] = float(q3 - q1)
        
        # Quartile deviation
        stats_dict['quartile_deviation'] = float((q3 - q1) / 2)
        
        # Mean absolute deviation
        stats_dict['mean_absolute_deviation'] = float(np.mean(np.abs(prices - prices.mean())))
        
        return stats_dict
    
    def _analyze_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the distribution of price data."""
        if 'price' not in df.columns:
            return {}
        
        prices = df[df['price'] > 0]['price']
        if len(prices) < 3:
            return {'error': 'Insufficient data for distribution analysis'}
        
        distribution_analysis = {}
        
        # Normality tests
        normality_tests = {}
        
        # Shapiro-Wilk test (best for small samples)
        if len(prices) <= 5000:
            try:
                shapiro_stat, shapiro_p = shapiro(prices)
                normality_tests['shapiro_wilk'] = {
                    'statistic': float(shapiro_stat),
                    'p_value': float(shapiro_p),
                    'is_normal': shapiro_p > 0.05
                }
            except Exception:
                pass
        
        # Jarque-Bera test
        try:
            jb_stat, jb_p = jarque_bera(prices)
            normality_tests['jarque_bera'] = {
                'statistic': float(jb_stat),
                'p_value': float(jb_p),
                'is_normal': jb_p > 0.05
            }
        except Exception:
            pass
        
        # D'Agostino normality test
        try:
            dagostino_stat, dagostino_p = normaltest(prices)
            normality_tests['dagostino'] = {
                'statistic': float(dagostino_stat),
                'p_value': float(dagostino_p),
                'is_normal': dagostino_p > 0.05
            }
        except Exception:
            pass
        
        distribution_analysis['normality_tests'] = normality_tests
        
        # Overall normality assessment
        normal_tests_passed = sum(1 for test in normality_tests.values() if test['is_normal'])
        total_tests = len(normality_tests)
        
        if total_tests > 0:
            distribution_analysis['is_likely_normal'] = normal_tests_passed >= total_tests / 2
        
        # Distribution shape analysis
        skewness = prices.skew()
        kurtosis = prices.kurtosis()
        
        shape_analysis = {
            'skewness': float(skewness),
            'skewness_interpretation': self._interpret_skewness(skewness),
            'kurtosis': float(kurtosis),
            'kurtosis_interpretation': self._interpret_kurtosis(kurtosis)
        }
        
        distribution_analysis['shape_analysis'] = shape_analysis
        
        # Best-fit distribution estimation
        distribution_analysis['distribution_fit'] = self._fit_distributions(prices)
        
        return distribution_analysis
    
    def _interpret_skewness(self, skewness: float) -> str:
        """Interpret skewness value."""
        if abs(skewness) < 0.5:
            return "approximately_symmetric"
        elif skewness > 0.5:
            return "right_skewed" if skewness < 1 else "highly_right_skewed"
        else:
            return "left_skewed" if skewness > -1 else "highly_left_skewed"
    
    def _interpret_kurtosis(self, kurtosis: float) -> str:
        """Interpret kurtosis value."""
        if abs(kurtosis) < 0.5:
            return "mesokurtic"  # Normal distribution
        elif kurtosis > 0.5:
            return "leptokurtic"  # Heavy tails, peaked
        else:
            return "platykurtic"  # Light tails, flat
    
    def _fit_distributions(self, prices: pd.Series) -> Dict[str, Any]:
        """Attempt to fit common distributions to the data."""
        if len(prices) < 10:
            return {'error': 'Insufficient data for distribution fitting'}
        
        distributions = ['norm', 'lognorm', 'gamma', 'beta', 'uniform']
        fit_results = {}
        
        for dist_name in distributions:
            try:
                dist = getattr(stats, dist_name)
                params = dist.fit(prices)
                
                # Calculate goodness of fit using Kolmogorov-Smirnov test
                ks_stat, ks_p = stats.kstest(prices, lambda x: dist.cdf(x, *params))
                
                fit_results[dist_name] = {
                    'parameters': [float(p) for p in params],
                    'ks_statistic': float(ks_stat),
                    'ks_p_value': float(ks_p),
                    'good_fit': ks_p > 0.05
                }
            except Exception:
                continue
        
        # Find best fitting distribution
        if fit_results:
            good_fits = {name: result for name, result in fit_results.items() if result['good_fit']}
            if good_fits:
                best_fit = max(good_fits.keys(), key=lambda x: good_fits[x]['ks_p_value'])
                fit_results['best_fit'] = best_fit
        
        return fit_results
    
    def _detect_outliers(self, df: pd.DataFrame, method: str = 'iqr') -> Dict[str, Any]:
        """Detect outliers using various methods."""
        if 'price' not in df.columns:
            return {}
        
        prices = df[df['price'] > 0]['price']
        if prices.empty:
            return {}
        
        outliers_analysis = {}
        
        if method == 'iqr':
            outliers_analysis = self._detect_outliers_iqr(prices, df)
        elif method == 'zscore':
            outliers_analysis = self._detect_outliers_zscore(prices, df)
        elif method == 'modified_zscore':
            outliers_analysis = self._detect_outliers_modified_zscore(prices, df)
        
        return outliers_analysis
    
    def _detect_outliers_iqr(self, prices: pd.Series, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect outliers using Interquartile Range method."""
        q1 = prices.quantile(0.25)
        q3 = prices.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outlier_indices = df[(df['price'] < lower_bound) | (df['price'] > upper_bound)].index
        outlier_prices = df.loc[outlier_indices, 'price'].tolist()
        
        return {
            'method': 'iqr',
            'outlier_count': len(outlier_indices),
            'outlier_percentage': (len(outlier_indices) / len(df)) * 100,
            'outlier_values': [float(p) for p in outlier_prices],
            'bounds': {
                'lower': float(lower_bound),
                'upper': float(upper_bound)
            },
            'outlier_products': df.loc[outlier_indices, ['name', 'platform', 'price']].to_dict('records')
        }
    
    def _detect_outliers_zscore(self, prices: pd.Series, df: pd.DataFrame, threshold: float = 3.0) -> Dict[str, Any]:
        """Detect outliers using Z-score method."""
        z_scores = np.abs(stats.zscore(prices))
        outlier_indices = df.index[z_scores > threshold]
        outlier_prices = df.loc[outlier_indices, 'price'].tolist()
        
        return {
            'method': 'zscore',
            'threshold': threshold,
            'outlier_count': len(outlier_indices),
            'outlier_percentage': (len(outlier_indices) / len(df)) * 100,
            'outlier_values': [float(p) for p in outlier_prices],
            'outlier_products': df.loc[outlier_indices, ['name', 'platform', 'price']].to_dict('records')
        }
    
    def _detect_outliers_modified_zscore(self, prices: pd.Series, df: pd.DataFrame, threshold: float = 3.5) -> Dict[str, Any]:
        """Detect outliers using Modified Z-score method."""
        median = prices.median()
        mad = np.median(np.abs(prices - median))
        
        if mad == 0:
            mad = np.mean(np.abs(prices - median))
        
        if mad == 0:
            return {
                'method': 'modified_zscore',
                'outlier_count': 0,
                'outlier_percentage': 0,
                'outlier_values': [],
                'note': 'No variation in data'
            }
        
        modified_z_scores = 0.6745 * (prices - median) / mad
        outlier_indices = df.index[np.abs(modified_z_scores) > threshold]
        outlier_prices = df.loc[outlier_indices, 'price'].tolist()
        
        return {
            'method': 'modified_zscore',
            'threshold': threshold,
            'outlier_count': len(outlier_indices),
            'outlier_percentage': (len(outlier_indices) / len(df)) * 100,
            'outlier_values': [float(p) for p in outlier_prices],
            'outlier_products': df.loc[outlier_indices, ['name', 'platform', 'price']].to_dict('records')
        }
    
    def _analyze_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlations between numerical variables."""
        numerical_columns = df.select_dtypes(include=[np.number]).columns
        
        if len(numerical_columns) < 2:
            return {'note': 'Insufficient numerical variables for correlation analysis'}
        
        correlation_matrix = df[numerical_columns].corr()
        
        # Find strong correlations (excluding self-correlations)
        strong_correlations = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i + 1, len(correlation_matrix.columns)):
                corr_value = correlation_matrix.iloc[i, j]
                if not np.isnan(corr_value) and abs(corr_value) > 0.5:
                    strong_correlations.append({
                        'variable1': correlation_matrix.columns[i],
                        'variable2': correlation_matrix.columns[j],
                        'correlation': float(corr_value),
                        'strength': 'strong' if abs(corr_value) > 0.7 else 'moderate'
                    })
        
        return {
            'correlation_matrix': correlation_matrix.to_dict(),
            'strong_correlations': strong_correlations
        }
    
    def _calculate_confidence_intervals(self, df: pd.DataFrame, confidence_level: float) -> Dict[str, Any]:
        """Calculate confidence intervals for price statistics."""
        if 'price' not in df.columns:
            return {}
        
        prices = df[df['price'] > 0]['price']
        if len(prices) < 2:
            return {}
        
        alpha = 1 - confidence_level
        
        # Confidence interval for mean
        mean_ci = stats.t.interval(
            confidence_level,
            len(prices) - 1,
            loc=prices.mean(),
            scale=prices.sem()
        )
        
        # Confidence interval for median (using bootstrap method)
        median_ci = self._bootstrap_median_ci(prices, confidence_level)
        
        return {
            'confidence_level': confidence_level,
            'mean_ci': {
                'lower': float(mean_ci[0]),
                'upper': float(mean_ci[1])
            },
            'median_ci': {
                'lower': float(median_ci[0]),
                'upper': float(median_ci[1])
            }
        }
    
    def _bootstrap_median_ci(self, data: pd.Series, confidence_level: float, n_bootstrap: int = 1000) -> tuple:
        """Calculate confidence interval for median using bootstrap method."""
        bootstrap_medians = []
        
        for _ in range(n_bootstrap):
            bootstrap_sample = np.random.choice(data, size=len(data), replace=True)
            bootstrap_medians.append(np.median(bootstrap_sample))
        
        alpha = 1 - confidence_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        return np.percentile(bootstrap_medians, [lower_percentile, upper_percentile])
    
    def _perform_hypothesis_tests(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform various hypothesis tests."""
        if 'price' not in df.columns:
            return {}
        
        prices = df[df['price'] > 0]['price']
        if prices.empty:
            return {}
        
        hypothesis_tests = {}
        
        # Test if mean is significantly different from a reference value
        # (using overall median as reference)
        reference_value = prices.median()
        t_stat, t_p = stats.ttest_1samp(prices, reference_value)
        
        hypothesis_tests['mean_vs_median'] = {
            'test': 'one_sample_t_test',
            'null_hypothesis': f'Mean equals {reference_value:.2f}',
            't_statistic': float(t_stat),
            'p_value': float(t_p),
            'reject_null': t_p < 0.05
        }
        
        return hypothesis_tests
    
    def _compare_platforms_statistically(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform statistical comparison between platforms."""
        if 'platform' not in df.columns:
            return {}
        
        platforms = df['platform'].unique()
        if len(platforms) < 2:
            return {}
        
        comparison_results = {}
        
        # ANOVA test for multiple platforms
        platform_groups = [df[df['platform'] == platform]['price'].dropna() 
                         for platform in platforms]
        
        # Remove empty groups
        platform_groups = [group for group in platform_groups if len(group) > 0]
        
        if len(platform_groups) >= 2:
            try:
                f_stat, f_p = stats.f_oneway(*platform_groups)
                comparison_results['anova'] = {
                    'test': 'one_way_anova',
                    'null_hypothesis': 'All platform means are equal',
                    'f_statistic': float(f_stat),
                    'p_value': float(f_p),
                    'significant_difference': f_p < 0.05
                }
            except Exception:
                pass
        
        # Pairwise t-tests between platforms
        pairwise_tests = {}
        for i, platform1 in enumerate(platforms):
            for j, platform2 in enumerate(platforms):
                if i < j:  # Avoid duplicate comparisons
                    group1 = df[df['platform'] == platform1]['price'].dropna()
                    group2 = df[df['platform'] == platform2]['price'].dropna()
                    
                    if len(group1) > 1 and len(group2) > 1:
                        try:
                            t_stat, t_p = stats.ttest_ind(group1, group2)
                            pairwise_tests[f'{platform1}_vs_{platform2}'] = {
                                't_statistic': float(t_stat),
                                'p_value': float(t_p),
                                'significant_difference': t_p < 0.05,
                                'mean_difference': float(group1.mean() - group2.mean())
                            }
                        except Exception:
                            continue
        
        comparison_results['pairwise_tests'] = pairwise_tests
        
        return comparison_results