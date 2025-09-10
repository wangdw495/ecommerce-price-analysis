"""Custom exceptions for the price monitoring system."""


class PriceMonitorError(Exception):
    """Base exception for all price monitor errors."""
    pass


class CollectorError(PriceMonitorError):
    """Exception raised by data collectors."""
    pass


class AnalyzerError(PriceMonitorError):
    """Exception raised by data analyzers."""
    pass


class ExporterError(PriceMonitorError):
    """Exception raised by data exporters."""
    pass


class RateLimitError(CollectorError):
    """Exception raised when rate limited by a platform."""
    pass


class ValidationError(PriceMonitorError):
    """Exception raised for data validation errors."""
    pass


class DatabaseError(PriceMonitorError):
    """Exception raised for database operation errors."""
    pass


class ConfigurationError(PriceMonitorError):
    """Exception raised for configuration errors."""
    pass