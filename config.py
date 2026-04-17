"""
Configuration module for Web-Based Data Extraction Tool
Contains all configuration settings for the Flask application
"""

import os
from datetime import timedelta

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Flask Configuration
class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Flask settings
    SEND_FILE_MAX_AGE_DEFAULT = 0
    JSON_SORT_KEYS = False
    
    # Request settings
    REQUEST_TIMEOUT = 30  # seconds (increased from 10 for slow websites)
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    
    # Scraping settings
    SCRAPING_DELAY = 1  # seconds between requests
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    # Pagination settings
    DEFAULT_MAX_PAGES = 5
    PAGE_LIMIT = 100
    
    # Data settings
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    MAX_ROWS_DISPLAY = 1000
    
    # Logging settings
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    LOG_FILE = os.path.join(LOG_DIR, 'scraper.log')
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    REQUEST_TIMEOUT = 5
    SCRAPING_DELAY = 0


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'WARNING'
    SCRAPING_DELAY = 2  # Increased delay for production


# Configuration factory
def get_config(env=None):
    """
    Get configuration based on environment
    
    Args:
        env (str): Environment name (development, testing, production)
        
    Returns:
        Config: Configuration class
    """
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    
    config_map = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
    }
    
    return config_map.get(env, DevelopmentConfig)
