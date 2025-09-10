"""Helper utility functions."""

import re
import unicodedata
from typing import Optional, Union
from urllib.parse import urlparse


def format_currency(amount: float, currency: str = "USD", decimal_places: int = 2) -> str:
    """Format a currency amount for display.
    
    Args:
        amount: The amount to format
        currency: Currency code (e.g., "USD", "EUR")
        decimal_places: Number of decimal places
        
    Returns:
        Formatted currency string
    """
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "CNY": "¥",
    }
    
    symbol = symbols.get(currency, currency + " ")
    
    if currency == "JPY":  # Japanese Yen typically has no decimal places
        decimal_places = 0
    
    formatted = f"{amount:,.{decimal_places}f}"
    
    if symbol in ["$", "£"]:
        return f"{symbol}{formatted}"
    else:
        return f"{formatted} {symbol}"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values.
    
    Args:
        old_value: Original value
        new_value: New value
        
    Returns:
        Percentage change (positive for increase, negative for decrease)
    """
    if old_value == 0:
        return 100.0 if new_value > 0 else 0.0
    
    return ((new_value - old_value) / old_value) * 100


def normalize_product_name(name: str) -> str:
    """Normalize product name for comparison and matching.
    
    Args:
        name: Original product name
        
    Returns:
        Normalized product name
    """
    if not name:
        return ""
    
    # 检测是否包含中文字符
    if re.search(r'[\u4e00-\u9fa5]', name):
        # 使用中文文本处理器
        try:
            from .chinese_text_processor import chinese_processor
            return chinese_processor.normalize_product_name(name)
        except ImportError:
            # 如果jieba等依赖不可用，使用基础处理
            pass
    
    # 英文处理逻辑
    # Convert to lowercase
    normalized = name.lower()
    
    # Remove accents and special characters
    normalized = unicodedata.normalize('NFD', normalized)
    normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    
    # Remove extra whitespace and common words
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = normalized.strip()
    
    # Remove common filler words
    filler_words = ['new', 'original', 'genuine', 'official', 'brand', 'item']
    words = normalized.split()
    words = [word for word in words if word not in filler_words]
    
    return ' '.join(words)


def extract_numeric_value(text: str) -> Optional[float]:
    """Extract the first numeric value from a text string.
    
    Args:
        text: Text containing numeric value
        
    Returns:
        First numeric value found, or None if none found
    """
    if not text:
        return None
    
    # Find all numeric patterns
    pattern = r'-?\d+(?:,\d{3})*(?:\.\d+)?'
    matches = re.findall(pattern, text)
    
    if not matches:
        return None
    
    try:
        # Remove commas and convert to float
        numeric_str = matches[0].replace(',', '')
        return float(numeric_str)
    except (ValueError, IndexError):
        return None


def validate_url(url: str) -> bool:
    """Validate if a string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    if not url:
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def safe_divide(numerator: Union[int, float], denominator: Union[int, float]) -> float:
    """Safely divide two numbers, returning 0 if denominator is 0.
    
    Args:
        numerator: Number to divide
        denominator: Number to divide by
        
    Returns:
        Result of division, or 0 if denominator is 0
    """
    if denominator == 0:
        return 0.0
    return numerator / denominator


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add to truncated text
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    truncate_at = max_length - len(suffix)
    return text[:truncate_at].rstrip() + suffix


def clean_html_text(text: str) -> str:
    """Clean HTML tags and entities from text.
    
    Args:
        text: Text containing HTML
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Replace common HTML entities
    entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' ',
    }
    
    for entity, replacement in entities.items():
        text = text.replace(entity, replacement)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def generate_product_hash(platform: str, product_id: str, name: str) -> str:
    """Generate a unique hash for a product across platforms.
    
    Args:
        platform: Platform name
        product_id: Product ID on the platform
        name: Product name
        
    Returns:
        Unique hash string
    """
    import hashlib
    
    # Create a unique string from platform, ID, and normalized name
    normalized_name = normalize_product_name(name)
    unique_string = f"{platform.lower()}:{product_id}:{normalized_name}"
    
    # Generate SHA-256 hash
    return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()[:16]