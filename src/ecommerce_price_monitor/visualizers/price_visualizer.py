"""Price visualization charts - Main visualizer with 6 different chart types."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import List, Dict, Any, Union, Optional

from .base_visualizer import BaseVisualizer
from ..collectors.base_collector import ProductData
from ..utils.helpers import format_currency


class PriceVisualizer(BaseVisualizer):
    """Main price visualizer with 6 different chart types."""
    
    def __init__(self):
        """Initialize the price visualizer."""
        super().__init__()
        
        # Chart type registry
        self.chart_types = {
            'price_distribution': self._create_price_distribution_chart,
            'platform_comparison': self._create_platform_comparison_chart,
            'price_trend': self._create_price_trend_chart,
            'scatter_analysis': self._create_scatter_analysis_chart,
            'heatmap': self._create_correlation_heatmap,
            'box_plot': self._create_box_plot_chart
        }
    
    def create_chart(
        self, 
        data: Union[List[ProductData], pd.DataFrame], 
        chart_type: str = 'price_distribution',
        **kwargs
    ) -> Union[plt.Figure, go.Figure]:
        """Create a specific type of price chart.
        
        Args:
            data: Product data to visualize
            chart_type: Type of chart to create
            **kwargs: Chart-specific parameters
            
        Returns:
            Chart figure
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data provided for visualization")
        
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = self.prepare_dataframe(data)
        else:
            df = data.copy()
        
        if chart_type not in self.chart_types:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        return self.chart_types[chart_type](df, **kwargs)
    
    def create_dashboard(
        self, 
        data: Union[List[ProductData], pd.DataFrame],
        **kwargs
    ) -> go.Figure:
        """Create a comprehensive dashboard with all 6 chart types.
        
        Args:
            data: Product data to visualize
            **kwargs: Dashboard configuration parameters
            
        Returns:
            Plotly dashboard figure
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data provided for dashboard")
        
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = self.prepare_dataframe(data)
        else:
            df = data.copy()
        
        # Create subplot layout (2x3 grid)
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=[
                'Price Distribution',
                'Platform Comparison',
                'Price vs Rating Scatter',
                'Platform Price Ranges',
                'Price Trend Over Time',
                'Price Correlation Heatmap'
            ],
            specs=[
                [{"type": "histogram"}, {"type": "bar"}],
                [{"type": "scatter"}, {"type": "box"}],
                [{"type": "scatter"}, {"type": "heatmap"}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        try:
            # 1. Price Distribution (Histogram)
            self._add_distribution_subplot(fig, df, row=1, col=1)
            
            # 2. Platform Comparison (Bar Chart)
            self._add_platform_comparison_subplot(fig, df, row=1, col=2)
            
            # 3. Scatter Plot (Price vs Rating)
            self._add_scatter_subplot(fig, df, row=2, col=1)
            
            # 4. Box Plot (Price Ranges by Platform)
            self._add_box_plot_subplot(fig, df, row=2, col=2)
            
            # 5. Price Trend (Line Chart)
            self._add_trend_subplot(fig, df, row=3, col=1)
            
            # 6. Correlation Heatmap
            self._add_heatmap_subplot(fig, df, row=3, col=2)
            
        except Exception as e:
            self.logger.error(f"Error creating dashboard: {e}")
            # Create a simple fallback chart
            return self._create_fallback_chart(df)
        
        # Update layout
        fig.update_layout(
            height=1200,
            title={
                'text': 'E-commerce Price Analysis Dashboard',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            showlegend=False,
            font=dict(size=10)
        )
        
        self.add_watermark(fig)
        return fig
    
    def _create_price_distribution_chart(self, df: pd.DataFrame, **kwargs) -> go.Figure:
        """Chart Type 1: Price Distribution Histogram."""
        engine = kwargs.get('engine', 'plotly')
        
        valid_prices = df[df['price'] > 0]['price']
        
        if engine == 'plotly':
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=valid_prices,
                nbinsx=30,
                name='Price Distribution',
                marker_color='#3b82f6',
                opacity=0.7
            ))
            
            fig.update_layout(
                title='Price Distribution Analysis',
                xaxis_title='Price ($)',
                yaxis_title='Number of Products',
                showlegend=False
            )
            
            # Add statistics annotations
            mean_price = valid_prices.mean()
            median_price = valid_prices.median()
            
            fig.add_vline(x=mean_price, line_dash="dash", line_color="red", 
                         annotation_text=f"Mean: {self.format_currency(mean_price)}")
            fig.add_vline(x=median_price, line_dash="dash", line_color="green", 
                         annotation_text=f"Median: {self.format_currency(median_price)}")
            
            return fig
        
        else:  # matplotlib
            fig, ax = plt.subplots(figsize=(12, 8))
            
            ax.hist(valid_prices, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            ax.axvline(valid_prices.mean(), color='red', linestyle='--', label=f'Mean: {self.format_currency(valid_prices.mean())}')
            ax.axvline(valid_prices.median(), color='green', linestyle='--', label=f'Median: {self.format_currency(valid_prices.median())}')
            
            ax.set_title('Price Distribution Analysis', fontsize=16)
            ax.set_xlabel('Price ($)')
            ax.set_ylabel('Number of Products')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            return fig
    
    def _create_platform_comparison_chart(self, df: pd.DataFrame, **kwargs) -> go.Figure:
        """Chart Type 2: Platform Comparison Bar Chart."""
        if 'platform' not in df.columns:
            return self._create_fallback_chart(df, "Platform column not found")
        
        platform_stats = df.groupby('platform').agg({
            'price': ['mean', 'median', 'count']
        }).round(2)
        
        platform_stats.columns = ['avg_price', 'median_price', 'product_count']
        platform_stats = platform_stats.reset_index()
        
        fig = go.Figure()
        
        # Average price bars
        fig.add_trace(go.Bar(
            x=platform_stats['platform'],
            y=platform_stats['avg_price'],
            name='Average Price',
            marker_color='#3b82f6',
            text=[self.format_currency(price) for price in platform_stats['avg_price']],
            textposition='auto'
        ))
        
        # Median price bars
        fig.add_trace(go.Bar(
            x=platform_stats['platform'],
            y=platform_stats['median_price'],
            name='Median Price',
            marker_color='#10b981',
            text=[self.format_currency(price) for price in platform_stats['median_price']],
            textposition='auto'
        ))
        
        fig.update_layout(
            title='Price Comparison Across Platforms',
            xaxis_title='Platform',
            yaxis_title='Price ($)',
            barmode='group'
        )
        
        return fig
    
    def _create_price_trend_chart(self, df: pd.DataFrame, **kwargs) -> go.Figure:
        """Chart Type 3: Price Trend Over Time."""
        if 'timestamp' not in df.columns:
            return self._create_fallback_chart(df, "Timestamp column not found")
        
        # Aggregate by date
        df_trend = df.groupby([df['timestamp'].dt.date, 'platform'])['price'].mean().reset_index()
        df_trend['timestamp'] = pd.to_datetime(df_trend['timestamp'])
        
        fig = go.Figure()
        
        colors = self.get_color_palette('primary', df['platform'].nunique())
        
        for i, platform in enumerate(df['platform'].unique()):
            platform_data = df_trend[df_trend['platform'] == platform]
            
            fig.add_trace(go.Scatter(
                x=platform_data['timestamp'],
                y=platform_data['price'],
                mode='lines+markers',
                name=platform,
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            title='Price Trends Over Time',
            xaxis_title='Date',
            yaxis_title='Average Price ($)',
            hovermode='x unified'
        )
        
        return fig
    
    def _create_scatter_analysis_chart(self, df: pd.DataFrame, **kwargs) -> go.Figure:
        """Chart Type 4: Scatter Plot Analysis (Price vs Rating)."""
        if 'rating' not in df.columns:
            # Use price vs review_count if rating not available
            if 'review_count' not in df.columns:
                return self._create_fallback_chart(df, "Rating and review_count columns not found")
            x_col, x_title = 'review_count', 'Review Count'
        else:
            x_col, x_title = 'rating', 'Rating'
        
        valid_data = df.dropna(subset=[x_col, 'price'])
        valid_data = valid_data[valid_data['price'] > 0]
        
        if 'platform' in df.columns:
            fig = px.scatter(
                valid_data,
                x=x_col,
                y='price',
                color='platform',
                size='price',
                hover_data=['name', 'platform'],
                title=f'Price vs {x_title} Analysis'
            )
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=valid_data[x_col],
                y=valid_data['price'],
                mode='markers',
                marker=dict(size=8, color='#3b82f6', opacity=0.6),
                text=valid_data['name'],
                hovertemplate=f'{x_title}: %{{x}}<br>Price: $%{{y:.2f}}<br>%{{text}}<extra></extra>'
            ))
            
            fig.update_layout(title=f'Price vs {x_title} Analysis')
        
        fig.update_xaxes(title=x_title)
        fig.update_yaxes(title='Price ($)')
        
        return fig
    
    def _create_correlation_heatmap(self, df: pd.DataFrame, **kwargs) -> go.Figure:
        """Chart Type 5: Correlation Heatmap."""
        # Select only numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty or len(numeric_df.columns) < 2:
            return self._create_fallback_chart(df, "Insufficient numeric data for correlation")
        
        # Calculate correlation matrix
        corr_matrix = numeric_df.corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0,
            text=corr_matrix.values.round(2),
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate='%{y} vs %{x}<br>Correlation: %{z:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Price Correlation Heatmap',
            width=600,
            height=500
        )
        
        return fig
    
    def _create_box_plot_chart(self, df: pd.DataFrame, **kwargs) -> go.Figure:
        """Chart Type 6: Box Plot for Price Distribution by Platform."""
        if 'platform' not in df.columns:
            return self._create_fallback_chart(df, "Platform column not found")
        
        fig = go.Figure()
        
        colors = self.get_color_palette('primary', df['platform'].nunique())
        
        for i, platform in enumerate(df['platform'].unique()):
            platform_prices = df[df['platform'] == platform]['price']
            valid_prices = platform_prices[platform_prices > 0]
            
            fig.add_trace(go.Box(
                y=valid_prices,
                name=platform,
                boxpoints='outliers',
                marker_color=colors[i % len(colors)]
            ))
        
        fig.update_layout(
            title='Price Distribution by Platform',
            yaxis_title='Price ($)',
            xaxis_title='Platform'
        )
        
        return fig
    
    # Helper methods for dashboard subplots
    def _add_distribution_subplot(self, fig: go.Figure, df: pd.DataFrame, row: int, col: int):
        """Add price distribution to subplot."""
        valid_prices = df[df['price'] > 0]['price']
        
        fig.add_trace(
            go.Histogram(x=valid_prices, nbinsx=20, marker_color='#3b82f6', opacity=0.7),
            row=row, col=col
        )
        
        fig.update_xaxes(title_text="Price ($)", row=row, col=col)
        fig.update_yaxes(title_text="Count", row=row, col=col)
    
    def _add_platform_comparison_subplot(self, fig: go.Figure, df: pd.DataFrame, row: int, col: int):
        """Add platform comparison to subplot."""
        if 'platform' not in df.columns:
            return
        
        platform_avg = df.groupby('platform')['price'].mean()
        
        fig.add_trace(
            go.Bar(x=platform_avg.index, y=platform_avg.values, marker_color='#10b981'),
            row=row, col=col
        )
        
        fig.update_xaxes(title_text="Platform", row=row, col=col)
        fig.update_yaxes(title_text="Avg Price ($)", row=row, col=col)
    
    def _add_scatter_subplot(self, fig: go.Figure, df: pd.DataFrame, row: int, col: int):
        """Add scatter plot to subplot."""
        if 'rating' in df.columns:
            valid_data = df.dropna(subset=['rating', 'price'])
            valid_data = valid_data[valid_data['price'] > 0]
            
            fig.add_trace(
                go.Scatter(
                    x=valid_data['rating'], 
                    y=valid_data['price'],
                    mode='markers',
                    marker=dict(size=4, opacity=0.6, color='#f59e0b')
                ),
                row=row, col=col
            )
            
            fig.update_xaxes(title_text="Rating", row=row, col=col)
            fig.update_yaxes(title_text="Price ($)", row=row, col=col)
    
    def _add_box_plot_subplot(self, fig: go.Figure, df: pd.DataFrame, row: int, col: int):
        """Add box plot to subplot."""
        if 'platform' not in df.columns:
            return
        
        colors = self.get_color_palette('primary', df['platform'].nunique())
        
        for i, platform in enumerate(df['platform'].unique()):
            platform_prices = df[df['platform'] == platform]['price']
            valid_prices = platform_prices[platform_prices > 0]
            
            fig.add_trace(
                go.Box(
                    y=valid_prices,
                    name=platform,
                    marker_color=colors[i % len(colors)],
                    showlegend=False
                ),
                row=row, col=col
            )
        
        fig.update_yaxes(title_text="Price ($)", row=row, col=col)
    
    def _add_trend_subplot(self, fig: go.Figure, df: pd.DataFrame, row: int, col: int):
        """Add trend line to subplot."""
        if 'timestamp' not in df.columns:
            return
        
        # Simple daily average
        daily_avg = df.groupby(df['timestamp'].dt.date)['price'].mean()
        
        fig.add_trace(
            go.Scatter(
                x=daily_avg.index,
                y=daily_avg.values,
                mode='lines+markers',
                line=dict(color='#8b5cf6', width=2),
                marker=dict(size=3)
            ),
            row=row, col=col
        )
        
        fig.update_xaxes(title_text="Date", row=row, col=col)
        fig.update_yaxes(title_text="Avg Price ($)", row=row, col=col)
    
    def _add_heatmap_subplot(self, fig: go.Figure, df: pd.DataFrame, row: int, col: int):
        """Add correlation heatmap to subplot."""
        numeric_df = df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) >= 2:
            corr_matrix = numeric_df.corr()
            
            fig.add_trace(
                go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.columns,
                    colorscale='RdBu',
                    zmid=0,
                    showscale=False
                ),
                row=row, col=col
            )
    
    def _create_fallback_chart(self, df: pd.DataFrame, message: str = "Data visualization not available") -> go.Figure:
        """Create a simple fallback chart when main chart fails."""
        fig = go.Figure()
        
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor="center", yanchor="middle",
            font=dict(size=16, color="gray"),
            showarrow=False
        )
        
        fig.update_layout(
            title="Chart Not Available",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        
        return fig