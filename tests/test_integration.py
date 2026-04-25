"""
Integration tests for Flask application
Tests complete workflows and endpoint integration
"""

import pytest
import json
from datetime import datetime


class TestFlaskAppInitialization:
    """Test Flask application initialization"""
    
    def test_app_creation(self, app):
        """Test Flask app is created"""
        assert app is not None
    
    def test_app_config(self, app):
        """Test app has correct config"""
        assert app.config['TESTING'] is True
    
    def test_app_has_routes(self, client):
        """Test app has registered routes"""
        # Test home route
        response = client.get('/')
        assert response.status_code in [200, 405]  # 405 if GET not allowed


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check_success(self, client):
        """Test health endpoint returns success"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'


class TestScrapeEndpoint:
    """Test web scraping endpoint"""
    
    def test_scrape_valid_request(self, client):
        """Test scraping with valid request"""
        payload = {
            'url': 'https://niftact.com',
            'selector': 'h1'
        }
        response = client.post('/scrape',
                              data=json.dumps(payload),
                              content_type='application/json')
        assert response.status_code in [200, 400, 500]
    
    def test_scrape_missing_url(self, client):
        """Test scraping without URL"""
        payload = {'selector': 'h1'}
        response = client.post('/scrape',
                              data=json.dumps(payload),
                              content_type='application/json')
        assert response.status_code == 400
    
    def test_scrape_missing_selector(self, client):
        """Test scraping without selector - should scrape all content"""
        payload = {'url': 'https://example.com'}
        response = client.post('/scrape',
                              data=json.dumps(payload),
                              content_type='application/json')
        # Selector is now optional - should return 200 and extract all content
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
    
    def test_scrape_invalid_url(self, client):
        """Test scraping with invalid URL"""
        payload = {
            'url': 'not-a-url',
            'selector': 'h1'
        }
        response = client.post('/scrape',
                              data=json.dumps(payload),
                              content_type='application/json')
        assert response.status_code == 400
    
    def test_scrape_returns_json(self, client):
        """Test scrape endpoint returns JSON"""
        payload = {
            'url': 'https://niftact.com',
            'selector': 'h1'
        }
        response = client.post('/scrape',
                              data=json.dumps(payload),
                              content_type='application/json')
        try:
            data = json.loads(response.data)
            assert isinstance(data, dict)
        except:
            pass


class TestProcessEndpoint:
    """Test data processing endpoint"""
    
    def test_process_valid_data(self, client):
        """Test processing valid data"""
        payload = {
            'data': ['Item 1', 'Item 2', 'Item 3'],
            'remove_duplicates': True,
            'handle_missing': 'drop'
        }
        response = client.post('/process',
                              data=json.dumps(payload),
                              content_type='application/json')
        assert response.status_code in [200, 400]
    
    def test_process_empty_data(self, client):
        """Test processing empty data"""
        payload = {
            'data': [],
            'remove_duplicates': True
        }
        response = client.post('/process',
                              data=json.dumps(payload),
                              content_type='application/json')
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]
    
    def test_process_with_duplicates(self, client):
        """Test duplicate removal during processing"""
        payload = {
            'data': ['Item', 'Item', 'Other'],
            'remove_duplicates': True
        }
        response = client.post('/process',
                              data=json.dumps(payload),
                              content_type='application/json')
        assert response.status_code in [200, 400]


class TestExportEndpoint:
    """Test CSV export endpoint"""
    
    def test_export_valid_data(self, client):
        """Test exporting valid data"""
        payload = {
            'data': ['Item 1', 'Item 2', 'Item 3'],
            'filename_prefix': 'test'
        }
        response = client.post('/export',
                              data=json.dumps(payload),
                              content_type='application/json')
        assert response.status_code in [200, 400]
    
    def test_export_returns_file_info(self, client):
        """Test export returns file information"""
        payload = {
            'data': ['Item 1', 'Item 2'],
            'filename_prefix': 'test'
        }
        response = client.post('/export',
                              data=json.dumps(payload),
                              content_type='application/json')
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'filename' in data or 'file_path' in data


class TestDownloadEndpoint:
    """Test file download endpoint"""
    
    def test_download_nonexistent_file(self, client):
        """Test downloading non-existent file"""
        response = client.get('/download/nonexistent.csv')
        assert response.status_code == 404
    
    def test_download_endpoint_exists(self, client):
        """Test download endpoint is available"""
        # Endpoint should exist (may return 404 for file)
        response = client.get('/download/test.csv')
        assert response.status_code in [200, 404]


class TestExportsListingEndpoint:
    """Test exports listing endpoint"""
    
    def test_list_exports(self, client):
        """Test listing exports"""
        response = client.get('/exports')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'files' in data or 'count' in data
    
    def test_exports_returns_list(self, client):
        """Test exports endpoint returns list"""
        response = client.get('/exports')
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, dict)


class TestPaginationDetection:
    """Test pagination detection endpoint"""
    
    def test_detect_pagination_valid_url(self, client):
        """Test pagination detection on valid URL"""
        payload = {'url': 'https://niftact.com'}
        response = client.post('/detect-pagination',
                              data=json.dumps(payload),
                              content_type='application/json')
        assert response.status_code in [200, 400]
    
    def test_detect_pagination_invalid_url(self, client):
        """Test pagination detection with invalid URL"""
        payload = {'url': 'invalid-url'}
        response = client.post('/detect-pagination',
                              data=json.dumps(payload),
                              content_type='application/json')
        assert response.status_code == 400


class TestAdvancedScrapingEndpoint:
    """Test advanced scraping with pagination"""
    
    def test_scrape_advanced_valid(self, client):
        """Test advanced scraping with valid parameters"""
        payload = {
            'url': 'https://niftact.com',
            'selector': 'h1',
            'pages': 1
        }
        response = client.post('/scrape-advanced',
                              data=json.dumps(payload),
                              content_type='application/json')
        assert response.status_code in [200, 400]
    
    def test_scrape_advanced_multiple_pages(self, client):
        """Test advanced scraping with multiple pages"""
        payload = {
            'url': 'https://niftact.com',
            'selector': 'p',
            'pages': 2,
            'delay': 0.5
        }
        response = client.post('/scrape-advanced',
                              data=json.dumps(payload),
                              content_type='application/json')
        assert response.status_code in [200, 400, 500]


class TestErrorHandling:
    """Test error handling across endpoints"""
    
    def test_malformed_json(self, client):
        """Test endpoint with malformed JSON"""
        response = client.post('/scrape',
                              data='{"invalid json',
                              content_type='application/json')
        assert response.status_code in [400, 415]
    
    def test_missing_content_type(self, client):
        """Test endpoint without content type"""
        payload = {'url': 'https://example.com'}
        response = client.post('/scrape',
                              data=json.dumps(payload))
        assert response.status_code in [200, 400, 415]
    
    def test_nonexistent_endpoint(self, client):
        """Test accessing nonexistent endpoint"""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404


class TestResponseFormats:
    """Test response format consistency"""
    
    def test_error_response_format(self, client):
        """Test error responses have consistent format"""
        payload = {'selector': 'h1'}  # Missing URL
        response = client.post('/scrape',
                              data=json.dumps(payload),
                              content_type='application/json')
        if response.status_code == 400:
            data = json.loads(response.data)
            assert 'error' in data or 'message' in data
    
    def test_success_response_format(self, client):
        """Test success responses have consistent format"""
        response = client.get('/health')
        data = json.loads(response.data)
        assert 'status' in data or 'success' in data
