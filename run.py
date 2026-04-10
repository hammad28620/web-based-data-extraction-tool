"""
Main entry point for the Web-Based Data Extraction Tool application
Run this file to start the Flask development server
"""

import os
import sys
import logging
from flask import Flask
from config import get_config

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def create_app(config_name=None):
    """
    Create and configure Flask application
    
    Args:
        config_name (str): Configuration environment name
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Create necessary directories
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    os.makedirs(app.config['LOG_DIR'], exist_ok=True)
    
    # Setup logging
    setup_logging(app)
    
    return app


def setup_logging(app):
    """
    Setup logging configuration for the application
    
    Args:
        app (Flask): Flask application instance
    """
    log_dir = app.config['LOG_DIR']
    log_file = app.config['LOG_FILE']
    
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL']),
        format=app.config['LOG_FORMAT'],
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
