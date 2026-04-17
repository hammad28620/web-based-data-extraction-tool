"""
Web Scraping Engine
Handles fetching webpage content and extracting data using BeautifulSoup
"""

import requests
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)


class ScraperEngine:
    """
    Web scraping engine using BeautifulSoup
    Handles HTTP requests, HTML parsing, and data extraction
    """
    
    def __init__(self, request_timeout=30, scraping_delay=1, user_agent=None):
        """
        Initialize scraper with configuration
        
        Args:
            request_timeout (int): Timeout for HTTP requests in seconds (default: 30s)
            scraping_delay (int): Delay between requests in seconds
            user_agent (str): Custom user agent string
        """
        self.request_timeout = request_timeout
        self.scraping_delay = scraping_delay
        self.user_agent = user_agent or (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/91.0.4472.124 Safari/537.36'
        )
        
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
    
    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch webpage content
        
        Args:
            url (str): URL to fetch
            
        Returns:
            str: HTML content or None if fetch fails
            
        Raises:
            RequestException: If request fails
        """
        try:
            logger.info(f"Fetching URL: {url}")
            
            response = self.session.get(
                url,
                timeout=self.request_timeout,
                allow_redirects=True
            )
            
            response.raise_for_status()  # Raise exception for bad status codes
            
            logger.info(f"Successfully fetched {url} (Status: {response.status_code})")
            
            return response.text
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while fetching {url}")
            raise Exception(f"Request timeout after {self.request_timeout} seconds")
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {url}: {str(e)}")
            raise Exception(f"Cannot connect to website: {str(e)}")
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {url}: {str(e)}")
            status_code = e.response.status_code
            raise Exception(f"HTTP {status_code} error: {e.response.reason}")
        
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise Exception(f"Failed to fetch page: {str(e)}")
    
    def parse_html(self, html_content: str) -> Optional[BeautifulSoup]:
        """
        Parse HTML content using BeautifulSoup
        
        Args:
            html_content (str): HTML content to parse
            
        Returns:
            BeautifulSoup: Parsed HTML object or None if parsing fails
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            logger.info("HTML parsed successfully")
            return soup
        
        except Exception as e:
            logger.error(f"Error parsing HTML: {str(e)}")
            raise Exception(f"Failed to parse HTML: {str(e)}")
    
    def clean_text(self, text: str) -> str:
        """
        Clean HTML-like text and normalize whitespace
        
        Args:
            text (str): Text to clean
            
        Returns:
            str: Cleaned text without extra whitespace
        """
        # Remove extra whitespace and newlines
        cleaned = ' '.join(text.split())
        return cleaned.strip()
    
    def extract_elements(self, soup: BeautifulSoup, selector: str) -> List[str]:
        """
        Extract elements by CSS selector or tag name
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            selector (str): CSS selector, tag name, or class selector
            
        Returns:
            List[str]: List of extracted text content
        """
        try:
            if not selector or not selector.strip():
                raise ValueError("Selector cannot be empty")
            
            selector = selector.strip()
            elements = []
            
            logger.info(f"Extracting elements with selector: {selector}")
            
            # Try as CSS selector first
            try:
                found_elements = soup.select(selector)
            except Exception:
                # If CSS selector fails, try simpler selection methods
                if selector.startswith('.'):
                    # Class selector
                    class_name = selector[1:]
                    found_elements = soup.find_all(class_=class_name)
                elif selector.startswith('#'):
                    # ID selector
                    element_id = selector[1:]
                    elem = soup.find(id=element_id)
                    found_elements = [elem] if elem else []
                else:
                    # Tag name
                    found_elements = soup.find_all(selector)
            
            if not found_elements:
                logger.warning(f"No elements found with selector: {selector}")
                return []
            
            logger.info(f"Found {len(found_elements)} elements")
            
            # Extract text from elements
            for element in found_elements:
                text = element.get_text(strip=True)
                if text:  # Only add non-empty text
                    # Clean the text to remove extra whitespace
                    cleaned_text = self.clean_text(text)
                    if cleaned_text:
                        elements.append(cleaned_text)
            
            logger.info(f"Extracted {len(elements)} non-empty elements")
            
            return elements
        
        except Exception as e:
            logger.error(f"Error extracting elements: {str(e)}")
            raise Exception(f"Failed to extract elements: {str(e)}")
    
    def extract_with_attributes(self, soup: BeautifulSoup, selector: str) -> List[Dict]:
        """
        Extract elements with their attributes
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            selector (str): CSS selector
            
        Returns:
            List[Dict]: List of dictionaries containing text and attributes
        """
        try:
            selector = selector.strip()
            elements = []
            
            logger.info(f"Extracting elements with attributes: {selector}")
            
            # Find elements
            try:
                found_elements = soup.select(selector)
            except Exception:
                if selector.startswith('.'):
                    class_name = selector[1:]
                    found_elements = soup.find_all(class_=class_name)
                elif selector.startswith('#'):
                    element_id = selector[1:]
                    elem = soup.find(id=element_id)
                    found_elements = [elem] if elem else []
                else:
                    found_elements = soup.find_all(selector)
            
            # Extract with attributes
            for element in found_elements:
                item = {
                    'text': element.get_text(strip=True),
                    'tag': element.name,
                    'attributes': dict(element.attrs)
                }
                elements.append(item)
            
            return elements
        
        except Exception as e:
            logger.error(f"Error extracting elements with attributes: {str(e)}")
            raise Exception(f"Failed to extract elements with attributes: {str(e)}")
    
    def scrape(self, url: str, selector: str, include_attributes: bool = False) -> Dict:
        """
        Complete scraping workflow
        
        Args:
            url (str): URL to scrape
            selector (str): CSS selector or tag name
            include_attributes (bool): Whether to include element attributes
            
        Returns:
            Dict: Scraping result with data
        """
        try:
            # Fetch page
            html_content = self.fetch_page(url)
            
            # Parse HTML
            soup = self.parse_html(html_content)
            
            # Extract elements
            if include_attributes:
                data = self.extract_with_attributes(soup, selector)
            else:
                data = self.extract_elements(soup, selector)
            
            logger.info(f"Scraping completed successfully. Found {len(data)} items")
            
            return {
                'success': True,
                'url': url,
                'selector': selector,
                'data': data,
                'count': len(data),
                'message': f'Successfully extracted {len(data)} items'
            }
        
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            return {
                'success': False,
                'url': url,
                'selector': selector,
                'data': [],
                'count': 0,
                'error': str(e)
            }
    
    def scrape_multiple_pages(self, 
                            start_url: str, 
                            selector: str,
                            pages: int = 1,
                            next_page_selector: Optional[str] = None) -> Dict:
        """
        Scrape multiple pages
        
        Args:
            start_url (str): Starting URL
            selector (str): CSS selector for data extraction
            pages (int): Number of pages to scrape
            next_page_selector (str): Selector for next page link
            
        Returns:
            Dict: Results from all pages
        """
        all_data = []
        current_url = start_url
        pages_scraped = 0
        
        try:
            for page_num in range(pages):
                logger.info(f"Scraping page {page_num + 1}/{pages}: {current_url}")
                
                # Fetch and parse
                html_content = self.fetch_page(current_url)
                soup = self.parse_html(html_content)
                
                # Extract data
                data = self.extract_elements(soup, selector)
                all_data.extend(data)
                
                pages_scraped += 1
                
                # Add delay between requests
                if page_num < pages - 1:
                    logger.info(f"Waiting {self.scraping_delay} seconds before next request...")
                    time.sleep(self.scraping_delay)
                
                # Find next page URL if needed
                if page_num < pages - 1 and next_page_selector:
                    try:
                        next_link = soup.select_one(next_page_selector)
                        if next_link and next_link.get('href'):
                            next_page_url = next_link['href']
                            # Handle relative URLs
                            if not next_page_url.startswith('http'):
                                from urllib.parse import urljoin
                                next_page_url = urljoin(current_url, next_page_url)
                            current_url = next_page_url
                            logger.info(f"Found next page: {current_url}")
                        else:
                            logger.warning("Next page selector didn't find a link")
                            break
                    except Exception as e:
                        logger.warning(f"Error finding next page: {str(e)}")
                        break
            
            return {
                'success': True,
                'pages_scraped': pages_scraped,
                'data': all_data,
                'count': len(all_data),
                'message': f'Successfully scraped {pages_scraped} pages with {len(all_data)} total items'
            }
        
        except Exception as e:
            logger.error(f"Multi-page scraping failed: {str(e)}")
            return {
                'success': False,
                'pages_scraped': pages_scraped,
                'data': all_data,
                'count': len(all_data),
                'error': str(e)
            }
