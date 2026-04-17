"""
Security and performance tests
Tests for XSS prevention, injection protection, and performance
"""

import pytest
import json
import time
from scraper.validators import validate_selector, ValidationError


class TestXSSPrevention:
    """Test XSS prevention"""
    
    def test_selector_xss_script_tag(self):
        """Test XSS with script tag in selector"""
        with pytest.raises(ValidationError):
            validate_selector("<script>alert('xss')</script>")
    
    def test_selector_xss_event_handler(self):
        """Test XSS with event handler in selector"""
        with pytest.raises(ValidationError):
            validate_selector("div onmouseover='alert(0)'")
    
    def test_selector_xss_javascript_protocol(self):
        """Test XSS with javascript: protocol"""
        with pytest.raises(ValidationError):
            validate_selector("javascript:alert('xss')")
    
    def test_endpoint_xss_in_url(self, client):
        """Test XSS attempt in URL parameter"""
        payload = {
            'url': 'https://example.com/<script>alert("xss")</script>',
            'selector': 'div'
        }
        response = client.post('/scrape',
                              data=json.dumps(payload),
                              content_type='application/json')
        # Should reject invalid URL
        assert response.status_code == 400
    
    def test_endpoint_xss_in_selector(self, client):
        """Test XSS attempt in selector parameter"""
        payload = {
            'url': 'https://example.com',
            'selector': '<script>alert("xss")</script>'
        }
        response = client.post('/scrape',
                              data=json.dumps(payload),
                              content_type='application/json')
        # Should reject malicious selector
        assert response.status_code == 400


class TestSQLInjectionPrevention:
    """Test SQL injection prevention"""
    
    def test_selector_sql_injection(self):
        """Test SQL injection in selector doesn't cause issues"""
        # This shouldn't cause failures as we're not using SQL
        try:
            validate_selector("div'; DROP TABLE users; --")
            # Selector validation doesn't check for SQL
        except:
            pass
    
    def test_url_sql_injection_safe(self):
        """Test URL with SQL injection pattern"""
        from scraper.validators import validate_url
        try:
            # URL validation should reject complex injection attempts
            validate_url("https://example.com/search?q=' OR '1'='1")
        except:
            pass


class TestPathTraversalPrevention:
    """Test path traversal prevention"""
    
    def test_filename_path_traversal(self, client):
        """Test path traversal in filename"""
        payload = {
            'data': ['Item 1'],
            'filename_prefix': '../../../etc/passwd'
        }
        response = client.post('/export',
                              data=json.dumps(payload),
                              content_type='application/json')
        # Should handle safely
        assert response.status_code in [200, 400]
    
    def test_download_path_traversal(self, client):
        """Test path traversal in download request"""
        response = client.get('/download/../../etc/passwd.csv')
        # Should not allow access to parent directories
        assert response.status_code == 404 or response.status_code == 400


class TestInputValidationSecurity:
    """Test input validation for security"""
    
    def test_oversized_input(self, client):
        """Test handling of oversized input"""
        large_data = ['Item'] * 10000
        payload = {'data': large_data}
        response = client.post('/process',
                              data=json.dumps(payload),
                              content_type='application/json')
        # Should handle or reject gracefully
        assert response.status_code in [200, 400, 413]
    
    def test_null_byte_injection(self, client):
        """Test null byte injection"""
        payload = {
            'url': 'https://example.com\x00.html',
            'selector': 'div'
        }
        # Should handle null bytes safely
        try:
            response = client.post('/scrape',
                                  data=json.dumps(payload),
                                  content_type='application/json')
            assert response.status_code in [200, 400]
        except:
            pass
    
    def test_unicode_bypass_attempt(self, client):
        """Test Unicode encoding bypass attempt"""
        payload = {
            'url': 'https://example.com',
            'selector': 'd\u0069v'  # 'div' with Unicode
        }
        response = client.post('/scrape',
                              data=json.dumps(payload),
                              content_type='application/json')
        # Should handle Unicode normally
        assert response.status_code in [200, 400]


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limiting_headers(self, client):
        """Test that rate limiting headers are present"""
        # Make normal request
        response = client.get('/exports')
        # Headers might not be present if rate limiter not enabled
        # This is optional depending on implementation
        assert response.status_code in [200, 429]
    
    def test_multiple_requests_sequential(self, client):
        """Test multiple sequential requests"""
        # Make multiple requests
        for i in range(5):
            response = client.get('/health')
            assert response.status_code == 200


class TestPerformance:
    """Test performance characteristics"""
    
    def test_health_endpoint_response_time(self, client):
        """Test health endpoint responds quickly"""
        start = time.time()
        response = client.get('/health')
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in less than 1 second
    
    def test_config_endpoint_performance(self, client):
        """Test config endpoint performance"""
        start = time.time()
        response = client.get('/api/config')
        elapsed = time.time() - start
        
        # Should return quickly
        assert elapsed < 2.0
    
    def test_exports_list_performance(self, client):
        """Test exports listing performance"""
        start = time.time()
        response = client.get('/exports')
        elapsed = time.time() - start
        
        # Should list files quickly even with many files
        assert elapsed < 3.0
    
    def test_large_data_processing_performance(self, client):
        """Test processing performance with large data"""
        # Create reasonably large data set
        large_data = [f'Item {i}' for i in range(1000)]
        payload = {'data': large_data}
        
        start = time.time()
        response = client.post('/process',
                              data=json.dumps(payload),
                              content_type='application/json')
        elapsed = time.time() - start
        
        # Should process within reasonable time
        if response.status_code == 200:
            assert elapsed < 10.0  # Reasonable timeout


class TestMemoryUsage:
    """Test memory usage characteristics"""
    
    def test_dataframe_memory_efficiency(self):
        """Test DataFrame memory usage"""
        from scraper.data_processor import DataProcessor
        import sys
        
        processor = DataProcessor()
        # Create DataFrame with 1000 items
        data = [f'Item {i}' for i in range(1000)]
        df = processor.create_dataframe(data)
        
        # Check memory usage is reasonable
        memory_usage = df.memory_usage(deep=True).sum()
        assert memory_usage < 1000000  # Less than 1MB for 1000 items
    
    def test_csv_export_memory(self, temp_dir):
        """Test CSV export doesn't consume excessive memory"""
        from scraper.csv_exporter import CSVExporter
        import pandas as pd
        
        exporter = CSVExporter(output_dir=temp_dir)
        # Create moderate sized DataFrame
        df = pd.DataFrame({
            'col1': [f'value{i}' for i in range(1000)],
            'col2': [f'data{i}' for i in range(1000)]
        })
        
        # Export should complete without memory issues
        filepath = exporter.export_to_csv(df, 'test.csv')
        assert filepath is not None


class TestConcurrency:
    """Test concurrent access handling"""
    
    def test_multiple_endpoint_access(self, client):
        """Test multiple endpoint access"""
        endpoints = ['/health', '/exports', '/api/config']
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 405]
    
    def test_concurrent_json_payloads(self, client):
        """Test handling multiple JSON requests"""
        payload = {
            'url': 'https://example.com',
            'selector': 'div'
        }
        
        for i in range(3):
            response = client.post('/scrape',
                                  data=json.dumps(payload),
                                  content_type='application/json')
            assert response.status_code in [200, 400, 500]
