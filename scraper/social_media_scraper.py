"""
Social Media Scraping Module
Scrapes content from Instagram, Twitter, LinkedIn, TikTok, and other platforms
"""

import logging
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from enum import Enum
from urllib.parse import urljoin, urlparse
from abc import ABC, abstractmethod
import time

logger = logging.getLogger(__name__)


class SocialMediaPlatform(Enum):
    """Supported social media platforms"""
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"


class SocialMediaScraper(ABC):
    """Base class for social media scrapers"""
    
    def __init__(self, request_timeout=10, rate_limit_delay=1):
        """
        Initialize social media scraper
        
        Args:
            request_timeout (int): Timeout for HTTP requests
            rate_limit_delay (float): Delay between requests in seconds
        """
        self.request_timeout = request_timeout
        self.rate_limit_delay = rate_limit_delay
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    @abstractmethod
    def scrape_profile(self, username: str) -> Dict:
        """Scrape user profile information"""
        pass
    
    @abstractmethod
    def scrape_posts(self, username: str, limit: int = 10) -> List[Dict]:
        """Scrape user posts/content"""
        pass
    
    def _rate_limit(self):
        """Apply rate limiting delay"""
        time.sleep(self.rate_limit_delay)
    
    def _make_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Make HTTP request with error handling
        
        Args:
            url (str): URL to request
            **kwargs: Additional arguments for requests.get()
            
        Returns:
            Response object or None if failed
        """
        try:
            self._rate_limit()
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.request_timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return None


class InstagramScraper(SocialMediaScraper):
    """Instagram profile and content scraper using metadata"""
    
    BASE_URL = "https://www.instagram.com"
    
    def scrape_profile(self, username: str) -> Dict:
        """
        Scrape Instagram user profile using OG metadata
        """
        try:
            url = f"{self.BASE_URL}/{username}/"
            # Use a generic bot User-Agent to get cleaner metadata
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            response = requests.get(url, headers=headers, timeout=self.request_timeout)
            
            if response.status_code != 200:
                return {'success': False, 'error': f'Failed to fetch profile (Status: {response.status_code})'}
            
            html = response.text
            import re
            
            # Extract info from og:description
            # Example: "105M Followers, 95 Following, 4,764 Posts - See Instagram photos and videos from NASA (@nasa)"
            desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', html)
            if not desc_match:
                return {'success': False, 'error': 'Could not find profile metadata'}
            
            desc = desc_match.group(1)
            
            # Simple parsing of the description string
            follower_count = 0
            following_count = 0
            post_count = 0
            
            parts = desc.split(',')
            if len(parts) >= 3:
                follower_count = parts[0].strip().split(' ')[0]
                following_count = parts[1].strip().split(' ')[0]
                post_count = parts[2].strip().split(' ')[0]
            
            # Extract profile pic
            pic_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
            profile_pic = pic_match.group(1) if pic_match else ''
            
            # Extract name
            title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            full_name = title_match.group(1).split(' (')[0] if title_match else username

            profile = {
                'platform': 'instagram',
                'username': username,
                'follower_count': follower_count,
                'following_count': following_count,
                'post_count': post_count,
                'full_name': full_name,
                'profile_pic': profile_pic,
                'url': url,
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            return {'success': True, 'data': profile}
            
        except Exception as e:
            logger.error(f"Instagram profile scrape error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def scrape_posts(self, username: str, limit: int = 10) -> Dict:
        """
        Instagram post scraping is highly restricted without API/Login.
        Returning a helpful error message.
        """
        return {
            'success': False, 
            'error': 'Instagram post scraping requires authentication or a specialized API due to recent changes.',
            'recommendation': 'Public metadata only provides profile overview.'
        }


class YouTubeScraper(SocialMediaScraper):
    """YouTube channel scraper using ytInitialData"""
    
    BASE_URL = "https://www.youtube.com"
    
    def scrape_profile(self, channel_handle: str) -> Dict:
        """
        Scrape YouTube channel info without API key
        """
        try:
            # Normalize handle
            if not channel_handle.startswith('@'):
                channel_handle = f"@{channel_handle}"
                
            url = f"{self.BASE_URL}/{channel_handle}/about"
            headers = {'Accept-Language': 'en-US,en;q=0.9'}
            response = requests.get(url, headers=headers, timeout=self.request_timeout)
            
            if response.status_code != 200:
                return {'success': False, 'error': f'Failed to fetch channel (Status: {response.status_code})'}
            
            html = response.text
            import json
            
            # Find ytInitialData JSON
            start_str = 'var ytInitialData ='
            start_idx = html.find(start_str)
            if start_idx == -1:
                return {'success': False, 'error': 'Could not find channel data'}
                
            start_idx += len(start_str)
            end_idx = html.find(';</script>', start_idx)
            data_str = html[start_idx:end_idx].strip()
            data = json.loads(data_str)
            
            # Extract channel info
            header = data.get('header', {}).get('pageHeaderRenderer', {}).get('content', {}).get('pageHeaderViewModel', {})
            metadata = data.get('metadata', {}).get('channelMetadataRenderer', {})
            
            # Get stats from metadata rows
            rows = header.get('metadata', {}).get('contentMetadataViewModel', {}).get('metadataRows', [])
            subscribers = "0"
            videos_count = "0"
            
            if len(rows) > 1:
                parts = rows[1].get('metadataParts', [])
                if len(parts) > 0:
                    subscribers = parts[0].get('text', {}).get('content', '0').split(' ')[0]
                if len(parts) > 1:
                    videos_count = parts[1].get('text', {}).get('content', '0').split(' ')[0]
            
            profile = {
                'platform': 'youtube',
                'username': channel_handle,
                'title': metadata.get('title', ''),
                'description': metadata.get('description', ''),
                'subscribers': subscribers,
                'video_count': videos_count,
                'profile_pic': header.get('image', {}).get('decoratedAvatarViewModel', {}).get('avatar', {}).get('avatarViewModel', {}).get('image', {}).get('sources', [{}])[0].get('url', ''),
                'url': f"{self.BASE_URL}/{channel_handle}",
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            return {'success': True, 'data': profile}
            
        except Exception as e:
            logger.error(f"YouTube profile scrape error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def scrape_posts(self, channel_handle: str, limit: int = 10) -> Dict:
        """
        Scrape latest YouTube videos from a channel
        """
        try:
            if not channel_handle.startswith('@'):
                channel_handle = f"@{channel_handle}"
                
            url = f"{self.BASE_URL}/{channel_handle}/videos"
            headers = {'Accept-Language': 'en-US,en;q=0.9'}
            response = requests.get(url, headers=headers, timeout=self.request_timeout)
            
            if response.status_code != 200:
                return {'success': False, 'error': 'Failed to fetch videos'}
                
            html = response.text
            import json
            
            start_str = 'var ytInitialData ='
            start_idx = html.find(start_str)
            if start_idx == -1:
                return {'success': False, 'error': 'Could not find video data'}
                
            start_idx += len(start_str)
            end_idx = html.find(';</script>', start_idx)
            data_str = html[start_idx:end_idx].strip()
            data = json.loads(data_str)
            
            # Navigate to video list
            tabs = data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])
            videos_tab = next((t for t in tabs if t.get('tabRenderer', {}).get('title') == 'Videos'), None)
            
            if not videos_tab:
                return {'success': False, 'error': 'Videos tab not found'}
                
            items = videos_tab['tabRenderer']['content']['richGridRenderer']['contents']
            
            posts = []
            for item in items[:limit]:
                video = item.get('richItemRenderer', {}).get('content', {}).get('videoRenderer')
                if not video:
                    continue
                    
                posts.append({
                    'post_id': video.get('videoId'),
                    'title': video.get('title', {}).get('runs', [{}])[0].get('text', ''),
                    'views': video.get('viewCountText', {}).get('simpleText', '0 views'),
                    'published': video.get('publishedTimeText', {}).get('simpleText', ''),
                    'thumbnail': video.get('thumbnail', {}).get('thumbnails', [{}])[-1].get('url', ''),
                    'url': f"https://www.youtube.com/watch?v={video.get('videoId')}",
                    'scraped_at': datetime.utcnow().isoformat()
                })
                
            return {'success': True, 'data': posts, 'count': len(posts)}
            
        except Exception as e:
            logger.error(f"YouTube videos scrape error: {str(e)}")
            return {'success': False, 'error': str(e)}


class FacebookScraper(SocialMediaScraper):
    """Facebook page scraper using OG metadata"""
    
    BASE_URL = "https://www.facebook.com"
    
    def scrape_profile(self, page_name: str) -> Dict:
        """
        Scrape Facebook page info using metadata
        """
        try:
            url = f"{self.BASE_URL}/{page_name}"
            headers = {'Accept-Language': 'en-US,en;q=0.9'}
            response = requests.get(url, headers=headers, timeout=self.request_timeout)
            
            if response.status_code != 200:
                return {'success': False, 'error': f'Failed to fetch Facebook page (Status: {response.status_code})'}
            
            html = response.text
            import re
            
            # Extract info from og:description
            # Example: "NASA. 28,652,229 likes · 229,341 talking about this."
            desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', html)
            if not desc_match:
                return {'success': False, 'error': 'Could not find page metadata'}
            
            desc = desc_match.group(1)
            
            # Extract likes (simple regex for numbers before 'likes')
            likes = re.search(r'([\d,]+)\s+likes', desc)
            likes_count = likes.group(1) if likes else "0"
            
            # Extract followers if present
            followers = re.search(r'([\d,]+)\s+followers', desc)
            followers_count = followers.group(1) if followers else likes_count # Often same on FB
            
            # Extract name and image
            title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            title = title_match.group(1) if title_match else page_name
            
            pic_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
            profile_pic = pic_match.group(1) if pic_match else ''
            
            profile = {
                'platform': 'facebook',
                'username': page_name,
                'title': title,
                'likes': likes_count,
                'followers': followers_count,
                'profile_pic': profile_pic,
                'url': url,
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            return {'success': True, 'data': profile}
            
        except Exception as e:
            logger.error(f"Facebook profile scrape error: {str(e)}")
            return {'success': False, 'error': str(e)}

    def scrape_posts(self, page_name: str, limit: int = 10) -> Dict:
        return {'success': False, 'error': 'Facebook posts require authentication to scrape.'}


class SocialMediaScraperFactory:
    """Factory for creating appropriate social media scraper"""
    
    scrapers = {
        SocialMediaPlatform.INSTAGRAM: InstagramScraper,
        SocialMediaPlatform.YOUTUBE: YouTubeScraper,
        SocialMediaPlatform.FACEBOOK: FacebookScraper,
    }
    
    @classmethod
    def create_scraper(
        cls,
        platform: SocialMediaPlatform,
        **credentials
    ) -> SocialMediaScraper:
        """
        Create scraper for specified platform
        
        Args:
            platform: Platform to scrape
            **credentials: API keys, bearer tokens, etc.
            
        Returns:
            Appropriate scraper instance
        """
        scraper_class = cls.scrapers.get(platform)
        if not scraper_class:
            raise ValueError(f"Unsupported platform: {platform}")
        
        return scraper_class(**credentials)
    
    @classmethod
    def get_supported_platforms(cls) -> List[str]:
        """Get list of supported platforms"""
        return [p.value for p in SocialMediaPlatform]


def scrape_social_media_profile(
    platform: str,
    username: str,
    **credentials
) -> Dict:
    """
    High-level function to scrape social media profile
    
    Args:
        platform (str): Social media platform name
        username (str): Username to scrape
        **credentials: API keys, tokens, etc.
        
    Returns:
        Dictionary with scraped profile data
    """
    try:
        platform_enum = SocialMediaPlatform(platform.lower())
        scraper = SocialMediaScraperFactory.create_scraper(platform_enum, **credentials)
        return scraper.scrape_profile(username)
    except ValueError as e:
        return {
            'success': False,
            'error': str(e),
            'supported_platforms': SocialMediaScraperFactory.get_supported_platforms()
        }
    except Exception as e:
        logger.error(f"Social media scraping error: {str(e)}")
        return {'success': False, 'error': str(e)}


def scrape_social_media_posts(
    platform: str,
    username: str,
    limit: int = 10,
    **credentials
) -> Dict:
    """
    High-level function to scrape social media posts
    
    Args:
        platform (str): Social media platform name
        username (str): Username to scrape
        limit (int): Maximum posts to scrape
        **credentials: API keys, tokens, etc.
        
    Returns:
        Dictionary with scraped posts data
    """
    try:
        platform_enum = SocialMediaPlatform(platform.lower())
        scraper = SocialMediaScraperFactory.create_scraper(platform_enum, **credentials)
        return scraper.scrape_posts(username, limit)
    except ValueError as e:
        return {
            'success': False,
            'error': str(e),
            'supported_platforms': SocialMediaScraperFactory.get_supported_platforms()
        }
    except Exception as e:
        logger.error(f"Social media posts scraping error: {str(e)}")
        return {'success': False, 'error': str(e)}
