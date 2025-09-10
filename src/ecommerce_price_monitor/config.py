"""Configuration management for the price monitoring system."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ScrapingConfig:
    """Configuration for web scraping."""
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    request_delay: float = 1.0
    timeout: int = 30
    retry_attempts: int = 3
    use_proxy: bool = False
    proxy_list: list = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=lambda: {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })


@dataclass
class DatabaseConfig:
    """Configuration for database storage."""
    type: str = "sqlite"
    path: str = "data/price_monitor.db"
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None


@dataclass
class NotificationConfig:
    """Configuration for notifications."""
    enabled: bool = False
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: list = field(default_factory=list)
    slack_webhook_url: str = ""


@dataclass
class AnalysisConfig:
    """Configuration for price analysis."""
    price_change_threshold: float = 0.05  # 5%
    volatility_window: int = 7  # days
    trend_window: int = 30  # days
    outlier_detection: bool = True
    seasonal_analysis: bool = True


@dataclass
class Config:
    """Main configuration class."""
    scraping: ScrapingConfig = field(default_factory=ScrapingConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    notification: NotificationConfig = field(default_factory=NotificationConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    
    # Supported platforms
    supported_platforms: list = field(default_factory=lambda: [
        # 国际平台
        'amazon', 'ebay', 'walmart', 'target', 'bestbuy',
        # 国内平台
        'jd', 'jingdong', 'taobao', 'xiaohongshu', 'xhs', 'douyin'
    ])
    
    # Export formats
    export_formats: list = field(default_factory=lambda: [
        'csv', 'excel', 'json', 'markdown', 'png', 'html'
    ])


class ConfigManager:
    """Manages configuration loading and saving."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = Path(config_path or "config/config.yaml")
        self._config: Optional[Config] = None
    
    def load_config(self) -> Config:
        """Load configuration from file or create default."""
        if self._config is not None:
            return self._config
            
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                self._config = self._dict_to_config(data)
            except Exception as e:
                print(f"Error loading config: {e}. Using default configuration.")
                self._config = Config()
        else:
            self._config = Config()
            self.save_config()
            
        return self._config
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        if self._config is None:
            return
            
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = self._config_to_dict(self._config)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
    
    def _dict_to_config(self, data: Dict[str, Any]) -> Config:
        """Convert dictionary to Config object."""
        config = Config()
        
        if 'scraping' in data:
            config.scraping = ScrapingConfig(**data['scraping'])
        if 'database' in data:
            config.database = DatabaseConfig(**data['database'])
        if 'notification' in data:
            config.notification = NotificationConfig(**data['notification'])
        if 'analysis' in data:
            config.analysis = AnalysisConfig(**data['analysis'])
        if 'supported_platforms' in data:
            config.supported_platforms = data['supported_platforms']
        if 'export_formats' in data:
            config.export_formats = data['export_formats']
            
        return config
    
    def _config_to_dict(self, config: Config) -> Dict[str, Any]:
        """Convert Config object to dictionary."""
        return {
            'scraping': {
                'user_agent': config.scraping.user_agent,
                'request_delay': config.scraping.request_delay,
                'timeout': config.scraping.timeout,
                'retry_attempts': config.scraping.retry_attempts,
                'use_proxy': config.scraping.use_proxy,
                'proxy_list': config.scraping.proxy_list,
                'headers': config.scraping.headers,
            },
            'database': {
                'type': config.database.type,
                'path': config.database.path,
                'host': config.database.host,
                'port': config.database.port,
                'username': config.database.username,
                'password': config.database.password,
                'database': config.database.database,
            },
            'notification': {
                'enabled': config.notification.enabled,
                'email_smtp_server': config.notification.email_smtp_server,
                'email_smtp_port': config.notification.email_smtp_port,
                'email_username': config.notification.email_username,
                'email_password': config.notification.email_password,
                'email_recipients': config.notification.email_recipients,
                'slack_webhook_url': config.notification.slack_webhook_url,
            },
            'analysis': {
                'price_change_threshold': config.analysis.price_change_threshold,
                'volatility_window': config.analysis.volatility_window,
                'trend_window': config.analysis.trend_window,
                'outlier_detection': config.analysis.outlier_detection,
                'seasonal_analysis': config.analysis.seasonal_analysis,
            },
            'supported_platforms': config.supported_platforms,
            'export_formats': config.export_formats,
        }


# Global configuration instance
config_manager = ConfigManager()