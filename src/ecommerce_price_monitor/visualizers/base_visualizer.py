"""Base visualizer class for all chart types."""

import logging
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from ..collectors.base_collector import ProductData
from ..config import config_manager
from ..utils.exceptions import ExporterError


class BaseVisualizer(ABC):
    """Abstract base class for all visualizers."""
    
    def __init__(self):
        """Initialize the base visualizer."""
        self.config = config_manager.load_config()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Set up default styling
        self._setup_styling()
        
        # Color palettes
        self.color_palettes = {
            'primary': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'],
            'pastel': ['#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5', '#c49c94'],
            'dark': ['#17202A', '#E74C3C', '#3498DB', '#2ECC71', '#F39C12', '#9B59B6'],
            'modern': ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4']
        }
    
    def _setup_styling(self):
        """Set up default styling for all plots."""
        # Matplotlib styling
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 11
        
        # Seaborn styling
        sns.set_theme(style="whitegrid", palette="husl")
    
    @abstractmethod
    def create_chart(
        self, 
        data: Union[List[ProductData], pd.DataFrame, Dict[str, Any]], 
        **kwargs
    ) -> Union[plt.Figure, go.Figure]:
        """Create a chart from the provided data.
        
        Args:
            data: Data to visualize
            **kwargs: Chart-specific parameters
            
        Returns:
            Matplotlib or Plotly figure
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
    
    def save_chart(
        self, 
        figure: Union[plt.Figure, go.Figure], 
        filename: str, 
        format: str = 'png',
        output_dir: str = 'data/reports'
    ) -> str:
        """Save chart to file.
        
        Args:
            figure: Figure object to save
            filename: Base filename (without extension)
            format: Output format ('png', 'jpg', 'svg', 'html', 'pdf')
            output_dir: Output directory
            
        Returns:
            Full path to saved file
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Add timestamp to filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        full_filename = f"{filename}_{timestamp}.{format}"
        file_path = os.path.join(output_dir, full_filename)
        
        try:
            if isinstance(figure, plt.Figure):
                # Matplotlib figure
                figure.savefig(
                    file_path, 
                    dpi=300, 
                    bbox_inches='tight',
                    facecolor='white',
                    edgecolor='none'
                )
            elif isinstance(figure, go.Figure):
                # Plotly figure
                if format.lower() == 'html':
                    figure.write_html(file_path)
                else:
                    figure.write_image(file_path, width=1200, height=800)
            else:
                raise ValueError(f"Unsupported figure type: {type(figure)}")
                
            self.logger.info(f"Chart saved to: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Error saving chart: {e}")
            raise ExporterError(f"Failed to save chart: {e}")
    
    def get_color_palette(self, palette_name: str = 'primary', n_colors: Optional[int] = None) -> List[str]:
        """Get color palette for charts.
        
        Args:
            palette_name: Name of the color palette
            n_colors: Number of colors needed
            
        Returns:
            List of color hex codes
        """
        palette = self.color_palettes.get(palette_name, self.color_palettes['primary'])
        
        if n_colors is None:
            return palette
        
        # If we need more colors than available, cycle through the palette
        if n_colors > len(palette):
            return (palette * (n_colors // len(palette) + 1))[:n_colors]
        
        return palette[:n_colors]
    
    def format_currency(self, amount: float, currency: str = 'USD') -> str:
        """Format currency for display.
        
        Args:
            amount: Amount to format
            currency: Currency code
            
        Returns:
            Formatted currency string
        """
        if currency == 'USD':
            return f'${amount:,.2f}'
        elif currency == 'EUR':
            return f'€{amount:,.2f}'
        elif currency == 'GBP':
            return f'£{amount:,.2f}'
        else:
            return f'{amount:,.2f} {currency}'
    
    def add_watermark(self, figure: Union[plt.Figure, go.Figure], text: str = "E-commerce Price Monitor"):
        """Add watermark to the figure.
        
        Args:
            figure: Figure to add watermark to
            text: Watermark text
        """
        if isinstance(figure, plt.Figure):
            # Matplotlib watermark
            figure.text(0.99, 0.01, text, fontsize=8, color='gray', alpha=0.5,
                       ha='right', va='bottom', transform=figure.transFigure)
        elif isinstance(figure, go.Figure):
            # Plotly watermark
            figure.add_annotation(
                text=text,
                xref="paper", yref="paper",
                x=0.99, y=0.01,
                xanchor="right", yanchor="bottom",
                font=dict(size=10, color="gray"),
                opacity=0.5,
                showarrow=False
            )
    
    def create_subplot_layout(
        self, 
        rows: int, 
        cols: int, 
        subplot_titles: Optional[List[str]] = None,
        engine: str = 'plotly'
    ) -> Union[plt.Figure, go.Figure]:
        """Create subplot layout.
        
        Args:
            rows: Number of rows
            cols: Number of columns
            subplot_titles: List of subplot titles
            engine: Plotting engine ('matplotlib' or 'plotly')
            
        Returns:
            Figure with subplot layout
        """
        if engine == 'matplotlib':
            fig, axes = plt.subplots(rows, cols, figsize=(15, 10))
            if subplot_titles:
                for i, title in enumerate(subplot_titles):
                    if rows == 1 and cols == 1:
                        axes.set_title(title)
                    elif rows == 1 or cols == 1:
                        axes[i].set_title(title)
                    else:
                        row, col = divmod(i, cols)
                        axes[row, col].set_title(title)
            return fig
        
        else:  # plotly
            fig = make_subplots(
                rows=rows, 
                cols=cols,
                subplot_titles=subplot_titles,
                vertical_spacing=0.08,
                horizontal_spacing=0.05
            )
            return fig
    
    def validate_data(self, data: Union[List[ProductData], pd.DataFrame, Dict[str, Any]]) -> bool:
        """Validate input data for visualization.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            if isinstance(data, list):
                if not data:
                    self.logger.warning("Empty data list provided")
                    return False
                if not all(isinstance(item, ProductData) for item in data):
                    self.logger.error("Invalid data type in list")
                    return False
                    
            elif isinstance(data, pd.DataFrame):
                if data.empty:
                    self.logger.warning("Empty DataFrame provided")
                    return False
                    
            elif isinstance(data, dict):
                if not data:
                    self.logger.warning("Empty dictionary provided")
                    return False
                    
            else:
                self.logger.error(f"Unsupported data type: {type(data)}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Data validation error: {e}")
            return False
    
    def get_chart_theme(self, theme: str = 'default') -> Dict[str, Any]:
        """Get chart theme configuration.
        
        Args:
            theme: Theme name ('default', 'dark', 'minimal', 'colorful')
            
        Returns:
            Theme configuration dictionary
        """
        themes = {
            'default': {
                'background_color': 'white',
                'grid_color': '#f0f0f0',
                'text_color': '#333333',
                'font_family': 'Arial, sans-serif'
            },
            'dark': {
                'background_color': '#2e2e2e',
                'grid_color': '#444444',
                'text_color': '#ffffff',
                'font_family': 'Arial, sans-serif'
            },
            'minimal': {
                'background_color': 'white',
                'grid_color': '#e0e0e0',
                'text_color': '#666666',
                'font_family': 'Helvetica, sans-serif'
            },
            'colorful': {
                'background_color': '#f8f9fa',
                'grid_color': '#dee2e6',
                'text_color': '#212529',
                'font_family': 'Roboto, sans-serif'
            }
        }
        
        return themes.get(theme, themes['default'])