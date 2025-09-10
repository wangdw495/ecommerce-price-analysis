"""Main data exporter with multiple format support."""

import os
import json
import logging
from typing import List, Dict, Any, Union, Optional
from datetime import datetime
import pandas as pd

from ..utils.exceptions import ExporterError


class DataExporter:
    """Main exporter that supports multiple output formats."""
    
    def __init__(self):
        """Initialize the data exporter."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def export_data(
        self,
        data: Union[List[Dict], pd.DataFrame, Any],
        format: str,
        filename: Optional[str] = None,
        output_dir: str = 'data/reports',
        **kwargs
    ) -> str:
        """Export data in the specified format.
        
        Args:
            data: Data to export
            format: Output format ('csv', 'excel', 'json', 'markdown', 'html')
            filename: Output filename (without extension)
            output_dir: Output directory
            **kwargs: Format-specific options
            
        Returns:
            Path to the exported file
        """
        supported_formats = ['csv', 'excel', 'json', 'markdown', 'html']
        if format.lower() not in supported_formats:
            raise ValueError(f"Unsupported export format: {format}. Supported: {supported_formats}")
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"price_analysis_{timestamp}"
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            if format.lower() == 'csv':
                return self._export_csv(data, filename, output_dir, **kwargs)
            elif format.lower() == 'excel':
                return self._export_excel(data, filename, output_dir, **kwargs)
            elif format.lower() == 'json':
                return self._export_json(data, filename, output_dir, **kwargs)
            elif format.lower() == 'markdown':
                return self._export_markdown(data, filename, output_dir, **kwargs)
            elif format.lower() == 'html':
                return self._export_html(data, filename, output_dir, **kwargs)
                
        except Exception as e:
            self.logger.error(f"Export failed for format {format}: {e}")
            raise ExporterError(f"Failed to export data as {format}: {e}")
    
    def _export_csv(self, data, filename, output_dir, **kwargs):
        """Export data to CSV format."""
        filepath = os.path.join(output_dir, f"{filename}.csv")
        
        if isinstance(data, pd.DataFrame):
            data.to_csv(filepath, index=False, encoding='utf-8')
        elif isinstance(data, list):
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False, encoding='utf-8')
        else:
            # Handle analysis results or other objects
            if hasattr(data, 'to_dict'):
                df = pd.DataFrame([data.to_dict()])
            elif hasattr(data, 'data'):
                df = pd.DataFrame([data.data])
            else:
                df = pd.DataFrame([str(data)])
            df.to_csv(filepath, index=False, encoding='utf-8')
        
        return filepath
    
    def _export_excel(self, data, filename, output_dir, **kwargs):
        """Export data to Excel format."""
        filepath = os.path.join(output_dir, f"{filename}.xlsx")
        
        if isinstance(data, pd.DataFrame):
            data.to_excel(filepath, index=False, engine='openpyxl')
        elif isinstance(data, list):
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False, engine='openpyxl')
        else:
            # Handle analysis results or other objects
            if hasattr(data, 'to_dict'):
                df = pd.DataFrame([data.to_dict()])
            elif hasattr(data, 'data'):
                df = pd.DataFrame([data.data])
            else:
                df = pd.DataFrame([str(data)])
            df.to_excel(filepath, index=False, engine='openpyxl')
        
        return filepath
    
    def _export_json(self, data, filename, output_dir, **kwargs):
        """Export data to JSON format."""
        filepath = os.path.join(output_dir, f"{filename}.json")
        
        if isinstance(data, pd.DataFrame):
            json_data = data.to_dict(orient='records')
        elif isinstance(data, list):
            json_data = data
        else:
            # Handle analysis results or other objects
            if hasattr(data, 'to_dict'):
                json_data = data.to_dict()
            elif hasattr(data, 'data'):
                json_data = data.data
            else:
                json_data = str(data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
        
        return filepath
    
    def _export_markdown(self, data, filename, output_dir, **kwargs):
        """Export data to Markdown format."""
        filepath = os.path.join(output_dir, f"{filename}.md")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Price Analysis Report\\n\\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
            
            if isinstance(data, pd.DataFrame):
                f.write("## Data Summary\\n\\n")
                f.write(data.to_markdown(index=False))
                f.write("\\n\\n")
            elif isinstance(data, list) and data:
                f.write("## Products\\n\\n")
                df = pd.DataFrame(data)
                f.write(df.to_markdown(index=False))
                f.write("\\n\\n")
            else:
                f.write("## Analysis Results\\n\\n")
                if hasattr(data, 'data') and isinstance(data.data, dict):
                    for key, value in data.data.items():
                        f.write(f"### {key.replace('_', ' ').title()}\\n\\n")
                        f.write(f"{value}\\n\\n")
                else:
                    f.write(f"{data}\\n\\n")
        
        return filepath
    
    def _export_html(self, data, filename, output_dir, **kwargs):
        """Export data to HTML format."""
        filepath = os.path.join(output_dir, f"{filename}.html")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Price Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>🛒 Price Analysis Report</h1>
    <div class="summary">
        <p><strong>Generated on:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
""")
            
            if isinstance(data, pd.DataFrame):
                f.write("<h2>📊 Data Summary</h2>")
                f.write(data.to_html(index=False, escape=False))
            elif isinstance(data, list) and data:
                f.write("<h2>📦 Products</h2>")
                df = pd.DataFrame(data)
                f.write(df.to_html(index=False, escape=False))
            else:
                f.write("<h2>📈 Analysis Results</h2>")
                if hasattr(data, 'data') and isinstance(data.data, dict):
                    for key, value in data.data.items():
                        f.write(f"<h3>{key.replace('_', ' ').title()}</h3>")
                        f.write(f"<p>{value}</p>")
                else:
                    f.write(f"<p>{data}</p>")
            
            f.write("</body></html>")
        
        return filepath
    
    def export_multiple_formats(
        self,
        data: Union[List[Dict], pd.DataFrame, Any],
        formats: List[str],
        base_filename: Optional[str] = None,
        output_dir: str = 'data/reports',
        **kwargs
    ) -> Dict[str, str]:
        """Export data in multiple formats simultaneously.
        
        Args:
            data: Data to export
            formats: List of output formats
            base_filename: Base filename (without extension)
            output_dir: Output directory
            **kwargs: Format-specific options
            
        Returns:
            Dictionary mapping format names to file paths
        """
        if base_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_filename = f"price_analysis_{timestamp}"
        
        results = {}
        
        for format_name in formats:
            try:
                file_path = self.export_data(
                    data, format_name, base_filename, output_dir, **kwargs
                )
                results[format_name] = file_path
                self.logger.info(f"Successfully exported {format_name} to {file_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to export {format_name}: {e}")
                results[format_name] = None
        
        return results