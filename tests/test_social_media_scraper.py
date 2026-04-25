"""
Social Media Scraper Tests

Comprehensive tests for social media scraping functionality.
Tests all platforms and error handling scenarios.

Author: Data Extraction Tool Team
Version: 1.0.0
"""

import pytest
import logging
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
import json

from scraper.social_media_scraper import (
    SocialMediaPlatform,
    SocialMediaScraper,
    InstagramScraper,
    TwitterScraper,
    LinkedInScraper,
    TikTokScraper,
    YouTubeScraper,
    SocialMediaScraperFactory,
    scrape_social_media_profile,
    scrape_social_media_posts,
)

logger = logging.getLogger(__name__)


class TestSocialMediaPlatformEnum:
    """Tests for SocialMediaPlatform enum"""
    
    def test_platform_values(self):
        """Test platform enum values"""
        assert SocialMediaPlatform.INSTAGRAM.value == "instagram"
        assert SocialMediaPlatform.TWITTER.value == "twitter"
        assert SocialMediaPlatform.LINKEDIN.value == "linkedin"
        assert SocialMediaPlatform.TIKTOK.value == "tiktok"
        assert SocialMediaPlatform.YOUTUBE.value == "youtube"
    
    def test_platform_enum_count(self):
        """Test all platforms exist"""
        platforms = list(SocialMediaPlatform)
        assert len(platforms) >= 5


class TestInstagramScraper:
    """Tests for Instagram scraper"""
    
    @pytest.fixture
    def scraper(self):
        """Create Instagram scraper instance"""
        return InstagramScraper()
    
    def test_initializer(self, scraper):
        """Test scraper initialization"""
        assert scraper.request_timeout == 10
        assert scraper.rate_limit_delay == 1
        assert scraper.headers is not None
        assert 'User-Agent' in scraper.headers
    
    def test_base_url(self, scraper):
        """Test base URL is correct"""
        assert scraper.BASE_URL == "https://www.instagram.com"
    
    @patch('scraper.social_media_scraper.InstagramScraper._make_request')
    def test_scrape_profile_success(self, mock_request, scraper):
        """Test successful profile scraping"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'graphql': {
                'user': {
                    'edge_followed_by': {'total_count': 1000},
                    'edge_follow': {'total_count': 500},
                    'edge_owner_to_timeline_media': {'total_count': 100},
                    'biography': 'Sample bio',
                    'full_name': 'Test User',
                    'external_url': 'https://example.com',
                    'public_email': 'test@example.com',
                    'profile_pic_url_hd': 'https://example.com/pic.jpg',
                    'is_verified': True,
                    'is_private': False
                }
            }
        }
        mock_request.return_value = mock_response
        
        result = scraper.scrape_profile('testuser')
        
        assert result['success'] is True
        assert 'data' in result
        profile = result['data']
        assert profile['username'] == 'testuser'
        assert profile['follower_count'] == 1000
        assert profile['following_count'] == 500
        assert profile['post_count'] == 100
        assert profile['verified'] is True
        assert 'scraped_at' in profile
    
    @patch('scraper.social_media_scraper.InstagramScraper._make_request')
    def test_scrape_profile_failure(self, mock_request, scraper):
        """Test profile scraping failure"""
        mock_request.return_value = None
        
        result = scraper.scrape_profile('testuser')
        
        assert result['success'] is False
        assert 'error' in result
    
    @patch('scraper.social_media_scraper.InstagramScraper._make_request')
    def test_scrape_posts_success(self, mock_request, scraper):
        """Test successful posts scraping"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'graphql': {
                'user': {
                    'edge_owner_to_timeline_media': {
                        'edges': [
                            {
                                'node': {
                                    'id': '123',
                                    'edge_media_to_caption': {
                                        'edges': [{'node': {'text': 'Test post'}}]
                                    },
                                    'edge_liked_by': {'total_count': 100},
                                    'edge_media_to_comment': {'total_count': 50},
                                    'taken_at_timestamp': 1234567890,
                                    '__typename': 'GraphImage',
                                    'display_url': 'https://example.com/post.jpg',
                                    'shortcode': 'abc123'
                                }
                            }
                        ]
                    }
                }
            }
        }
        mock_request.return_value = mock_response
        
        result = scraper.scrape_posts('testuser', limit=10)
        
        assert result['success'] is True
        assert 'data' in result
        assert 'count' in result
        assert result['count'] == 1
        assert len(result['data']) == 1
        post = result['data'][0]
        assert post['post_id'] == '123'
        assert post['likes'] == 100
        assert post['comments'] == 50
    
    @patch('scraper.social_media_scraper.InstagramScraper._make_request')
    def test_scrape_posts_failure(self, mock_request, scraper):
        """Test posts scraping failure"""
        mock_request.return_value = None
        
        result = scraper.scrape_posts('testuser')
        
        assert result['success'] is False
        assert 'error' in result


class TestTwitterScraper:
    """Tests for Twitter scraper"""
    
    @pytest.fixture
    def scraper(self):
        """Create Twitter scraper instance"""
        return TwitterScraper()
    
    @pytest.fixture
    def scraper_with_token(self):
        """Create Twitter scraper with bearer token"""
        return TwitterScraper(bearer_token='test_token_12345')
    
    def test_initializer(self, scraper):
        """Test scraper initialization"""
        assert scraper.BASE_URL == "https://twitter.com"
        assert scraper.API_URL == "https://api.twitter.com/2"
        assert scraper.bearer_token is None
    
    def test_initializer_with_token(self, scraper_with_token):
        """Test scraper initialization with bearertoken"""
        assert scraper_with_token.bearer_token == 'test_token_12345'
        assert 'Authorization' in scraper_with_token.headers
    
    @patch('scraper.social_media_scraper.TwitterScraper._make_request')
    def test_scrape_profile_without_token(self, mock_request, scraper):
        """Test profile scraping without API token"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        result = scraper.scrape_profile('testuser')
        
        assert result['success'] is True
        assert 'data' in result
        profile = result['data']
        assert profile['platform'] == 'twitter'
        assert profile['username'] == 'testuser'
    
    @patch('scraper.social_media_scraper.TwitterScraper._make_request')
    def test_scrape_profile_with_token(self, mock_request, scraper_with_token):
        """Test profile scraping with API token"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': {
                'id': '123456',
                'name': 'Test User',
                'description': 'Test description',
                'verified': True,
                'public_metrics': {
                    'followers_count': 5000,
                    'following_count': 1000,
                    'tweet_count': 500
                }
            }
        }
        mock_request.return_value = mock_response
        
        result = scraper_with_token.scrape_profile('testuser')
        
        assert result['success'] is True
        profile = result['data']
        assert profile['followers'] == 5000
        assert profile['verified'] is True
        assert profile['tweets'] == 500
    
    @patch('scraper.social_media_scraper.TwitterScraper._make_request')
    def test_scrape_posts_without_token(self, mock_request, scraper):
        """Test posts scraping without token returns error"""
        result = scraper.scrape_posts('testuser')
        
        assert result['success'] is False
        assert 'bearer token required' in result['error'].lower()
    
    @patch('scraper.social_media_scraper.TwitterScraper._make_request')
    def test_scrape_posts_with_token(self, mock_request, scraper_with_token):
        """Test posts scraping with token"""
        # First call for user ID
        user_response = MagicMock()
        user_response.json.return_value = {'data': {'id': '123456'}}
        
        # Second call for tweets
        tweets_response = MagicMock()
        tweets_response.json.return_value = {
            'data': [
                {
                    'id': 'tweet_1',
                    'text': 'Test tweet 1',
                    'created_at': '2023-01-01T00:00:00.000Z',
                    'public_metrics': {
                        'like_count': 100,
                        'retweet_count': 50,
                        'reply_count': 10
                    }
                },
                {
                    'id': 'tweet_2',
                    'text': 'Test tweet 2',
                    'created_at': '2023-01-02T00:00:00.000Z',
                    'public_metrics': {
                        'like_count': 200,
                        'retweet_count': 75,
                        'reply_count': 20
                    }
                }
            ]
        }
        
        mock_request.side_effect = [user_response, tweets_response]
        
        result = scraper_with_token.scrape_posts('testuser', limit=10)
        
        assert result['success'] is True
        assert 'data' in result
        assert result['count'] == 2
        assert len(result['data']) == 2


class TestLinkedInScraper:
    """Tests for LinkedIn scraper"""
    
    @pytest.fixture
    def scraper(self):
        """Create LinkedIn scraper instance"""
        return LinkedInScraper()
    
    def test_initializer(self, scraper):
        """Test scraper initialization"""
        assert scraper.BASE_URL == "https://www.linkedin.com"
    
    @patch('scraper.social_media_scraper.LinkedInScraper._make_request')
    def test_scrape_profile(self, mock_request, scraper):
        """Test LinkedIn profile scraping"""
        mock_response = MagicMock()
        mock_request.return_value = mock_response
        
        result = scraper.scrape_profile('testuser')
        
        assert result['success'] is True
        assert 'data' in result
        assert result['data']['platform'] == 'linkedin'
        assert 'restricts' in result['data']['note'].lower()
    
    def test_scrape_posts_not_supported(self, scraper):
        """Test that LinkedIn posts scraping is not supported"""
        result = scraper.scrape_posts('testuser')
        
        assert result['success'] is False
        assert 'authentication' in result['error'].lower()


class TestTikTokScraper:
    """Tests for TikTok scraper"""
    
    @pytest.fixture
    def scraper(self):
        """Create TikTok scraper instance"""
        return TikTokScraper()
    
    def test_initializer(self, scraper):
        """Test scraper initialization"""
        assert scraper.BASE_URL == "https://www.tiktok.com"
    
    @patch('scraper.social_media_scraper.TikTokScraper._make_request')
    def test_scrape_profile(self, mock_request, scraper):
        """Test TikTok profile scraping"""
        mock_response = MagicMock()
        mock_request.return_value = mock_response
        
        result = scraper.scrape_profile('testuser')
        
        assert result['success'] is True
        assert 'data' in result
        assert 'rendering' in result['data']['note'].lower()
    
    def test_scrape_posts_requires_rendering(self, scraper):
        """Test that TikTok videos require dynamic rendering"""
        result = scraper.scrape_posts('testuser')
        
        assert result['success'] is False
        assert 'rendering' in result['error'].lower()


class TestYouTubeScraper:
    """Tests for YouTube scraper"""
    
    @pytest.fixture
    def scraper(self):
        """Create YouTube scraper instance"""
        return YouTubeScraper()
    
    @pytest.fixture
    def scraper_with_key(self):
        """Create YouTube scraper with API key"""
        return YouTubeScraper(api_key='test_api_key_12345')
    
    def test_initializer(self, scraper):
        """Test scraper initialization"""
        assert scraper.BASE_URL == "https://www.youtube.com"
        assert scraper.api_key is None
    
    def test_initializer_with_api_key(self, scraper_with_key):
        """Test scraper initialization with API key"""
        assert scraper_with_key.api_key == 'test_api_key_12345'
    
    @patch('scraper.social_media_scraper.YouTubeScraper._make_request')
    def test_scrape_profile_without_key(self, mock_request, scraper):
        """Test YouTube profile scraping without API key"""
        mock_response = MagicMock()
        mock_request.return_value = mock_response
        
        result = scraper.scrape_profile('UC12345')
        
        assert result['success'] is True
        assert 'data' in result
        assert result['data']['platform'] == 'youtube'


class TestSocialMediaScraperFactory:
    """Tests for SocialMediaScraperFactory"""
    
    def test_create_instagram_scraper(self):
        """Test creating Instagram scraper"""
        scraper = SocialMediaScraperFactory.create_scraper(
            SocialMediaPlatform.INSTAGRAM
        )
        assert isinstance(scraper, InstagramScraper)
    
    def test_create_twitter_scraper(self):
        """Test creating Twitter scraper"""
        scraper = SocialMediaScraperFactory.create_scraper(
            SocialMediaPlatform.TWITTER,
            bearer_token='test_token'
        )
        assert isinstance(scraper, TwitterScraper)
        assert scraper.bearer_token == 'test_token'
    
    def test_create_linkedin_scraper(self):
        """Test creating LinkedIn scraper"""
        scraper = SocialMediaScraperFactory.create_scraper(
            SocialMediaPlatform.LINKEDIN
        )
        assert isinstance(scraper, LinkedInScraper)
    
    def test_create_tiktok_scraper(self):
        """Test creating TikTok scraper"""
        scraper = SocialMediaScraperFactory.create_scraper(
            SocialMediaPlatform.TIKTOK
        )
        assert isinstance(scraper, TikTokScraper)
    
    def test_create_youtube_scraper(self):
        """Test creating YouTube scraper"""
        scraper = SocialMediaScraperFactory.create_scraper(
            SocialMediaPlatform.YOUTUBE,
            api_key='test_key'
        )
        assert isinstance(scraper, YouTubeScraper)
        assert scraper.api_key == 'test_key'
    
    def test_create_invalid_scraper(self):
        """Test creating scraper for invalid platform"""
        with pytest.raises(ValueError):
            SocialMediaScraperFactory.create_scraper('invalid_platform')
    
    def test_get_supported_platforms(self):
        """Test getting supported platforms list"""
        platforms = SocialMediaScraperFactory.get_supported_platforms()
        assert isinstance(platforms, list)
        assert 'instagram' in platforms
        assert 'twitter' in platforms
        assert 'linkedin' in platforms
        assert 'tiktok' in platforms
        assert 'youtube' in platforms


class TestSocialMediaScrapingFunctions:
    """Tests for high-level scraping functions"""
    
    @patch('scraper.social_media_scraper.SocialMediaScraperFactory.create_scraper')
    def test_scrape_social_media_profile_success(self, mock_create):
        """Test successful profile scraping function"""
        mock_scraper = MagicMock()
        mock_scraper.scrape_profile.return_value = {
            'success': True,
            'data': {'username': 'testuser'}
        }
        mock_create.return_value = mock_scraper
        
        result = scrape_social_media_profile('instagram', 'testuser')
        
        assert result['success'] is True
        assert result['data']['username'] == 'testuser'
    
    def test_scrape_social_media_profile_invalid_platform(self):
        """Test profile scraping with invalid platform"""
        result = scrape_social_media_profile('invalid', 'testuser')
        
        assert result['success'] is False
        assert 'error' in result
        assert 'supported_platforms' in result
    
    @patch('scraper.social_media_scraper.SocialMediaScraperFactory.create_scraper')
    def test_scrape_social_media_posts_success(self, mock_create):
        """Test successful posts scraping function"""
        mock_scraper = MagicMock()
        mock_scraper.scrape_posts.return_value = {
            'success': True,
            'count': 5,
            'data': []
        }
        mock_create.return_value = mock_scraper
        
        result = scrape_social_media_posts('twitter', 'testuser', limit=10)
        
        assert result['success'] is True
        assert result['count'] == 5
    
    def test_scrape_social_media_posts_invalid_platform(self):
        """Test posts scraping with invalid platform"""
        result = scrape_social_media_posts('invalid', 'testuser')
        
        assert result['success'] is False
        assert 'error' in result


class TestRateLimiting:
    """Tests for rate limiting functionality"""
    
    @pytest.fixture
    def scraper(self):
        """Create a scraper instance"""
        return TwitterScraper(rate_limit_delay=0.1)
    
    def test_rate_limit_delay(self, scraper):
        """Test that rate limiting adds delay"""
        import time
        start = time.time()
        scraper._rate_limit()
        elapsed = time.time() - start
        assert elapsed >= scraper.rate_limit_delay


class TestErrorHandling:
    """Tests for error handling"""
    
    @pytest.fixture
    def scraper(self):
        """Create Instagram scraper for testing"""
        return InstagramScraper()
    
    @patch('scraper.social_media_scraper.InstagramScraper._make_request')
    def test_network_error_handling(self, mock_request, scraper):
        """Test handling of network errors"""
        mock_request.return_value = None
        
        result = scraper.scrape_profile('testuser')
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_exception_handling(self, scraper):
        """Test exception handling during scraping"""
        # This will raise an exception because JSON parsing will fail
        with patch.object(scraper, '_make_request') as mock:
            mock_response = MagicMock()
            mock_response.json.side_effect = ValueError("JSON decode error")
            mock.return_value = mock_response
            
            result = scraper.scrape_profile('testuser')
            
            assert result['success'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
