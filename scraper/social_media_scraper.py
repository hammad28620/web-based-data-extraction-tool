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
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
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
    """Instagram profile and content scraper"""
    
    BASE_URL = "https://www.instagram.com"
    
    def scrape_profile(self, username: str) -> Dict:
        """
        Scrape Instagram user profile
        
        Args:
            username (str): Instagram username
            
        Returns:
            Dictionary with profile info
        """
        try:
            # Instagram API endpoint (public data only)
            url = f"{self.BASE_URL}/{username}/?__a=1&__d=dis"
            response = self._make_request(url)
            
            if not response:
                return {'success': False, 'error': 'Failed to fetch profile'}
            
            data = response.json()
            user = data.get('graphql', {}).get('user', {})
            
            profile = {
                'platform': 'instagram',
                'username': username,
                'follower_count': user.get('edge_followed_by', {}).get('total_count', 0),
                'following_count': user.get('edge_follow', {}).get('total_count', 0),
                'post_count': user.get('edge_owner_to_timeline_media', {}).get('total_count', 0),
                'bio': user.get('biography', ''),
                'full_name': user.get('full_name', ''),
                'website': user.get('external_url', ''),
                'email': user.get('public_email', ''),
                'profile_pic': user.get('profile_pic_url_hd', ''),
                'verified': user.get('is_verified', False),
                'private': user.get('is_private', False),
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            return {'success': True, 'data': profile}
            
        except Exception as e:
            logger.error(f"Instagram profile scrape error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def scrape_posts(self, username: str, limit: int = 10) -> Dict:
        """
        Scrape Instagram user posts
        
        Args:
            username (str): Instagram username
            limit (int): Maximum posts to scrape
            
        Returns:
            Dictionary with posts list
        """
        try:
            url = f"{self.BASE_URL}/{username}/?__a=1&__d=dis"
            response = self._make_request(url)
            
            if not response:
                return {'success': False, 'error': 'Failed to fetch posts'}
            
            data = response.json()
            edges = data.get('graphql', {}).get('user', {}).get(
                'edge_owner_to_timeline_media', {}
            ).get('edges', [])
            
            posts = []
            for edge in edges[:limit]:
                node = edge.get('node', {})
                post = {
                    'post_id': node.get('id'),
                    'caption': node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
                    'likes': node.get('edge_liked_by', {}).get('total_count', 0),
                    'comments': node.get('edge_media_to_comment', {}).get('total_count', 0),
                    'timestamp': node.get('taken_at_timestamp', ''),
                    'media_type': node.get('__typename', ''),
                    'image_url': node.get('display_url', ''),
                    'url': f"{self.BASE_URL}/p/{node.get('shortcode', '')}/",
                    'scraped_at': datetime.utcnow().isoformat()
                }
                posts.append(post)
            
            return {'success': True, 'data': posts, 'count': len(posts)}
            
        except Exception as e:
            logger.error(f"Instagram posts scrape error: {str(e)}")
            return {'success': False, 'error': str(e)}


class TwitterScraper(SocialMediaScraper):
    """Twitter/X profile and tweet scraper"""
    
    BASE_URL = "https://twitter.com"
    API_URL = "https://api.twitter.com/2"
    
    def __init__(self, bearer_token: Optional[str] = None, **kwargs):
        """Initialize Twitter scraper with optional bearer token"""
        super().__init__(**kwargs)
        self.bearer_token = bearer_token
        if bearer_token:
            self.headers['Authorization'] = f'Bearer {bearer_token}'
    
    def scrape_profile(self, username: str) -> Dict:
        """
        Scrape Twitter user profile (public data)
        
        Args:
            username (str): Twitter username (without @)
            
        Returns:
            Dictionary with profile info
        """
        try:
            # Try API first if bearer token available
            if self.bearer_token:
                return self._scrape_profile_api(username)
            
            # Fallback to scraping (limited data)
            url = f"{self.BASE_URL}/{username}"
            response = self._make_request(url)
            
            if not response:
                return {'success': False, 'error': 'Failed to fetch Twitter profile'}
            
            # Extract basic info from HTML
            profile = {
                'platform': 'twitter',
                'username': username,
                'url': url,
                'note': 'Limited data - requires API bearer token for full profile data',
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            return {'success': True, 'data': profile}
            
        except Exception as e:
            logger.error(f"Twitter profile scrape error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _scrape_profile_api(self, username: str) -> Dict:
        """Scrape Twitter profile using official API"""
        try:
            # Get user ID first
            url = f"{self.API_URL}/users/by/username/{username}"
            response = self._make_request(url, params={'user.fields': 'public_metrics,description,verified'})
            
            if not response:
                return {'success': False, 'error': 'Failed to fetch Twitter user'}
            
            data = response.json()
            if 'errors' in data:
                return {'success': False, 'error': data['errors'][0]['message']}
            
            user_data = data.get('data', {})
            profile = {
                'platform': 'twitter',
                'username': username,
                'name': user_data.get('name', ''),
                'description': user_data.get('description', ''),
                'verified': user_data.get('verified', False),
                'followers': user_data.get('public_metrics', {}).get('followers_count', 0),
                'following': user_data.get('public_metrics', {}).get('following_count', 0),
                'tweets': user_data.get('public_metrics', {}).get('tweet_count', 0),
                'url': f"{self.BASE_URL}/{username}",
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            return {'success': True, 'data': profile}
            
        except Exception as e:
            logger.error(f"Twitter API scrape error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def scrape_posts(self, username: str, limit: int = 10) -> Dict:
        """
        Scrape Twitter tweets (requires API bearer token)
        
        Args:
            username (str): Twitter username
            limit (int): Max tweets to scrape
            
        Returns:
            Dictionary with tweets list
        """
        if not self.bearer_token:
            return {
                'success': False,
                'error': 'Twitter API bearer token required for tweet scraping'
            }
        
        try:
            # Get user ID
            user_url = f"{self.API_URL}/users/by/username/{username}"
            response = self._make_request(user_url)
            
            if not response:
                return {'success': False, 'error': 'Failed to get user ID'}
            
            user_id = response.json().get('data', {}).get('id')
            if not user_id:
                return {'success': False, 'error': 'User not found'}
            
            # Get tweets
            tweets_url = f"{self.API_URL}/users/{user_id}/tweets"
            response = self._make_request(
                tweets_url,
                params={
                    'max_results': min(limit, 100),
                    'tweet.fields': 'public_metrics,created_at',
                    'expansions': 'author_id'
                }
            )
            
            if not response:
                return {'success': False, 'error': 'Failed to fetch tweets'}
            
            data = response.json()
            tweets = []
            for tweet in data.get('data', []):
                tweets.append({
                    'tweet_id': tweet.get('id'),
                    'text': tweet.get('text', ''),
                    'created_at': tweet.get('created_at', ''),
                    'likes': tweet.get('public_metrics', {}).get('like_count', 0),
                    'retweets': tweet.get('public_metrics', {}).get('retweet_count', 0),
                    'replies': tweet.get('public_metrics', {}).get('reply_count', 0),
                    'url': f"{self.BASE_URL}/{username}/status/{tweet.get('id')}",
                    'scraped_at': datetime.utcnow().isoformat()
                })
            
            return {'success': True, 'data': tweets, 'count': len(tweets)}
            
        except Exception as e:
            logger.error(f"Twitter tweets scrape error: {str(e)}")
            return {'success': False, 'error': str(e)}


class LinkedInScraper(SocialMediaScraper):
    """LinkedIn profile scraper (public profiles only)"""
    
    BASE_URL = "https://www.linkedin.com"
    
    def scrape_profile(self, username: str) -> Dict:
        """
        Scrape LinkedIn public profile
        
        Args:
            username (str): LinkedIn username or ID
            
        Returns:
            Dictionary with profile info
        """
        try:
            url = f"{self.BASE_URL}/in/{username}/"
            response = self._make_request(url)
            
            if not response:
                return {'success': False, 'error': 'Failed to access LinkedIn profile'}
            
            # LinkedIn heavily restricts scraping - requires authentication
            profile = {
                'platform': 'linkedin',
                'username': username,
                'url': url,
                'note': 'LinkedIn restricts automated scraping. Use official APIs or manual access.',
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            return {'success': True, 'data': profile}
            
        except Exception as e:
            logger.error(f"LinkedIn profile scrape error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def scrape_posts(self, username: str, limit: int = 10) -> Dict:
        """LinkedIn posts scraping (limited, requires authentication)"""
        return {
            'success': False,
            'error': 'LinkedIn post scraping requires official API or account authentication'
        }


class TikTokScraper(SocialMediaScraper):
    """TikTok profile and video scraper"""
    
    BASE_URL = "https://www.tiktok.com"
    
    def scrape_profile(self, username: str) -> Dict:
        """
        Scrape TikTok user profile
        
        Args:
            username (str): TikTok username (without @)
            
        Returns:
            Dictionary with profile info
        """
        try:
            url = f"{self.BASE_URL}/@{username}"
            response = self._make_request(url)
            
            if not response:
                return {'success': False, 'error': 'Failed to access TikTok profile'}
            
            # Basic profile info from public page
            profile = {
                'platform': 'tiktok',
                'username': username,
                'url': url,
                'note': 'TikTok profiles require dynamic rendering for full data',
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            return {'success': True, 'data': profile}
            
        except Exception as e:
            logger.error(f"TikTok profile scrape error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def scrape_posts(self, username: str, limit: int = 10) -> Dict:
        """
        Scrape TikTok videos (limited without dynamic rendering)
        
        Args:
            username (str): TikTok username
            limit (int): Max videos to scrape
            
        Returns:
            Dictionary with videos list
        """
        return {
            'success': False,
            'error': 'TikTok video scraping requires Selenium/Playwright for JavaScript rendering',
            'recommendation': 'Use dynamic_scraper.py with Playwright for TikTok content'
        }


class YouTubeScraper(SocialMediaScraper):
    """YouTube channel and video scraper"""
    
    BASE_URL = "https://www.youtube.com"
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize YouTube scraper with optional API key"""
        super().__init__(**kwargs)
        self.api_key = api_key
    
    def scrape_profile(self, channel_id: str) -> Dict:
        """
        Scrape YouTube channel information
        
        Args:
            channel_id (str): YouTube channel ID or username
            
        Returns:
            Dictionary with channel info
        """
        try:
            if self.api_key:
                return self._scrape_channel_api(channel_id)
            
            # Fallback URL-based scraping
            url = f"{self.BASE_URL}/{channel_id}"
            response = self._make_request(url)
            
            if not response:
                return {'success': False, 'error': 'Failed to access YouTube channel'}
            
            channel = {
                'platform': 'youtube',
                'channel_id': channel_id,
                'url': url,
                'note': 'Use YouTube Data API for full channel data',
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            return {'success': True, 'data': channel}
            
        except Exception as e:
            logger.error(f"YouTube channel scrape error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _scrape_channel_api(self, channel_id: str) -> Dict:
        """Scrape YouTube channel using API"""
        try:
            url = "https://www.googleapis.com/youtube/v3/channels"
            params = {
                'part': 'statistics,snippet',
                'forHandle': f"@{channel_id}",
                'key': self.api_key
            }
            response = self._make_request(url, params=params)
            
            if not response:
                return {'success': False, 'error': 'Failed to fetch YouTube channel'}
            
            data = response.json()
            if data.get('items'):
                item = data['items'][0]
                channel = {
                    'platform': 'youtube',
                    'channel_id': item['id'],
                    'title': item.get('snippet', {}).get('title', ''),
                    'description': item.get('snippet', {}).get('description', ''),
                    'subscribers': item.get('statistics', {}).get('subscriberCount', 'N/A'),
                    'videos': item.get('statistics', {}).get('videoCount', 0),
                    'views': item.get('statistics', {}).get('viewCount', 0),
                    'url': f"{self.BASE_URL}/channel/{item['id']}",
                    'scraped_at': datetime.utcnow().isoformat()
                }
                return {'success': True, 'data': channel}
            
            return {'success': False, 'error': 'Channel not found'}
            
        except Exception as e:
            logger.error(f"YouTube API scrape error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def scrape_posts(self, channel_id: str, limit: int = 10) -> Dict:
        """YouTube videos scraping (requires API key)"""
        if not self.api_key:
            return {
                'success': False,
                'error': 'YouTube API key required for video scraping'
            }
        
        return {'success': False, 'error': 'Video scraping not yet implemented'}


class SocialMediaScraperFactory:
    """Factory for creating appropriate social media scraper"""
    
    scrapers = {
        SocialMediaPlatform.INSTAGRAM: InstagramScraper,
        SocialMediaPlatform.TWITTER: TwitterScraper,
        SocialMediaPlatform.LINKEDIN: LinkedInScraper,
        SocialMediaPlatform.TIKTOK: TikTokScraper,
        SocialMediaPlatform.YOUTUBE: YouTubeScraper,
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
