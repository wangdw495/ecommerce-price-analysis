"""Logging configuration for the price monitoring system."""

import logging
import logging.config
import os
from datetime import datetime
from pathlib import Path


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    console_output: bool = True,
    file_output: bool = True
) -> None:
    """Setup logging configuration for the application.
    
    Args:
        log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        log_dir: Directory for log files
        console_output: Whether to output to console
        file_output: Whether to output to files
    """
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d')
    log_filename = log_path / f"price_monitor_{timestamp}.log"
    error_log_filename = log_path / f"price_monitor_errors_{timestamp}.log"
    
    # Define log format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    detailed_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    
    # Configure logging
    handlers = []
    
    # Console handler
    if console_output:
        console_handler = {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        }
        handlers.append('console')
    
    # File handler
    if file_output:
        file_handler = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': str(log_filename),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        }
        
        # Error file handler
        error_file_handler = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': str(error_log_filename),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 3,
            'encoding': 'utf-8'
        }
        
        handlers.extend(['file', 'error_file'])
    
    # Logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': log_format,
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': detailed_format,
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {},
        'loggers': {
            'ecommerce_price_monitor': {
                'handlers': handlers,
                'level': 'DEBUG',
                'propagate': False
            },
            # Third-party library loggers
            'requests': {
                'handlers': handlers,
                'level': 'WARNING',
                'propagate': False
            },
            'urllib3': {
                'handlers': handlers,
                'level': 'WARNING',
                'propagate': False
            },
            'matplotlib': {
                'handlers': handlers,
                'level': 'WARNING',
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': handlers
        }
    }
    
    # Add handlers to config
    if console_output:
        config['handlers']['console'] = console_handler
    
    if file_output:
        config['handlers']['file'] = file_handler
        config['handlers']['error_file'] = error_file_handler
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log the setup
    logger = logging.getLogger('ecommerce_price_monitor.setup')
    logger.info(f"Logging configured - Level: {log_level}, Console: {console_output}, File: {file_output}")
    
    if file_output:
        logger.info(f"Log files: {log_filename}, {error_log_filename}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"ecommerce_price_monitor.{name}")


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Format the log record with colors."""
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        return f"{color}{log_message}{self.COLORS['RESET']}"


def setup_colored_logging(log_level: str = "INFO") -> None:
    """Setup colored logging for better console readability.
    
    Args:
        log_level: Logging level
    """
    # Create colored formatter
    colored_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup console handler with colored formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(colored_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    logger = logging.getLogger('ecommerce_price_monitor')
    logger.setLevel('DEBUG')
    
    logger.info("Colored logging configured")


def configure_third_party_loggers(level: str = "WARNING") -> None:
    """Configure third-party library loggers to reduce noise.
    
    Args:
        level: Log level for third-party libraries
    """
    third_party_loggers = [
        'requests',
        'urllib3',
        'selenium',
        'matplotlib',
        'plotly',
        'pandas',
        'numpy'
    ]
    
    for logger_name in third_party_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        
    # Suppress specific noisy loggers
    logging.getLogger('urllib3.connectionpool').setLevel('ERROR')
    logging.getLogger('matplotlib.font_manager').setLevel('ERROR')