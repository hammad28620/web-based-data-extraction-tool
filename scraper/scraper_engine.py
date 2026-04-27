"""
Web Scraping Engine
Handles fetching webpage content and extracting data using BeautifulSoup
"""

import requests
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import re
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class ScraperEngine:
    """
    Web scraping engine using BeautifulSoup
    Handles HTTP requests, HTML parsing, and data extraction
    """
    
    def __init__(self, request_timeout=30, scraping_delay=1, user_agent=None, max_retries=3):
        """
        Initialize scraper with configuration
        
        Args:
            request_timeout (int): Timeout for HTTP requests in seconds (default: 30s)
            scraping_delay (int): Delay between requests in seconds
            user_agent (str): Custom user agent string
            max_retries (int): Maximum number of retries for failed requests
        """
        self.request_timeout = request_timeout
        self.scraping_delay = scraping_delay
        self.max_retries = max_retries
        self.user_agent = user_agent or (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/91.0.4472.124 Safari/537.36'
        )
        
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        
        # Setup retry strategy with exponential backoff
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1  # Exponential backoff: 1, 2, 4, 8 seconds
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        logger.info(f"Scraper initialized with max_retries={max_retries}, backoff_factor=1")
    
    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch webpage content with retry logic
        
        Args:
            url (str): URL to fetch
            
        Returns:
            str: HTML content or None if fetch fails
            
        Raises:
            RequestException: If request fails after all retries
        """
        last_error = None
        
        # Manual retry loop for additional error handling
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"Fetching URL: {url} (Attempt {attempt + 1}/{self.max_retries + 1})")
                
                response = self.session.get(
                    url,
                    timeout=self.request_timeout,
                    allow_redirects=True
                )
                
                response.raise_for_status()  # Raise exception for bad status codes
                
                logger.info(f"Successfully fetched {url} (Status: {response.status_code})")
                
                return response.text
                
            except requests.exceptions.Timeout as e:
                last_error = f"Request timeout after {self.request_timeout} seconds"
                logger.warning(f"Timeout on attempt {attempt + 1}: {last_error}")
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
            
            except requests.exceptions.ConnectionError as e:
                last_error = f"Cannot connect to website: {str(e)}"
                logger.warning(f"Connection error on attempt {attempt + 1}: {last_error}")
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
            
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                last_error = f"HTTP {status_code} error: {e.response.reason}"
                logger.warning(f"HTTP error on attempt {attempt + 1}: {last_error}")
                
                # Don't retry on 4xx errors (except 429 which is handled by retry strategy)
                if 400 <= status_code < 500 and status_code != 429:
                    raise Exception(last_error)
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
            
            except Exception as e:
                last_error = f"Failed to fetch page: {str(e)}"
                logger.warning(f"Error on attempt {attempt + 1}: {last_error}")
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
        
        # All retries exhausted
        logger.error(f"Failed to fetch {url} after {self.max_retries + 1} attempts. Last error: {last_error}")
        raise Exception(last_error or "Failed to fetch page after all retries")
    
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
        Comprehensive text cleaning with multiple passes
        Removes HTML entities, special characters, URLs, metadata, etc.
        
        Args:
            text (str): Text to clean
            
        Returns:
            str: Cleaned text without extra whitespace and noise
        """
        # Pass 1: Remove HTML entities and special Unicode characters
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        text = text.replace('&apos;', "'")
        text = text.replace('&#x2013;', '-')  # En dash
        text = text.replace('&#x2014;', '-')  # Em dash
        text = text.replace('&#8217;', "'")   # Right single quote
        text = text.replace('&#8212;', '-')   # Em dash (numeric)
        
        # Pass 2: Remove URLs (http, https, ftp, www)
        text = re.sub(r'https?://[^\s]+', '', text)
        text = re.sub(r'www\.[^\s]+', '', text)
        text = re.sub(r'ftp://[^\s]+', '', text)
        
        # Pass 3: Remove email addresses
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)
        
        # Pass 4: Remove phone numbers (various formats)
        text = re.sub(r'\+?1?\s*\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}', '', text)
        text = re.sub(r'\+[0-9]{1,3}\s?[0-9]{1,14}', '', text)
        
        # Pass 5: Remove timestamps and dates
        text = re.sub(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', '', text)
        text = re.sub(r'\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:am|pm|AM|PM))?', '', text)
        
        # Pass 5a: Remove date names (Jan, Feb, etc.)
        text = re.sub(r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b', '', text, flags=re.IGNORECASE)
        
        # Pass 5b: Remove metadata patterns
        text = re.sub(r'(?:author|by|published|posted|updated|modified|written by)[\s:]+[^\n.;]*', '', text, flags=re.IGNORECASE)
        
        # Pass 5c: Remove pricing and cost patterns
        text = re.sub(r'[\$€£¥]\d+(?:[.,]\d{2})?', '', text)  # $99.99, €50, etc.
        text = re.sub(r'\b(?:price|cost|fee|charge)\s*[:=]\s*[^\n.;]*', '', text, flags=re.IGNORECASE)
        
        # Pass 5d: Remove rating and review patterns
        text = re.sub(r'\b\d+(?:\.\d)?\s*(?:out of|/)\s*\d+\s*(?:stars?|points?)?\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(?:rating|review|stars?)\s*[:=]\s*[^\n.;]*', '', text, flags=re.IGNORECASE)
        
        # Pass 6: Remove social media shares and counts
        text = re.sub(r'(?:shares?|likes?|comments?)\s*[:=]?\s*\d+', '', text, flags=re.IGNORECASE)
        
        # Pass 7: Remove social media handles and hashtags
        text = re.sub(r'@[a-zA-Z0-9_]+', '', text)
        text = re.sub(r'#[a-zA-Z0-9_]+', '', text)
        
        # Pass 8: Remove excessive punctuation and symbols
        # Keep basic punctuation but remove excessive repetition
        text = re.sub(r'([!?.;,\-*+/=|()[\]{}])\1{2,}', r'\1', text)
        
        # Pass 9: Remove lines that are mostly symbols
        text = re.sub(r'^[-_*=+~]{3,}$', '', text, flags=re.MULTILINE)
        
        # Pass 10: Remove bullet points and list markers at start
        text = re.sub(r'^\s*[•\-*+]\s+', '', text, flags=re.MULTILINE)
        
        # Pass 11: Remove zero-width characters and other invisible Unicode
        text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
        
        # Pass 12: Remove IP addresses and server info
        text = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '', text)  # IP addresses
        
        # Pass 13: Remove form field placeholders
        text = re.sub(r'(?:name|email|password|username|phone|address)\s*[:=]?\s*(?:\(.*?\))?', '', text, flags=re.IGNORECASE)
        
        # Pass 14: Remove common placeholder text
        text = re.sub(r'(?:enter|type|leave|input|required|optional|field)', '', text, flags=re.IGNORECASE)
        
        # Pass 15: Normalize multiple spaces and newlines
        text = ' '.join(text.split())
        
        # Pass 16: Remove trailing/leading punctuation and whitespace
        text = re.sub(r'^[^\w]+', '', text)  # Remove leading non-word chars
        text = re.sub(r'[^\w]+$', '', text)  # Remove trailing non-word chars
        
        # Pass 17: Clean up multiple spaces again
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def should_skip_text(self, text: str) -> bool:
        """
        Determine if cleaned text should be skipped
        Filters out spam, metadata, and low-quality content
        
        Args:
            text (str): Cleaned text to evaluate
            
        Returns:
            bool: True if should be skipped, False if valid content
        """
        if not text:
            return True
        
        # Too short - likely not meaningful
        if len(text) < 5:
            return True
        
        # Mostly numbers or special chars
        word_chars = sum(1 for c in text if c.isalnum() or c.isspace())
        if word_chars < 0.5 * len(text):
            return True
        
        # Too many uppercase (likely acronyms or headers)
        uppercase_chars = sum(1 for c in text if c.isupper())
        if uppercase_chars > 0.75 * len(text):
            return True
        
        words = text.split()
        
        # Too few words
        if len(words) < 2:
            return True
        
        # Empty words (unlikely)
        if len(words) > 100 and len(text) < 50:
            return True
        
        # Numbers only (prices, IDs, etc.)
        if re.match(r'^[\d\$\€\£\¥.,\s]+$', text):
            return True
        
        # Too many numbers (likely metadata or code)
        numbers = sum(1 for c in text if c.isdigit())
        if numbers > 0.4 * len(text):
            return True
        
        # Spam and noise patterns
        spam_patterns = [
            r'^(click|subscribe|follow|share|like|comment|rate|save|pin|tweet)\s*(here)?\s*$',
            r'^(loading|buffering|please wait)',
            r'^(error|warning|notice|alert)\s*:?',
            r'javascript:|onclick|onerror|onload',
            r'\.com$|\.org$|\.net$|\.io$|\.co$',
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',  # Email only
            r'^https?://',  # URL only
            r'^(author|by|published|posted|updated|modified)\s*:',
            r'^(ratings?|reviews?|stars?|comments?)\s*:?\s*\d',
            r'^(price|cost|fee)\s*:?\s*\$?\d',
            r'(admin|username|password|login|sign\s*up)',
            r'^(view|show|hide|display|expand|collapse)',
            r'(captcha|recaptcha|verification|security\s*code)',
        ]
        
        text_lower = text.lower()
        for pattern in spam_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def extract_elements(self, soup: BeautifulSoup, selector: str = None) -> List[str]:
        """
        Extract elements by CSS selector or tag name
        If selector is None, extracts all paragraphs and text content from the page
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            selector (str): CSS selector, tag name, or class selector (optional)
            
        Returns:
            List[str]: List of extracted text content
        """
        try:
            # If no selector provided, extract all content (paragraphs and text)
            if not selector or not selector.strip():
                return self.extract_all_content(soup)
            
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
            
            # Extract text from elements with advanced filtering
            for element in found_elements:
                text = element.get_text(strip=True)
                if text:  # Only add non-empty text
                    # Clean the text
                    cleaned_text = self.clean_text(text)
                    
                    # Skip if should be filtered out
                    if self.should_skip_text(cleaned_text):
                        logger.debug(f"Skipping filtered text: {cleaned_text[:50]}")
                        continue
                    
                    if cleaned_text:
                        elements.append(cleaned_text)
            
            logger.info(f"Extracted {len(elements)} non-empty elements (after filtering)")
            
            return elements
        
        except Exception as e:
            logger.error(f"Error extracting elements: {str(e)}")
            raise Exception(f"Failed to extract elements: {str(e)}")
    
    def is_noise_element(self, element) -> bool:
        """
        Check if an element is likely noise (footer, nav, ads, etc.)
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            bool: True if element is noise, False otherwise
        """
        try:
            # Check tag name
            if element.name in ['script', 'style', 'noscript', 'meta', 'link']:
                return True
            
            # Check for common noise classes and IDs
            noise_keywords = ['footer', 'nav', 'navbar', 'menu', 'sidebar', 'ads', 'advertisement', 
                            'cookie', 'consent', 'popup', 'modal', 'breadcrumb', 'pagination',
                            'copyright', 'social', 'widget', 'tracking', 'analytics', 'comments-form',
                            'related-posts', 'suggested-posts', 'trending', 'share-']
            
            element_class = element.get('class', [])
            element_id = element.get('id', '')
            
            # Flatten class list
            classes = ' '.join(element_class).lower() if element_class else ''
            element_id = element_id.lower()
            
            for keyword in noise_keywords:
                if keyword in classes or keyword in element_id:
                    return True
            
            # Check parent elements
            parent = element.parent
            while parent and parent.name:
                parent_class = ' '.join(parent.get('class', [])).lower()
                parent_id = parent.get('id', '').lower()
                
                for keyword in noise_keywords:
                    if keyword in parent_class or keyword in parent_id:
                        return True
                
                parent = parent.parent
            
            return False
        
        except Exception:
            return False
    
    def is_mostly_links(self, element) -> bool:
        """
        Check if element contains mostly links (likely navigation or footer)
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            bool: True if mostly links, False otherwise
        """
        try:
            links = element.find_all('a')
            text_length = len(element.get_text(strip=True))
            
            # If element is very small, skip
            if text_length < 10:
                return True
            
            # If more than 50% links, consider it navigation
            link_text_length = sum(len(link.get_text(strip=True)) for link in links)
            
            return link_text_length > (text_length * 0.5)
        
        except Exception:
            return False
    
    def is_content_text(self, text: str) -> bool:
        """
        Check if text looks like actual content (not menu items, metadata, etc.)
        
        Args:
            text (str): Text to check
            
        Returns:
            bool: True if looks like content, False if looks like noise
        """
        text_lower = text.lower().strip()
        
        # Navigation and UI elements
        nav_patterns = [
            r'^(home|about|contact|services|products|blog|news|faq|help|support)',
            r'^(gallery|portfolio|projects|team|staff|careers|jobs)',
            r'^(login|register|sign in|log in|my account|profile)',
        ]
        
        # Social and engagement
        social_patterns = [
            r'^(share|follow|subscribe|comment|reply|like|love|posted)',
            r'^(@|#)[a-z0-9_]+',  # Social handles and hashtags
        ]
        
        # Metadata and legal
        metadata_patterns = [
            r'^(copyright|all rights reserved|terms|privacy|cookies|disclaimer)',
            r'^(author|by|written by)\s*(:|,)?',
            r'^(published|posted|updated|modified)\s*(on)?',
            r'^\d{1,2}\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',  # Dates
        ]
        
        # CTA and promotional
        cta_patterns = [
            r'^(click here|read more|learn more|continue reading)',
            r'^(buy now|shop now|order now|get started)',
            r'^(promotional|ad|advertisement|sponsored)',
        ]
        
        # Form and technical
        form_patterns = [
            r'(name|email|phone|address)\s*[:=]',
            r'(username|password|captcha)',
            r'^(required|optional|field)',
            r'(javascript:|onclick|onerror)',
        ]
        
        # Combine all patterns
        all_patterns = nav_patterns + social_patterns + metadata_patterns + cta_patterns + form_patterns
        
        for pattern in all_patterns:
            if re.search(pattern, text_lower):
                return False
        
        return True
    
    def extract_all_content(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract all meaningful content from the page
        Filters out footers, navigation, links, and other noise
        Extracts paragraphs, headings, list items, and other text content
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            List[str]: List of cleaned, meaningful text content
        """
        try:
            logger.info("Extracting all page content with noise filtering")
            elements = []
            seen_text = set()  # Track seen content to avoid duplicates
            
            # Remove common noise elements first
            noise_tags = soup.find_all(['script', 'style', 'noscript', 'meta', 'link', 'footer', 'nav', 'aside'])
            for tag in noise_tags:
                tag.decompose()
            
            # Tags to extract content from (in priority order)
            content_tags = ['article', 'main', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                          'li', 'td', 'th', 'blockquote', 'pre', 'div', 'span']
            
            # Find all relevant content elements
            for tag in content_tags:
                found_elements = soup.find_all(tag, recursive=True)
                
                for element in found_elements:
                    # Skip if it's a noise element
                    if self.is_noise_element(element):
                        logger.debug(f"Skipping noise element: {element.name}")
                        continue
                    
                    # Skip if mostly links
                    if self.is_mostly_links(element):
                        logger.debug(f"Skipping link-heavy element: {element.name}")
                        continue
                    
                    text = element.get_text(strip=True)
                    
                    # Skip very short text or empty
                    if not text or len(text) < 5:
                        continue
                    
                    # Skip if doesn't look like real content
                    if not self.is_content_text(text):
                        logger.debug(f"Skipping non-content text: {text[:50]}")
                        continue
                    
                    # Clean the text
                    cleaned_text = self.clean_text(text)
                    
                    # Skip if text is too long (likely contains lots of stuff)
                    if len(cleaned_text) > 1000:
                        logger.debug(f"Skipping overly long text: {len(cleaned_text)} chars")
                        continue
                    
                    # Avoid duplicates
                    if cleaned_text and cleaned_text not in seen_text:
                        elements.append(cleaned_text)
                        seen_text.add(cleaned_text)
            
            logger.info(f"Extracted {len(elements)} items from page content (cleaned)")
            return elements
        
        except Exception as e:
            logger.error(f"Error extracting all content: {str(e)}")
            raise Exception(f"Failed to extract page content: {str(e)}")
    
    def extract_with_attributes(self, soup: BeautifulSoup, selector: str = None) -> List[Dict]:
        """
        Extract elements with their attributes
        If selector is None, extracts all content
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            selector (str): CSS selector (optional)
            
        Returns:
            List[Dict]: List of dictionaries containing text and attributes
        """
        try:
            # If no selector provided, extract all content
            if not selector or not selector.strip():
                all_content = self.extract_all_content(soup)
                # Convert to list of dicts
                return [{'text': item, 'tag': 'content', 'attributes': {}} for item in all_content]
            
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
    
    def scrape(self, url: str, selector: str = None, include_attributes: bool = False) -> Dict:
        """
        Complete scraping workflow
        If selector is None, extracts all page content
        
        Args:
            url (str): URL to scrape
            selector (str): CSS selector or tag name (optional)
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
                'selector': selector or 'all_content',
                'data': data,
                'count': len(data),
                'message': f'Successfully extracted {len(data)} items'
            }
        
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            return {
                'success': False,
                'url': url,
                'selector': selector or 'all_content',
                'data': [],
                'count': 0,
                'error': str(e)
            }
    
    def scrape_multiple_pages(self, 
                            start_url: str, 
                            selector: str = None,
                            pages: int = 1,
                            next_page_selector: Optional[str] = None) -> Dict:
        """
        Scrape multiple pages
        If selector is None, extracts all page content
        
        Args:
            start_url (str): Starting URL
            selector (str): CSS selector for data extraction (optional)
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
    
    def scrape_urls(self, 
                    urls: List[str], 
                    selector: Optional[str] = None, 
                    include_attributes: bool = False) -> Dict:
        """
        Scrape a list of specific URLs
        
        Args:
            urls (List[str]): List of URLs to scrape
            selector (str): CSS selector for data extraction
            include_attributes (bool): Whether to include element attributes
            
        Returns:
            Dict: Combined results from all URLs
        """
        all_data = []
        urls_scraped = 0
        
        try:
            for url in urls:
                logger.info(f"Scraping URL {urls_scraped + 1}/{len(urls)}: {url}")
                
                try:
                    # Fetch and parse
                    html_content = self.fetch_page(url)
                    soup = self.parse_html(html_content)
                    
                    if not soup:
                        logger.warning(f"Failed to parse HTML for {url}")
                        continue
                        
                    # Extract data
                    if include_attributes:
                        data = self.extract_with_attributes(soup, selector)
                    else:
                        data = self.extract_elements(soup, selector)
                        
                    all_data.extend(data)
                    urls_scraped += 1
                    
                    # Add delay between requests
                    if urls_scraped < len(urls):
                        logger.info(f"Waiting {self.scraping_delay} seconds before next request...")
                        time.sleep(self.scraping_delay)
                        
                except Exception as e:
                    logger.error(f"Failed to scrape {url}: {str(e)}")
                    continue
                    
            return {
                'success': True,
                'urls_scraped': urls_scraped,
                'total_urls': len(urls),
                'data': all_data,
                'count': len(all_data),
                'message': f'Successfully scraped {urls_scraped} pages with {len(all_data)} total items'
            }
            
        except Exception as e:
            logger.error(f"Multi-URL scraping failed: {str(e)}")
            return {
                'success': False,
                'urls_scraped': urls_scraped,
                'data': all_data,
                'count': len(all_data),
                'error': str(e)
            }

    def discover_links(self, url: str, max_links: int = 100, auto_pagination: bool = True) -> Dict:
        """
        Discover links on a webpage, optionally following pagination
        
        Args:
            url (str): URL to start discovery from
            max_links (int): Maximum number of links to return
            auto_pagination (bool): Whether to follow "Next" links to find more pages
            
        Returns:
            Dict: Discovered links
        """
        try:
            from urllib.parse import urljoin, urlparse
            from scraper.pagination_handler import PaginationHandler
            
            logger.info(f"Starting link discovery on: {url} (auto_pagination={auto_pagination})")
            
            links = []
            seen_urls = {url} # Skip the starting URL itself if it appears as a link
            pages_to_visit = [url]
            pages_processed = 0
            max_pages = 5 if auto_pagination else 1
            
            pagination_handler = PaginationHandler()
            
            # Extract base domain for filtering
            base_domain = urlparse(url).netloc
            
            while pages_to_visit and len(links) < max_links and pages_processed < max_pages:
                current_url = pages_to_visit.pop(0)
                pages_processed += 1
                
                logger.info(f"Processing discovery page {pages_processed}: {current_url}")
                
                try:
                    html_content = self.fetch_page(current_url)
                    if not html_content:
                        continue
                        
                    soup = self.parse_html(html_content)
                    if not soup:
                        continue
                    
                    # 1. Find all links on this page
                    for link_elem in soup.find_all('a', href=True):
                        href = link_elem.get('href', '').strip()
                        
                        if not href or href.startswith('#') or href.startswith('javascript:'):
                            continue
                        
                        # Convert relative URLs to absolute
                        absolute_url = urljoin(current_url, href)
                        
                        # Filter by domain (same-domain links only)
                        parsed_link = urlparse(absolute_url)
                        if parsed_link.netloc != base_domain:
                            continue
                            
                        # Normalize URL (remove fragments)
                        normalized_url = absolute_url.split('#')[0].rstrip('/')
                        
                        if normalized_url in seen_urls:
                            continue
                            
                        # Get link text
                        link_text = link_elem.get_text(strip=True)
                        if not link_text:
                            link_text = normalized_url.split('/')[-1] or 'Untitled Page'
                            
                        link_data = {
                            'url': normalized_url,
                            'text': link_text[:100],
                            'type': 'link'
                        }
                        
                        links.append(link_data)
                        seen_urls.add(normalized_url)
                        
                        if len(links) >= max_links:
                            break
                    
                    # 2. Find next page if auto_pagination is enabled
                    if auto_pagination and pages_processed < max_pages and len(links) < max_links:
                        next_page = pagination_handler.get_next_page_url(soup, current_url)
                        if next_page and next_page not in seen_urls:
                            # Add to front of queue to prioritize pagination over other links
                            pages_to_visit.insert(0, next_page)
                            # We don't add next_page to links list usually, it's just a source
                            seen_urls.add(next_page) 
                
                except Exception as e:
                    logger.error(f"Error during discovery on {current_url}: {str(e)}")
                    continue
                    
                # Small delay between discovery requests
                if pages_to_visit and pages_processed < max_pages:
                    time.sleep(self.scraping_delay)
            
            logger.info(f"Discovery finished. Found {len(links)} unique links across {pages_processed} pages.")
            
            return {
                'success': True,
                'base_url': url,
                'domain': base_domain,
                'links': links[:max_links],
                'count': len(links[:max_links]),
                'pages_processed': pages_processed
            }
            
        except Exception as e:
            logger.error(f"Link discovery failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
