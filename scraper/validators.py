"""
Input Validators
Validates user input for URLs, selectors, and other parameters
"""

import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_url(url: str) -> bool:
    """
    Validate if the URL is in correct format
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if valid, False otherwise
        
    Raises:
        ValidationError: If URL is invalid
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")
    
    url = url.strip()
    
    if len(url) < 10:
        raise ValidationError("URL too short")
    
    # Check if URL starts with http or https
    if not url.startswith(('http://', 'https://')):
        raise ValidationError("URL must start with http:// or https://")
    
    # Parse URL
    try:
        result = urlparse(url)
        
        # Check for required parts
        if not result.scheme or not result.netloc:
            raise ValidationError("Invalid URL format")
        
        # Check domain name
        if '.' not in result.netloc:
            raise ValidationError("Invalid domain name")
        
        logger.info(f"URL validated successfully: {url}")
        return True
    
    except Exception as e:
        logger.error(f"URL validation failed: {str(e)}")
        raise ValidationError(f"Invalid URL format: {str(e)}")


def validate_selector(selector: str) -> bool:
    """
    Validate CSS selector or HTML tag
    
    Args:
        selector (str): CSS selector or HTML tag to validate
        
    Returns:
        bool: True if valid, False otherwise
        
    Raises:
        ValidationError: If selector is invalid
    """
    if not selector or not isinstance(selector, str):
        raise ValidationError("Selector must be a non-empty string")
    
    selector = selector.strip()
    
    if len(selector) < 1:
        raise ValidationError("Selector cannot be empty")
    
    if len(selector) > 500:
        raise ValidationError("Selector is too long (max 500 characters)")
    
    # Check for very suspicious patterns
    if '<script' in selector.lower() or 'javascript:' in selector.lower():
        raise ValidationError("Invalid selector pattern detected")
    
    # Allow common selectors
    # Valid patterns: tag names, class names (.class), IDs (#id), CSS selectors
    valid_selector_patterns = [
        r'^[a-zA-Z][a-zA-Z0-9_-]*$',          # Tag name (p, div, h1, etc.)
        r'^\.[a-zA-Z0-9_-]+$',                # Class (.class)
        r'^#[a-zA-Z0-9_-]+$',                 # ID (#id)
        r'^[a-zA-Z0-9\s.,#\[\]="\':-]+$',    # Complex selectors
    ]
    
    is_valid = False
    for pattern in valid_selector_patterns:
        if re.match(pattern, selector):
            is_valid = True
            break
    
    if not is_valid:
        logger.warning(f"Suspicious selector pattern: {selector}")
        # Don't block, just warn - let BeautifulSoup handle it
    
    logger.info(f"Selector validated: {selector}")
    return True


def validate_page_number(pages: int) -> bool:
    """
    Validate page number for multi-page scraping
    
    Args:
        pages (int): Number of pages to scrape
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If invalid
    """
    if not isinstance(pages, int):
        raise ValidationError("Page number must be an integer")
    
    if pages < 1:
        raise ValidationError("Page number must be at least 1")
    
    if pages > 100:
        raise ValidationError("Page number cannot exceed 100 (to prevent abuse)")
    
    return True


def validate_scrape_request(data: dict) -> dict:
    """
    Validate complete scrape request
    
    Args:
        data (dict): Request data containing url and selector
        
    Returns:
        dict: Validated and cleaned data
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Request must be a JSON object")
    
    # Extract and validate URL
    url = data.get('url', '').strip()
    if not url:
        raise ValidationError("URL is required")
    
    try:
        validate_url(url)
    except ValidationError as e:
        raise ValidationError(f"URL validation failed: {str(e)}")
    
    # Extract and validate selector
    selector = data.get('selector', '').strip()
    if not selector:
        raise ValidationError("Selector is required")
    
    try:
        validate_selector(selector)
    except ValidationError as e:
        raise ValidationError(f"Selector validation failed: {str(e)}")
    
    # Validate pages (optional)
    pages = data.get('pages', 1)
    if pages:
        try:
            if isinstance(pages, str):
                pages = int(pages)
            validate_page_number(pages)
        except (ValidationError, ValueError) as e:
            raise ValidationError(f"Pages validation failed: {str(e)}")
    
    # Return cleaned data
    return {
        'url': url,
        'selector': selector,
        'pages': max(1, int(pages)) if pages else 1,
        'include_attributes': data.get('include_attributes', False)
    }


def sanitize_selector(selector: str) -> str:
    """
    Sanitize selector to prevent issues
    
    Args:
        selector (str): Raw selector
        
    Returns:
        str: Sanitized selector
    """
    if not selector:
        return selector
    
    # Remove leading/trailing whitespace
    selector = selector.strip()
    
    # Remove any potential script tags or dangerous patterns
    selector = selector.replace('<', '').replace('>', '')
    
    return selector
