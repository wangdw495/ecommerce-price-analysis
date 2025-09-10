"""
E-commerce Price Monitor - A comprehensive price monitoring and analysis system.

This package provides tools for:
- Multi-platform price data collection
- Intelligent data analysis and trend detection
- Rich visualizations and reporting
- Automated monitoring and alerts
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .collectors import PriceCollector
from .analyzers import PriceAnalyzer
from .visualizers import PriceVisualizer
from .exporters import DataExporter

__all__ = [
    "PriceCollector",
    "PriceAnalyzer", 
    "PriceVisualizer",
    "DataExporter",
]