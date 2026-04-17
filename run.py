"""
Main entry point for the Web-Based Data Extraction Tool application
Run this file to start the Flask development server

Usage:
    python run.py                    # Development mode
    FLASK_ENV=production python run.py  # Production mode
    FLASK_ENV=testing python run.py     # Testing mode
"""

import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app

# Get logger
logger = logging.getLogger(__name__)


def main():
    """
    Application entry point
    Initializes and runs the Flask server
    """
    try:
        # Get environment (default to development)
        env = os.environ.get('FLASK_ENV', 'development')
        
        # Create Flask app
        app = create_app(config_name=env)
        
        # Log startup information
        logger.info(f"Starting Web-Based Data Extraction Tool server")
        logger.info(f"Environment: {env}")
        logger.info(f"Debug mode: {app.config['DEBUG']}")
        logger.info(f"Server running on http://localhost:5000")
        
        # Run development server
        app.run(
            debug=app.config['DEBUG'],
            host='0.0.0.0',
            port=5000,
            use_reloader=True,
            use_debugger=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        print(f"ERROR: Failed to start application: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
