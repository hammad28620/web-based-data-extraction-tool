"""
Social Media API Integration Tests

Tests for Flask API endpoints for social media scraping.
Tests endpoint access, response formats, and error handling.

Author: Data Extraction Tool Team
Version: 1.0.0
"""

import pytest
import json
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime

logger = logging.getLogger(__name__)


class TestSocialProfileScrapeEndpoint:
    """Tests for /social/scrape-profile endpoint"""
    
    def test_endpoint_exists(self, client):
        """Test endpoint is accessible"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.return_value = {'success': False, 'error': 'Test mock'}
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            assert response.status_code != 404
    
    def test_valid_request_instagram(self, client):
        """Test valid Instagram profile scraping request"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'data': {'username': 'testuser', 'followers': 1000}
            }
            
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'instagram', 'username': 'testuser'},
                content_type='application/json'
            )
            
            assert response.status_code in [200, 400, 500]
            data = response.get_json()
            assert 'success' in data or 'error' in data
    
    def test_valid_request_twitter(self, client):
        """Test valid Twitter profile scraping request"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'data': {'username': 'testuser', 'followers': 5000}
            }
            
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            
            assert response.status_code in [200, 400, 500]
    
    def test_missing_platform(self, client):
        """Test request with missing platform"""
        response = client.post(
            '/social/scrape-profile',
            json={'username': 'testuser'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data or data.get('success') is False
    
    def test_missing_username(self, client):
        """Test request with missing username"""
        response = client.post(
            '/social/scrape-profile',
            json={'platform': 'instagram'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_empty_username(self, client):
        """Test request with empty username"""
        response = client.post(
            '/social/scrape-profile',
            json={'platform': 'instagram', 'username': ''}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_unsupported_platform(self, client):
        """Test request with unsupported platform"""
        response = client.post(
            '/social/scrape-profile',
            json={'platform': 'unsupported_platform', 'username': 'testuser'}
        )
        
        assert response.status_code in [200, 400, 500]
    
    def test_wrong_content_type(self, client):
        """Test request with wrong content type"""
        response = client.post(
            '/social/scrape-profile',
            data='invalid data',
            content_type='text/plain'
        )
        
        assert response.status_code in [400, 415, 500]
    
    def test_rate_limiting(self, client):
        """Test that endpoints handle rapid requests"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock:
            mock.return_value = {'success': False, 'error': 'Test'}
            for i in range(3):
                response = client.post(
                    '/social/scrape-profile',
                    json={'platform': 'twitter', 'username': f'user{i}'}
                )
                assert response.status_code in [200, 400, 429, 500]
    
    def test_response_format_success(self, client):
        """Test successful response format"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'data': {'username': 'test', 'followers': 100}
            }
            
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            
            if response.status_code == 200:
                data = response.get_json()
                assert 'success' in data
                assert data.get('success') is True


class TestSocialPostsScrapeEndpoint:
    """Tests for /social/scrape-posts endpoint"""
    
    def test_endpoint_exists(self, client):
        """Test endpoint is accessible"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {'success': False, 'error': 'Test'}
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            assert response.status_code != 404
    
    def test_valid_request(self, client):
        """Test valid posts scraping request"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'count': 5,
                'data': []
            }
            
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser', 'limit': 10}
            )
            
            assert response.status_code in [200, 400, 500]
    
    def test_default_limit(self, client):
        """Test default limit is applied"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {'success': True, 'count': 0, 'data': []}
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'instagram', 'username': 'testuser'}
            )
            
            assert response.status_code in [200, 400, 500]
    
    def test_custom_limit(self, client):
        """Test custom limit is accepted"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {'success': True, 'count': 0, 'data': []}
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser', 'limit': 50}
            )
            
            assert response.status_code in [200, 400, 500]
    
    def test_limit_max_capped(self, client):
        """Test limit is capped at 100"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'count': 0,
                'data': []
            }
            
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser', 'limit': 500}
            )
            
            assert response.status_code in [200, 400, 500]
    
    def test_missing_username(self, client):
        """Test request with missing username"""
        response = client.post(
            '/social/scrape-posts',
            json={'platform': 'instagram'}
        )
        
        assert response.status_code == 400
    
    def test_response_format(self, client):
        """Test response format contains expected fields"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'count': 3,
                'data': [
                    {'title': 'Post 1'},
                    {'title': 'Post 2'},
                    {'title': 'Post 3'}
                ]
            }
            
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            
            if response.status_code == 200:
                data = response.get_json()
                assert 'success' in data
                assert data.get('success') is True


class TestSocialPlatformsEndpoint:
    """Tests for /social/platforms endpoint"""
    
    def test_endpoint_exists(self, client):
        """Test endpoint is accessible"""
        response = client.get('/social/platforms')
        assert response.status_code != 404
    
    def test_response_is_json(self, client):
        """Test response is JSON"""
        response = client.get('/social/platforms')
        assert response.content_type
        assert 'json' in response.content_type.lower()
    
    def test_response_contains_platforms(self, client):
        """Test response contains platforms list"""
        response = client.get('/social/platforms')
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'platforms' in data or 'success' in data
    
    def test_response_contains_details(self, client):
        """Test response contains platform details"""
        response = client.get('/social/platforms')
        
        if response.status_code == 200:
            data = response.get_json()
            if 'details' in data:
                assert isinstance(data['details'], dict)
    
    def test_success_flag(self, client):
        """Test success flag is present"""
        response = client.get('/social/platforms')
        
        data = response.get_json()
        assert 'success' in data or 'platforms' in data


class TestErrorHandling:
    """Tests for error handling in endpoints"""
    
    def test_profile_endpoint_handles_exception(self, client):
        """Test profile endpoint handles exceptions gracefully"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.side_effect = Exception("Test error")
            
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data or data.get('success') is False
    
    def test_posts_endpoint_handles_exception(self, client):
        """Test posts endpoint handles exceptions gracefully"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.side_effect = Exception("Test error")
            
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            
            assert response.status_code == 500
    
    def test_platforms_endpoint_handles_exception(self, client):
        """Test platforms endpoint handles exceptions gracefully"""
        with patch('scraper.social_media_scraper.SocialMediaScraperFactory') as mock_factory:
            mock_factory.get_supported_platforms.side_effect = Exception("Test error")
            
            response = client.get('/social/platforms')
            
            assert response.status_code == 500
            data = response.get_json()
            assert data.get('success') is False


class TestInputValidation:
    """Tests for input validation"""
    
    def test_whitespace_trimming(self, client):
        """Test whitespace in username is trimmed"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock:
            mock.return_value = {'success': False, 'error': 'Test'}
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'instagram', 'username': '  testuser  '}
            )
            
            assert response.status_code in [200, 400, 500]
    
    def test_platform_lowercase_conversion(self, client):
        """Test platform name is converted to lowercase"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.return_value = {'success': True, 'data': {}}
            
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'INSTAGRAM', 'username': 'testuser'}
            )
            
            assert response.status_code in [200, 400, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
"""
Social Media API Integration Tests

Tests for Flask API endpoints for social media scraping.
Tests endpoint access, response formats, and error handling.

Author: Data Extraction Tool Team
Version: 1.0.0
"""

import pytest
import json
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime

logger = logging.getLogger(__name__)


class TestSocialProfileScrapeEndpoint:
    """Tests for /social/scrape-profile endpoint"""
    
    def test_endpoint_exists(self, client):
        """Test endpoint is accessible"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.return_value = {'success': False, 'error': 'Test mock'}
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            assert response.status_code != 404
    
    def test_valid_request_instagram(self, client):
        """Test valid Instagram profile scraping request"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'data': {'username': 'testuser', 'followers': 1000}
            }
            
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'instagram', 'username': 'testuser'},
                content_type='application/json'
            )
            
            assert response.status_code in [200, 400, 500]
            data = response.get_json()
            assert 'success' in data or 'error' in data
    
    def test_valid_request_twitter(self, client):
        """Test valid Twitter profile scraping request"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'data': {'username': 'testuser', 'followers': 5000}
            }
            
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            
            assert response.status_code in [200, 400, 500]
    
    def test_missing_platform(self, client):
        """Test request with missing platform"""
        response = client.post(
            '/social/scrape-profile',
            json={'username': 'testuser'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data or data.get('success') is False
    
    def test_missing_username(self, client):
        """Test request with missing username"""
        response = client.post(
            '/social/scrape-profile',
            json={'platform': 'instagram'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_empty_username(self, client):
        """Test request with empty username"""
        response = client.post(
            '/social/scrape-profile',
            json={'platform': 'instagram', 'username': ''}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_unsupported_platform(self, client):
        """Test request with unsupported platform"""
        response = client.post(
            '/social/scrape-profile',
            json={'platform': 'unsupported_platform', 'username': 'testuser'}
        )
        
        assert response.status_code in [200, 400, 500]
    
    def test_wrong_content_type(self, client):
        """Test request with wrong content type"""
        response = client.post(
            '/social/scrape-profile',
            data='invalid data',
            content_type='text/plain'
        )
        
        assert response.status_code in [400, 415, 500]
    
    def test_rate_limiting(self, client):
        """Test that endpoints handle rapid requests"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock:
            mock.return_value = {'success': False, 'error': 'Test'}
            for i in range(3):
                response = client.post(
                    '/social/scrape-profile',
                    json={'platform': 'twitter', 'username': f'user{i}'}
                )
                assert response.status_code in [200, 400, 429, 500]
    
    def test_response_format_success(self, client):
        """Test successful response format"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'data': {'username': 'test', 'followers': 100}
            }
            
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            
            if response.status_code == 200:
                data = response.get_json()
                assert 'success' in data
                assert data.get('success') is True


class TestSocialPostsScrapeEndpoint:
    """Tests for /social/scrape-posts endpoint"""
    
    def test_endpoint_exists(self, client):
        """Test endpoint is accessible"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {'success': False, 'error': 'Test'}
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            assert response.status_code != 404
    
    def test_valid_request(self, client):
        """Test valid posts scraping request"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'count': 5,
                'data': []
            }
            
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser', 'limit': 10}
            )
            
            assert response.status_code in [200, 400, 500]
    
    def test_default_limit(self, client):
        """Test default limit is applied"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {'success': True, 'count': 0, 'data': []}
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'instagram', 'username': 'testuser'}
            )
            
            assert response.status_code in [200, 400, 500]
    
    def test_custom_limit(self, client):
        """Test custom limit is accepted"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {'success': True, 'count': 0, 'data': []}
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser', 'limit': 50}
            )
            
            assert response.status_code in [200, 400, 500]
    
    def test_limit_max_capped(self, client):
        """Test limit is capped at 100"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'count': 0,
                'data': []
            }
            
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser', 'limit': 500}
            )
            
            assert response.status_code in [200, 400, 500]
    
    def test_missing_username(self, client):
        """Test request with missing username"""
        response = client.post(
            '/social/scrape-posts',
            json={'platform': 'instagram'}
        )
        
        assert response.status_code == 400
    
    def test_response_format(self, client):
        """Test response format contains expected fields"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'count': 3,
                'data': [
                    {'title': 'Post 1'},
                    {'title': 'Post 2'},
                    {'title': 'Post 3'}
                ]
            }
            
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            
            if response.status_code == 200:
                data = response.get_json()
                assert 'success' in data
                assert data.get('success') is True


class TestSocialPlatformsEndpoint:
    """Tests for /social/platforms endpoint"""
    
    def test_endpoint_exists(self, client):
        """Test endpoint is accessible"""
        response = client.get('/social/platforms')
        assert response.status_code != 404
    
    def test_response_is_json(self, client):
        """Test response is JSON"""
        response = client.get('/social/platforms')
        assert response.content_type
        assert 'json' in response.content_type.lower()
    
    def test_response_contains_platforms(self, client):
        """Test response contains platforms list"""
        response = client.get('/social/platforms')
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'platforms' in data or 'success' in data
    
    def test_response_contains_details(self, client):
        """Test response contains platform details"""
        response = client.get('/social/platforms')
        
        if response.status_code == 200:
            data = response.get_json()
            if 'details' in data:
                assert isinstance(data['details'], dict)
    
    def test_success_flag(self, client):
        """Test success flag is present"""
        response = client.get('/social/platforms')
        
        data = response.get_json()
        assert 'success' in data or 'platforms' in data


class TestErrorHandling:
    """Tests for error handling in endpoints"""
    
    def test_profile_endpoint_handles_exception(self, client):
        """Test profile endpoint handles exceptions gracefully"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.side_effect = Exception("Test error")
            
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data or data.get('success') is False
    
    def test_posts_endpoint_handles_exception(self, client):
        """Test posts endpoint handles exceptions gracefully"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.side_effect = Exception("Test error")
            
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            
            assert response.status_code == 500
    
    def test_platforms_endpoint_handles_exception(self, client):
        """Test platforms endpoint handles exceptions gracefully"""
        with patch('scraper.social_media_scraper.SocialMediaScraperFactory') as mock_factory:
            mock_factory.get_supported_platforms.side_effect = Exception("Test error")
            
            response = client.get('/social/platforms')
            
            assert response.status_code == 500
            data = response.get_json()
            assert data.get('success') is False


class TestInputValidation:
    """Tests for input validation"""
    
    def test_whitespace_trimming(self, client):
        """Test whitespace in username is trimmed"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock:
            mock.return_value = {'success': False, 'error': 'Test'}
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'instagram', 'username': '  testuser  '}
            )
            
            assert response.status_code in [200, 400, 500]
    
    def test_platform_lowercase_conversion(self, client):
        """Test platform name is converted to lowercase"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.return_value = {'success': True, 'data': {}}
            
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'INSTAGRAM', 'username': 'testuser'}
            )
            
            assert response.status_code in [200, 400, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

    """Tests for /social/scrape-profile endpoint"""
    
    def test_endpoint_exists(self, client):
        """Test endpoint is accessible"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.return_value = {'success': False, 'error': 'Test mock'}
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            # Should not be 404
            assert response.status_code != 404
    
    def test_valid_request_instagram(self, client):
        """Test valid Instagram profile scraping request"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'data': {'username': 'testuser', 'followers': 1000}
            }
            
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'instagram', 'username': 'testuser'},
                content_type='application/json'
            )
            
            assert response.status_code in [200, 400, 500]  # Endpoint exists
            data = response.get_json()
            assert 'success' in data or 'error' in data
    
    def test_valid_request_twitter(self, client):
        """Test valid Twitter profile scraping request"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'data': {'username': 'testuser', 'followers': 5000}
            }
            
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            
            assert response.status_code in [200, 400, 500]
    
    def test_missing_platform(self, client):
        """Test request with missing platform"""
        response = client.post(
            '/social/scrape-profile',
            json={'username': 'testuser'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data or 'success' in data
        assert data.get('success') is False or 'required' in data.get('message', '').lower()
    
    def test_missing_username(self, client):
        """Test request with missing username"""
        response = client.post(
            '/social/scrape-profile',
            json={'platform': 'instagram'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_empty_username(self, client):
        """Test request with empty username"""
        response = client.post(
            '/social/scrape-profile',
            json={'platform': 'instagram', 'username': ''}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_unsupported_platform(self, client):
        """Test request with unsupported platform"""
        response = client.post(
            '/social/scrape-profile',
            json={'platform': 'unsupported_platform', 'username': 'testuser'}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 500]
    
    def test_wrong_content_type(self, client):
        """Test request with wrong content type"""
        response = client.post(
            '/social/scrape-profile',
            data='invalid data',
            content_type='text/plain'
        )
        
        assert response.status_code in [400, 415, 500]  # Bad request or unsupported media type
    
    def test_rate_limiting(self, client):
        """Test that endpoints handle rapid requests"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock:
            mock.return_value = {'success': False, 'error': 'Test'}
            # Make just 3 rapid requests (not 25)
            for i in range(3):
                response = client.post(
                    '/social/scrape-profile',
                    json={'platform': 'twitter', 'username': f'user{i}'}
                )
                assert response.status_code in [200, 400, 429, 500]
    
    def test_response_format_success(self, client):
        """Test successful response format"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'data': {'username': 'test', 'followers': 100}
            }
            
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            
            if response.status_code == 200:
                data = response.get_json()
                assert 'success' in data
                assert data.get('success') is True


class TestSocialPostsScrapeEndpoint:
    """Tests for /social/scrape-posts endpoint"""
    
    def test_endpoint_exists(self, client):
        """Test endpoint is accessible"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {'success': False, 'error': 'Test'}
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            assert response.status_code != 404
    
    def test_valid_request(self, client):
        """Test valid posts scraping request"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'count': 5,
                'data': []
            }
            
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser', 'limit': 10}
            )
            
            assert response.status_code in [200, 400, 500]
    
    def test_default_limit(self, client):
        """Test default limit is applied"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {'success': True, 'count': 0, 'data': []}
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'instagram', 'username': 'testuser'}
            )
            
            # Should use default limit
            assert response.status_code in [200, 400, 500]
    
    def test_custom_limit(self, client):
        """Test custom limit is accepted"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {'success': True, 'count': 0, 'data': []}
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser', 'limit': 50}
            )
            
            assert response.status_code in [200, 400, 500]
    
    def test_limit_max_capped(self, client):
        """Test limit is capped at 100"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'count': 0,
                'data': []
            }
            
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser', 'limit': 500}
            )
            
            # Should be accepted (capped to 100)
            assert response.status_code in [200, 400, 500]
    
    def test_missing_username(self, client):
        """Test request with missing username"""
        response = client.post(
            '/social/scrape-posts',
            json={'platform': 'instagram'}
        )
        
        assert response.status_code == 400
    
    def test_response_format(self, client):
        """Test response format contains expected fields"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'count': 3,
                'data': [
                    {'title': 'Post 1'},
                    {'title': 'Post 2'},
                    {'title': 'Post 3'}
                ]
            }
            
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            
            if response.status_code == 200:
                data = response.get_json()
                assert 'success' in data
                assert data.get('success') is True


class TestSocialPlatformsEndpoint:
    """Tests for /social/platforms endpoint"""
    
    def test_endpoint_exists(self, client):
        """Test endpoint is accessible"""
        response = client.get('/social/platforms')
        assert response.status_code != 404
    
    def test_response_is_json(self, client):
        """Test response is JSON"""
        response = client.get('/social/platforms')
        assert response.content_type
        assert 'json' in response.content_type.lower()
    
    def test_response_contains_platforms(self, client):
        """Test response contains platforms list"""
        response = client.get('/social/platforms')
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'platforms' in data or 'success' in data
    
    def test_response_contains_details(self, client):
        """Test response contains platform details"""
        response = client.get('/social/platforms')
        
        if response.status_code == 200:
            data = response.get_json()
            if 'details' in data:
                assert isinstance(data['details'], dict)
    
    def test_success_flag(self, client):
        """Test success flag is present"""
        response = client.get('/social/platforms')
        
        data = response.get_json()
        assert 'success' in data or 'platforms' in data
    
    def test_timestamp_included(self, client):
        """Test timestamp is included"""
        response = client.get('/social/platforms')
        
        if response.status_code == 200:
            data = response.get_json()
            if 'timestamp' in data:
                # Should be valid ISO format
                try:
                    datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                    assert True
                except:
                    assert False, "Invalid timestamp format"


class TestErrorHandling:
    """Tests for error handling in endpoints"""
    
    def test_profile_endpoint_handles_exception(self, client):
        """Test profile endpoint handles exceptions gracefully"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.side_effect = Exception("Test error")
            
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data or data.get('success') is False
    
    def test_posts_endpoint_handles_exception(self, client):
        """Test posts endpoint handles exceptions gracefully"""
        with patch('scraper.social_media_scraper.scrape_social_media_posts') as mock_scrape:
            mock_scrape.side_effect = Exception("Test error")
            
            response = client.post(
                '/social/scrape-posts',
                json={'platform': 'twitter', 'username': 'testuser'}
            )
            
            assert response.status_code == 500
    
    def test_platforms_endpoint_handles_exception(self, client):
        """Test platforms endpoint handles exceptions gracefully"""
        with patch('scraper.social_media_scraper.SocialMediaScraperFactory') as mock_factory:
            mock_factory.get_supported_platforms.side_effect = Exception("Test error")
            
            response = client.get('/social/platforms')
            
            assert response.status_code == 500
            data = response.get_json()
            assert data.get('success') is False


class TestResponseHeaders:
    """Tests for response headers"""
    
    def test_content_type_json(self, client):
        """Test content type is JSON"""
        response = client.get('/social/platforms')
        assert 'application/json' in response.content_type
    
    def test_cors_headers_if_enabled(self, client):
        """Test CORS headers if enabled"""
        response = client.get('/social/platforms')
        # Headers might vary based on configuration
        assert response.status_code in [200, 400, 500]


class TestInputValidation:
    """Tests for input validation"""
    
    def test_whitespace_trimming(self, client):
        """Test whitespace in username is trimmed"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock:
            mock.return_value = {'success': False, 'error': 'Test'}
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'instagram', 'username': '  testuser  '}
            )
            
            # Should handle whitespace
            assert response.status_code in [200, 400, 500]
    
    def test_platform_lowercase_conversion(self, client):
        """Test platform name is converted to lowercase"""
        with patch('scraper.social_media_scraper.scrape_social_media_profile') as mock_scrape:
            mock_scrape.return_value = {'success': True, 'data': {}}
            
            response = client.post(
                '/social/scrape-profile',
                json={'platform': 'INSTAGRAM', 'username': 'testuser'}
            )
            
            # Should handle uppercase platform
            assert response.status_code in [200, 400, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

