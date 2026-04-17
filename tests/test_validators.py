"""
Unit tests for validators module
Tests input validation and security checks
"""

import pytest
from scraper.validators import (
    validate_url,
    validate_selector,
    validate_page_number,
    validate_scrape_request,
    ValidationError
)


class TestURLValidation:
    """Test URL validation"""
    
    def test_valid_http_url(self):
        """Test valid HTTP URL"""
        result = validate_url("http://example.com")
        assert result is True
    
    def test_valid_https_url(self):
        """Test valid HTTPS URL"""
        result = validate_url("https://example.com")
        assert result is True
    
    def test_valid_url_with_path(self):
        """Test URL with path"""
        result = validate_url("https://example.com/path/to/page")
        assert result is True
    
    def test_invalid_url_no_scheme(self):
        """Test URL without scheme"""
        with pytest.raises(ValidationError):
            validate_url("example.com")
    
    def test_invalid_url_wrong_scheme(self):
        """Test URL with wrong scheme"""
        with pytest.raises(ValidationError):
            validate_url("ftp://example.com")
    
    def test_invalid_url_empty(self):
        """Test empty URL"""
        with pytest.raises(ValidationError):
            validate_url("")
    
    def test_invalid_url_malformed(self):
        """Test malformed URL"""
        with pytest.raises(ValidationError):
            validate_url("not a url")
    
    def test_url_with_query_params(self):
        """Test URL with query parameters"""
        result = validate_url("https://example.com/search?q=test&lang=en")
        assert result is True


class TestSelectorValidation:
    """Test CSS selector validation"""
    
    def test_valid_simple_selector(self):
        """Test simple selector"""
        result = validate_selector("div")
        assert result is True
    
    def test_valid_class_selector(self):
        """Test class selector"""
        result = validate_selector(".item")
        assert result is True
    
    def test_valid_id_selector(self):
        """Test ID selector"""
        result = validate_selector("#main")
        assert result is True
    
    def test_valid_complex_selector(self):
        """Test complex selector"""
        result = validate_selector("div.container > p.text")
        assert result is True
    
    def test_empty_selector(self):
        """Test empty selector"""
        with pytest.raises(ValidationError):
            validate_selector("")
    
    def test_selector_too_long(self):
        """Test selector exceeding length limit"""
        long_selector = "div" * 200  # Many repetitions
        with pytest.raises(ValidationError):
            validate_selector(long_selector)
    
    def test_selector_with_xss_attempt(self):
        """Test selector with XSS-like patterns"""
        with pytest.raises(ValidationError):
            validate_selector("<script>alert('xss')</script>")
    
    def test_selector_with_quotes(self):
        """Test valid selector with quotes (for attribute selectors)"""
        result = validate_selector('[data-value="123"]')
        assert result is True


class TestPageNumberValidation:
    """Test page number validation"""
    
    def test_valid_page_number(self):
        """Test valid page number"""
        result = validate_page_number(1)
        assert result is True
    
    def test_valid_page_number_mid_range(self):
        """Test page number in middle of range"""
        result = validate_page_number(50)
        assert result is True
    
    def test_valid_page_number_max(self):
        """Test page number at max allowed"""
        result = validate_page_number(100)
        assert result is True
    
    def test_invalid_page_zero(self):
        """Test page number zero"""
        with pytest.raises(ValidationError):
            validate_page_number(0)
    
    def test_invalid_page_negative(self):
        """Test negative page number"""
        with pytest.raises(ValidationError):
            validate_page_number(-1)
    
    def test_invalid_page_exceeds_max(self):
        """Test page number exceeding max"""
        with pytest.raises(ValidationError):
            validate_page_number(101)
    
    def test_page_number_string_digits(self):
        """Test page number as string of digits (should fail - must be int)"""
        with pytest.raises(ValidationError):
            validate_page_number("5")
    
    def test_page_number_invalid_string(self):
        """Test invalid page number string"""
        with pytest.raises(ValidationError):
            validate_page_number("abc")


class TestScrapeRequestValidation:
    """Test complete scrape request validation"""
    
    def test_valid_scrape_request(self):
        """Test valid scrape request"""
        request_data = {
            "url": "https://example.com",
            "selector": ".item"
        }
        result = validate_scrape_request(request_data)
        assert result['url'] == "https://example.com"
        assert result['selector'] == ".item"
    
    def test_request_with_pages(self):
        """Test request with pages parameter"""
        request_data = {
            "url": "https://example.com",
            "selector": ".item",
            "pages": 3
        }
        result = validate_scrape_request(request_data)
        assert result['pages'] == 3
    
    def test_request_missing_url(self):
        """Test request missing URL"""
        request_data = {"selector": ".item"}
        with pytest.raises(ValidationError):
            validate_scrape_request(request_data)
    
    def test_request_missing_selector(self):
        """Test request missing selector"""
        request_data = {"url": "https://example.com"}
        with pytest.raises(ValidationError):
            validate_scrape_request(request_data)
    
    def test_request_invalid_url(self):
        """Test request with invalid URL"""
        request_data = {
            "url": "invalid",
            "selector": ".item"
        }
        with pytest.raises(ValidationError):
            validate_scrape_request(request_data)
    
    def test_request_invalid_pages(self):
        """Test request with invalid pages"""
        request_data = {
            "url": "https://example.com",
            "selector": ".item",
            "pages": 150
        }
        with pytest.raises(ValidationError):
            validate_scrape_request(request_data)
    
    def test_request_empty_url(self):
        """Test request with empty URL"""
        request_data = {
            "url": "",
            "selector": ".item"
        }
        with pytest.raises(ValidationError):
            validate_scrape_request(request_data)


class TestValidationErrorException:
    """Test ValidationError exception"""
    
    def test_validation_error_message(self):
        """Test ValidationError contains proper message"""
        try:
            raise ValidationError("Test error message")
        except ValidationError as e:
            assert "Test error message" in str(e)
    
    def test_validation_error_is_exception(self):
        """Test ValidationError is an Exception"""
        assert issubclass(ValidationError, Exception)
