"""
Pagination Handler Module
Handles pagination detection and multi-page scraping workflows
"""

import logging
from bs4 import BeautifulSoup
from typing import Optional, Dict, List, Tuple
from urllib.parse import urljoin
import re

logger = logging.getLogger(__name__)


class PaginationHandler:
    """
    Handle pagination detection and multi-page scraping
    """
    
    # Common pagination selector patterns
    NEXT_PAGE_SELECTORS = [
        'a.next',
        'a[rel="next"]',
        '.pagination a.next',
        '.pager a.next',
        'a:contains("Next")',
        'a:contains("→")',
        '.pagination .next a',
        'li.next a',
        'a[aria-label*="next"]',
        'button.next',
        '.btn-next',
    ]
    
    PAGINATION_SELECTORS = [
        '.pagination',
        '.pager',
        'nav.pagination',
        '.page-numbers',
        '.paginator',
    ]
    
    def __init__(self, max_pages: int = 10):
        """
        Initialize pagination handler
        
        Args:
            max_pages (int): Maximum pages allowed to scrape
        """
        self.max_pages = max_pages
        logger.info(f"Pagination handler initialized with max_pages={max_pages}")
    
    def detect_pagination(self, soup: BeautifulSoup) -> Dict:
        """
        Detect if page has pagination
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            Dict: Pagination detection results
        """
        try:
            result = {
                'has_pagination': False,
                'next_page_url': None,
                'pagination_type': None,
                'page_info': {}
            }
            
            logger.info("Detecting pagination...")
            
            # Try to find pagination container
            for selector in self.PAGINATION_SELECTORS:
                pagination = soup.select_one(selector)
                if pagination:
                    logger.info(f"Found pagination container: {selector}")
                    result['has_pagination'] = True
                    result['pagination_type'] = selector
                    
                    # Try to get next page link
                    next_url = self._find_next_page_link(soup)
                    if next_url:
                        result['next_page_url'] = next_url
                    
                    break
            
            # Additional check: look for common pagination patterns
            if not result['has_pagination']:
                # Check for common pagination patterns in links
                all_links = soup.find_all('a')
                for link in all_links:
                    text = link.get_text(strip=True).lower()
                    if any(word in text for word in ['next', 'more', '→', '»']):
                        result['has_pagination'] = True
                        result['next_page_url'] = link.get('href')
                        result['pagination_type'] = 'link_text_pattern'
                        logger.info("Detected pagination via link text pattern")
                        break
            
            logger.info(f"Pagination detection result: {result}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error detecting pagination: {str(e)}")
            return {'has_pagination': False, 'error': str(e)}
    
    def _find_next_page_link(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Find next page link using various selectors
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            str: URL of next page or None
        """
        try:
            for selector in self.NEXT_PAGE_SELECTORS:
                # Simple selectors (avoid :contains pseudo-selector)
                if ':contains' not in selector and ':' not in selector:
                    link = soup.select_one(selector)
                    if link and link.get('href'):
                        return link.get('href')
            
            return None
        
        except Exception as e:
            logger.warning(f"Error finding next page link: {str(e)}")
            return None
    
    def get_next_page_url(self, 
                         soup: BeautifulSoup, 
                         current_url: str,
                         custom_selector: Optional[str] = None) -> Optional[str]:
        """
        Get the URL of the next page
        
        Args:
            soup (BeautifulSoup): Parsed HTML of current page
            current_url (str): Current page URL (for relative URL resolution)
            custom_selector (str): Custom selector for next page link
            
        Returns:
            str: Absolute URL of next page or None
        """
        try:
            next_url = None
            
            # Try custom selector first if provided
            if custom_selector:
                try:
                    link = soup.select_one(custom_selector)
                    if link and link.get('href'):
                        next_url = link.get('href')
                        logger.info(f"Found next page using custom selector: {next_url}")
                except:
                    pass
            
            # Try default selectors
            if not next_url:
                next_url = self._find_next_page_link(soup)
            
            if not next_url:
                logger.warning("No next page link found")
                return None
            
            # Convert relative URL to absolute
            if not next_url.startswith(('http://', 'https://')):
                next_url = urljoin(current_url, next_url)
                logger.info(f"Converted relative URL to absolute: {next_url}")
            
            return next_url
        
        except Exception as e:
            logger.error(f"Error getting next page URL: {str(e)}")
            return None
    
    def extract_page_info(self, soup: BeautifulSoup) -> Dict:
        """
        Extract page information (current page, total pages, etc.)
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            Dict: Page information
        """
        try:
            info = {
                'current_page': None,
                'total_pages': None,
                'current_page_text': None,
                'page_numbers': []
            }
            
            # Look for page information in common locations
            pagination = soup.select_one('.pagination, .pager, nav.pagination')
            if pagination:
                # Get all page links
                page_links = pagination.find_all('a')
                page_numbers = []
                
                for link in page_links:
                    text = link.get_text(strip=True)
                    # Try to extract page numbers
                    if text.isdigit():
                        page_numbers.append(int(text))
                
                if page_numbers:
                    info['page_numbers'] = sorted(set(page_numbers))
                    info['total_pages'] = max(page_numbers)
                
                # Check for active page indicator
                active = pagination.select_one('.active, .current, [aria-current="page"]')
                if active:
                    text = active.get_text(strip=True)
                    if text.isdigit():
                        info['current_page'] = int(text)
                    info['current_page_text'] = text
            
            logger.info(f"Extracted page info: {info}")
            
            return info
        
        except Exception as e:
            logger.error(f"Error extracting page info: {str(e)}")
            return {'error': str(e)}
    
    def validate_next_page(self, next_url: str, current_url: str) -> bool:
        """
        Validate if next page URL is legitimate
        
        Args:
            next_url (str): URL of next page
            current_url (str): Current page URL
            
        Returns:
            bool: True if next page URL is valid
        """
        try:
            if not next_url:
                return False
            
            # Extract domains
            current_domain = current_url.split('/')[2]
            next_domain = next_url.split('/')[2]
            
            # Don't follow links to different domains
            if current_domain != next_domain:
                logger.warning(f"Domain mismatch: {current_domain} != {next_domain}")
                return False
            
            # Check if URL contains obvious pagination indicators
            pagination_indicators = ['page', 'p=', 'offset=', 'start=', 'num=']
            if any(indicator in next_url.lower() for indicator in pagination_indicators):
                logger.info(f"Valid pagination URL detected: {next_url}")
                return True
            
            # If no pagination indicator but same domain, might still be valid
            if current_domain == next_domain:
                logger.info(f"Same domain, accepting next page: {next_url}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error validating next page: {str(e)}")
            return False
    
    def generate_page_urls(self, 
                          base_url: str, 
                          page_count: int,
                          page_param: str = 'page',
                          start_page: int = 1) -> List[str]:
        """
        Generate pagination URLs using common parameter patterns
        
        Args:
            base_url (str): Base URL
            page_count (int): Number of pages to generate
            page_param (str): Parameter name for page number (page, p, offset, etc.)
            start_page (int): Starting page number
            
        Returns:
            List[str]: List of generated URLs
        """
        try:
            urls = []
            
            for page_num in range(start_page, start_page + page_count):
                # Check if URL already has parameters
                if '?' in base_url:
                    url = f"{base_url}&{page_param}={page_num}"
                else:
                    url = f"{base_url}?{page_param}={page_num}"
                
                urls.append(url)
            
            logger.info(f"Generated {len(urls)} pagination URLs")
            
            return urls
        
        except Exception as e:
            logger.error(f"Error generating page URLs: {str(e)}")
            return []


class ProgressTracker:
    """
    Track scraping progress for multi-page operations
    """
    
    def __init__(self, total_items: int = 0, total_pages: int = 1):
        """
        Initialize progress tracker
        
        Args:
            total_items (int): Total items to scrape
            total_pages (int): Total pages to scrape
        """
        self.total_items = total_items
        self.total_pages = total_pages
        self.current_page = 0
        self.items_scraped = 0
        self.pages_completed = 0
        self.start_time = None
        self.current_page_items = 0
    
    def start_page(self, page_num: int):
        """Mark the start of scraping a page"""
        self.current_page = page_num
        self.current_page_items = 0
        logger.info(f"Starting page {page_num}/{self.total_pages}")
    
    def update(self, items_count: int = 0):
        """
        Update progress
        
        Args:
            items_count (int): Items found on current page
        """
        self.current_page_items = items_count
        self.items_scraped += items_count
    
    def page_complete(self):
        """Mark current page as complete"""
        self.pages_completed += 1
    
    def get_progress(self) -> Dict:
        """
        Get current progress
        
        Returns:
            Dict: Progress information
        """
        progress = {
            'total_pages': self.total_pages,
            'pages_completed': self.pages_completed,
            'pages_remaining': self.total_pages - self.pages_completed,
            'current_page': self.current_page,
            'total_items': self.total_items,
            'items_scraped': self.items_scraped,
            'current_page_items': self.current_page_items,
            'page_progress': f"{self.pages_completed}/{self.total_pages}",
            'percentage': round((self.pages_completed / max(self.total_pages, 1)) * 100, 1)
        }
        return progress
    
    def get_summary(self) -> Dict:
        """
        Get progress summary
        
        Returns:
            Dict: Summary information
        """
        return {
            'status': 'completed' if self.pages_completed >= self.total_pages else 'in_progress',
            'pages_scraped': self.pages_completed,
            'total_pages': self.total_pages,
            'items_extracted': self.items_scraped,
            'completion_percentage': round((self.pages_completed / max(self.total_pages, 1)) * 100, 1)
        }
