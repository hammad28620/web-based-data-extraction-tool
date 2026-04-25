"""
Input Validators
Validates user input for URLs, selectors, and other parameters
"""

import logging
import re
from urllib.parse import urlparse
import ipaddress

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def is_private_ip(hostname: str) -> bool:
    """
    Check if hostname/IP is private or reserved
    
    Args:
        hostname (str): Hostname or IP address to check
        
    Returns:
        bool: True if private/reserved, False otherwise
    """
    try:
        # Check if it's an IP address
        ip = ipaddress.ip_address(hostname)
        
        # Check if it's a private, loopback, or link-local address
        return (
            ip.is_private or 
            ip.is_loopback or 
            ip.is_link_local or 
            ip.is_multicast or 
            ip.is_reserved
        )
    except ValueError:
        # Not an IP address, check if it looks like localhost-like hostname
        hostname_lower = hostname.lower()
        
        private_patterns = [
            'localhost',
            '127.',
            '192.168.',
            '10.',
            '172.16.',
            '172.17.',
            '172.18.',
            '172.19.',
            '172.20.',
            '172.21.',
            '172.22.',
            '172.23.',
            '172.24.',
            '172.25.',
            '172.26.',
            '172.27.',
            '172.28.',
            '172.29.',
            '172.30.',
            '172.31.',
            '0.0.0.0',
            '169.254.',
            '::1',  # IPv6 loopback
            'fc00:',  # IPv6 private
            'fe80:',  # IPv6 link-local
            '.local',
            '.internal',
            '.private',
            '.dev',
            '.test',
            '.example',
        ]
        
        for pattern in private_patterns:
            if hostname_lower.startswith(pattern) or pattern in hostname_lower:
                return True
        
        return False


def validate_url(url: str) -> bool:
    """
    Validate if the URL is in correct format and safe to fetch
    Prevents SSRF attacks by blocking private/internal addresses
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if valid, False otherwise
        
    Raises:
        ValidationError: If URL is invalid or potentially unsafe
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")
    
    url = url.strip()
    
    if len(url) < 10:
        raise ValidationError("URL too short")
    
    # Check if URL starts with http or https
    if not url.startswith(('http://', 'https://')):
        raise ValidationError("URL must start with http:// or https://")
    
    # Check for HTML/JavaScript injection in URL
    suspicious_patterns = ['<script', 'javascript:', 'onerror=', 'onload=']
    url_lower = url.lower()
    for pattern in suspicious_patterns:
        if pattern in url_lower:
            raise ValidationError(f"Suspicious pattern detected in URL: {pattern}")
    
    # Parse URL
    try:
        result = urlparse(url)
        
        # Check for required parts
        if not result.scheme or not result.netloc:
            raise ValidationError("Invalid URL format")
        
        # Check domain name
        if '.' not in result.netloc and not result.netloc.startswith('localhost'):
            # Allow localhost without dot
            if result.netloc != 'localhost' and ':' not in result.netloc:
                raise ValidationError("Invalid domain name")
        
        # SSRF Protection: Check for private/internal addresses
        # Extract hostname from netloc (remove port if present)
        hostname = result.netloc.split(':')[0]
        
        if is_private_ip(hostname):
            raise ValidationError("Access to private/internal addresses is not allowed")
        
        # Block file:// protocol
        if result.scheme == 'file':
            raise ValidationError("file:// protocol is not allowed")
        
        # Block data: protocol
        if result.scheme == 'data':
            raise ValidationError("data: protocol is not allowed")
        
        logger.info(f"URL validated successfully: {url}")
        return True
    
    except ValidationError:
        raise
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
    
    # Check for event handlers to prevent XSS
    event_handlers = [
        'onload', 'onerror', 'onmouseover', 'onmouseout', 'onclick', 'ondblclick',
        'onkeydown', 'onkeyup', 'onkeypress', 'onfocus', 'onblur', 'onchange',
        'onsubmit', 'onreset', 'onabort', 'ondrag', 'ondrop', 'onpaste', 'oncopy',
        'oncut', 'onwheel', 'onscroll', 'onresize'
    ]
    selector_lower = selector.lower()
    for handler in event_handlers:
        if f'{handler}=' in selector_lower or f'{handler} ' in selector_lower:
            raise ValidationError(f"Invalid event handler detected: {handler}")
    
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
        data (dict): Request data containing url and optional selector
        
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
    
    # Extract and validate selector (now optional)
    selector = data.get('selector', '').strip()
    if selector:  # Only validate if provided
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
        'selector': selector if selector else None,  # None if not provided
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
