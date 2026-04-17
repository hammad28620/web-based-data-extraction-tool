"""
Flask application initialization and configuration
Contains app factory, routes, and error handlers
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from datetime import datetime
import sys

# Add scraper module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scraper.scraper_engine import ScraperEngine
from scraper.validators import validate_scrape_request, ValidationError
from scraper.data_processor import DataProcessor
from scraper.csv_exporter import CSVExporter
from scraper.pagination_handler import PaginationHandler, ProgressTracker

logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """
    Application factory function
    Creates and configures Flask application instance
    
    Args:
        config_name (str): Configuration environment name (development, testing, production)
        
    Returns:
        Flask: Configured Flask application instance
    """
    from config import get_config
    
    # Create Flask app
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Create necessary directories
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    os.makedirs(app.config['LOG_DIR'], exist_ok=True)
    
    # Setup logging
    setup_logging(app)
    
    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    
    logger.info(f"Flask app initialized in {config.__name__} mode")
    logger.info("Rate limiting enabled - 200 requests/day, 50 requests/hour")
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register routes
    register_routes(app, limiter)
    
    return app


def setup_logging(app):
    """
    Configure logging for the application
    
    Args:
        app (Flask): Flask application instance
    """
    log_dir = app.config['LOG_DIR']
    log_file = app.config['LOG_FILE']
    log_level = app.config['LOG_LEVEL']
    log_format = app.config['LOG_FORMAT']
    
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Remove existing handlers to avoid duplicates
    app.logger.handlers = []
    
    # Create file handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, log_level))
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(getattr(logging, log_level))
    
    logger.info(f"Logging configured. Log file: {log_file}")


def register_error_handlers(app):
    """
    Register error handlers for common HTTP errors
    
    Args:
        app (Flask): Flask application instance
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors"""
        logger.error(f"Bad Request: {str(error)}")
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': 'The request was invalid or malformed',
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        logger.warning(f"Not Found: {request.path}")
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors"""
        logger.error(f"Internal Server Error: {str(error)}")
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred. Please try again later.',
            'timestamp': datetime.utcnow().isoformat()
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all unhandled exceptions"""
        logger.error(f"Unhandled Exception: {str(error)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'An unexpected error occurred',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


def register_routes(app, limiter=None):
    """
    Register all application routes
    
    Args:
        app (Flask): Flask application instance
        limiter (Limiter): Flask-Limiter instance for rate limiting
    """
    # Default no-op limiter if none provided
    if limiter is None:
        class NoOpLimiter:
            def limit(self, *args, **kwargs):
                return lambda f: f
        limiter = NoOpLimiter()
    
    @app.route('/', methods=['GET'])
    def index():
        """
        Home page route
        Serves the main HTML interface
        
        Returns:
            str: Rendered HTML template
        """
        logger.info("Home page accessed")
        try:
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Error rendering index.html: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Template Error',
                'message': 'Failed to load the main page'
            }), 500
    
    @app.route('/scrape', methods=['POST'])
    @limiter.limit("10 per minute")
    def scrape():
        """
        Scraping endpoint (Rate limited: 10 per minute)
        Handles scraping requests from the frontend
        
        Expected JSON payload:
        {
            "url": "https://example.com",
            "selector": "div.class-name or tag-name",
            "pages": 1 (optional),
            "include_attributes": false (optional)
        }
        
        Returns:
            JSON response with scraped data or error
        """
        logger.info("Scrape endpoint called")
        
        try:
            # Get JSON data from request
            data = request.get_json()
            
            if not data:
                logger.warning("No JSON data provided in scrape request")
                return jsonify({
                    'success': False,
                    'error': 'No Data',
                    'message': 'Request body must be JSON'
                }), 400
            
            # Validate request data
            try:
                validated_data = validate_scrape_request(data)
            except ValidationError as e:
                logger.warning(f"Validation error: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Validation Error',
                    'message': str(e)
                }), 400
            
            # Extract validated parameters
            url = validated_data['url']
            selector = validated_data['selector']
            pages = validated_data['pages']
            include_attributes = validated_data.get('include_attributes', False)
            
            logger.info(f"Scraping: URL={url}, Selector={selector}, Pages={pages}")
            
            # Initialize scraper with config
            scraper = ScraperEngine(
                request_timeout=app.config['REQUEST_TIMEOUT'],
                scraping_delay=app.config['SCRAPING_DELAY'],
                user_agent=app.config['USER_AGENT']
            )
            
            # Perform scraping
            if pages > 1:
                result = scraper.scrape_multiple_pages(
                    start_url=url,
                    selector=selector,
                    pages=pages
                )
            else:
                result = scraper.scrape(
                    url=url,
                    selector=selector,
                    include_attributes=include_attributes
                )
            
            # Format response
            if result['success']:
                return jsonify({
                    'success': True,
                    'url': url,
                    'selector': selector,
                    'pages': pages if pages > 1 else None,
                    'count': result['count'],
                    'data': result['data'],
                    'message': result['message'],
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
            else:
                logger.error(f"Scraping failed: {result.get('error')}")
                return jsonify({
                    'success': False,
                    'error': 'Scraping Failed',
                    'message': result.get('error', 'Unknown error occurred'),
                    'timestamp': datetime.utcnow().isoformat()
                }), 400
            
        except ValueError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Invalid JSON',
                'message': 'Request body must be valid JSON'
            }), 400
        
        except Exception as e:
            logger.error(f"Error in scrape endpoint: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Scraping Error',
                'message': 'An unexpected error occurred during scraping'
            }), 500
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint
        Used to verify application is running
        
        Returns:
            JSON response with application status
        """
        logger.debug("Health check requested")
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    @app.route('/api/config', methods=['GET'])
    def get_app_config():
        """
        Get application configuration details
        Returns non-sensitive configuration information
        
        Returns:
            JSON response with app configuration
        """
        logger.info("Config endpoint accessed")
        return jsonify({
            'success': True,
            'config': {
                'debug': app.config['DEBUG'],
                'max_content_length': app.config['MAX_CONTENT_LENGTH'],
                'request_timeout': app.config['REQUEST_TIMEOUT'],
                'scraping_delay': app.config['SCRAPING_DELAY'],
                'default_max_pages': app.config['DEFAULT_MAX_PAGES'],
                'max_rows_display': app.config['MAX_ROWS_DISPLAY']
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    @app.route('/process', methods=['POST'])
    @limiter.limit("20 per minute")
    def process_data():
        """
        Process scraped data and convert to DataFrame
        Handles cleaning, validation, and formatting
        
        Expected JSON payload:
        {
            "data": [...],  # Array of scraped items
            "selector": "selector used",
            "remove_duplicates": true,
            "handle_missing": "drop"  # or "fill"
        }
        
        Returns:
            JSON response with processed data preview
        """
        logger.info("Data processing endpoint called")
        
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No Data',
                    'message': 'Request body must be JSON'
                }), 400
            
            # Extract data
            raw_data = data.get('data', [])
            selector = data.get('selector', 'Data')
            
            if not raw_data:
                return jsonify({
                    'success': False,
                    'error': 'Empty Data',
                    'message': 'No data to process'
                }), 400
            
            # Initialize processor
            processor = DataProcessor(max_rows=app.config['MAX_ROWS_DISPLAY'])
            
            try:
                # Create DataFrame
                df = processor.create_dataframe(raw_data, column_name=selector)
                
                # Clean data
                df = processor.clean_dataframe(df)
                
                # Remove duplicates if requested
                if data.get('remove_duplicates', True):
                    df = processor.remove_duplicates(df)
                
                # Handle missing values
                missing_method = data.get('handle_missing', 'drop')
                df = processor.handle_missing_values(df, method=missing_method)
                
                # Get summary and preview
                summary = processor.get_data_summary(df)
                validation = processor.validate_data(df)
                preview = processor.get_preview(df, rows=10)
                
                logger.info("Data processing completed successfully")
                
                return jsonify({
                    'success': True,
                    'message': 'Data processed successfully',
                    'summary': summary,
                    'validation': validation,
                    'preview': preview,
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
            
            except Exception as e:
                logger.error(f"Error processing data: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Processing Error',
                    'message': str(e)
                }), 400
        
        except Exception as e:
            logger.error(f"Error in process endpoint: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Server Error',
                'message': 'An unexpected error occurred'
            }), 500
    
    @app.route('/export', methods=['POST'])
    @limiter.limit("20 per minute")
    def export_data():
        """
        Export scraped and processed data to CSV
        
        Expected JSON payload:
        {
            "data": [...],  # Array of data to export
            "selector": "selector used",
            "filename": "custom_filename.csv" (optional)
        }
        
        Returns:
            JSON response with export details and download link
        """
        logger.info("Data export endpoint called")
        
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No Data',
                    'message': 'Request body must be JSON'
                }), 400
            
            raw_data = data.get('data', [])
            
            if not raw_data:
                return jsonify({
                    'success': False,
                    'error': 'Empty Data',
                    'message': 'No data to export'
                }), 400
            
            try:
                # Initialize processor and exporter
                processor = DataProcessor(max_rows=app.config['MAX_ROWS_DISPLAY'])
                exporter = CSVExporter(output_dir=app.config['DATA_DIR'])
                
                # Process data
                df = processor.create_dataframe(raw_data, column_name='Data')
                df = processor.clean_dataframe(df)
                df = processor.remove_duplicates(df)
                df = processor.handle_missing_values(df, method='drop')
                
                # Generate filename
                selector = data.get('selector', 'scrape')
                custom_filename = data.get('filename')
                
                if custom_filename:
                    filename = custom_filename
                else:
                    filename = exporter.generate_filename(prefix=selector)
                
                # Export to CSV
                success, filepath = exporter.export_to_csv(df, filename=filename)
                
                if success:
                    file_info = exporter.get_file_info(filepath)
                    
                    logger.info(f"Data exported successfully: {filepath}")
                    
                    return jsonify({
                        'success': True,
                        'message': 'Data exported successfully',
                        'file_info': file_info,
                        'download_url': f'/download/{filename}',
                        'rows_exported': len(df),
                        'timestamp': datetime.utcnow().isoformat()
                    }), 200
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Export Error',
                        'message': 'Failed to create CSV file'
                    }), 400
            
            except Exception as e:
                logger.error(f"Error exporting data: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Export Error',
                    'message': str(e)
                }), 400
        
        except Exception as e:
            logger.error(f"Error in export endpoint: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Server Error',
                'message': 'An unexpected error occurred'
            }), 500
    
    @app.route('/download/<filename>', methods=['GET'])
    def download_file(filename):
        """
        Download exported CSV file
        
        Args:
            filename (str): Name of file to download
            
        Returns:
            File download or error response
        """
        logger.info(f"Download requested for: {filename}")
        
        try:
            # Validate filename (prevent directory traversal)
            if '..' in filename or '/' in filename or '\\' in filename:
                logger.warning(f"Invalid filename attempted: {filename}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid Filename',
                    'message': 'Invalid filename'
                }), 400
            
            filepath = os.path.join(app.config['DATA_DIR'], filename)
            
            # Check if file exists
            if not os.path.exists(filepath):
                logger.warning(f"File not found: {filepath}")
                return jsonify({
                    'success': False,
                    'error': 'File Not Found',
                    'message': 'Download file not found'
                }), 404
            
            logger.info(f"Sending file: {filepath}")
            
            return send_file(
                filepath,
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
        
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Download Error',
                'message': 'Failed to download file'
            }), 500
    
    @app.route('/exports', methods=['GET'])
    def list_exports():
        """
        List all exported CSV files
        
        Returns:
            JSON response with list of files
        """
        logger.info("List exports endpoint called")
        
        try:
            exporter = CSVExporter(output_dir=app.config['DATA_DIR'])
            files = exporter.list_exports()
            
            file_details = []
            for filename in files:
                filepath = os.path.join(app.config['DATA_DIR'], filename)
                try:
                    file_info = exporter.get_file_info(filepath)
                    file_details.append(file_info)
                except:
                    pass
            
            return jsonify({
                'success': True,
                'count': len(file_details),
                'files': file_details,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
        except Exception as e:
            logger.error(f"Error listing exports: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'List Error',
                'message': str(e)
            }), 500
    
    @app.route('/detect-pagination', methods=['POST'])
    @limiter.limit("10 per minute")
    def detect_pagination():
        """
        Detect if a website has pagination
        
        Expected JSON payload:
        {
            "url": "https://example.com"
        }
        
        Returns:
            JSON response with pagination detection results
        """
        logger.info("Pagination detection endpoint called")
        
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No Data',
                    'message': 'Request body must be JSON'
                }), 400
            
            url = data.get('url', '').strip()
            
            if not url:
                return jsonify({
                    'success': False,
                    'error': 'Missing URL',
                    'message': 'URL is required'
                }), 400
            
            try:
                # Fetch and parse
                scraper = ScraperEngine(
                    request_timeout=app.config['REQUEST_TIMEOUT'],
                    user_agent=app.config['USER_AGENT']
                )
                
                html_content = scraper.fetch_page(url)
                soup = scraper.parse_html(html_content)
                
                # Detect pagination
                pagination_handler = PaginationHandler(max_pages=app.config['DEFAULT_MAX_PAGES'])
                pagination_result = pagination_handler.detect_pagination(soup)
                page_info = pagination_handler.extract_page_info(soup)
                
                logger.info(f"Pagination detection result: {pagination_result}")
                
                return jsonify({
                    'success': True,
                    'url': url,
                    'pagination': pagination_result,
                    'page_info': page_info,
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
            
            except Exception as e:
                logger.error(f"Error detecting pagination: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Detection Error',
                    'message': str(e)
                }), 400
        
        except Exception as e:
            logger.error(f"Error in pagination detection endpoint: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Server Error',
                'message': 'An unexpected error occurred'
            }), 500
    
    @app.route('/scrape-advanced', methods=['POST'])
    @limiter.limit("10 per minute")
    def scrape_advanced():
        """
        Advanced scraping with pagination support and progress tracking
        Expected JSON payload:
        {
            "url": "https://example.com",
            "selector": ".item",
            "pages": 3,
            "next_page_selector": "a.next" (optional),
            "delay": 1.5
        }
        
        Returns:
            JSON response with scraped data and statistics
        """
        logger.info("Advanced scraping endpoint called")
        
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No Data',
                    'message': 'Request body must be JSON'
                }), 400
            
            # Validate request
            try:
                validated_data = validate_scrape_request(data)
            except ValidationError as e:
                logger.warning(f"Validation error: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Validation Error',
                    'message': str(e)
                }), 400
            
            url = validated_data['url']
            selector = validated_data['selector']
            pages = validated_data['pages']
            next_page_selector = data.get('next_page_selector')
            custom_delay = data.get('delay', app.config['SCRAPING_DELAY'])
            
            logger.info(f"Advanced scraping: URL={url}, Selector={selector}, Pages={pages}")
            
            # Initialize components
            scraper = ScraperEngine(
                request_timeout=app.config['REQUEST_TIMEOUT'],
                scraping_delay=custom_delay,
                user_agent=app.config['USER_AGENT']
            )
            
            pagination_handler = PaginationHandler(max_pages=pages)
            progress_tracker = ProgressTracker(total_pages=pages)
            
            all_data = []
            current_url = url
            
            try:
                for page_num in range(pages):
                    progress_tracker.start_page(page_num + 1)
                    
                    try:
                        # Fetch and parse
                        html_content = scraper.fetch_page(current_url)
                        soup = scraper.parse_html(html_content)
                        
                        # Extract data
                        page_data = scraper.extract_elements(soup, selector)
                        all_data.extend(page_data)
                        
                        progress_tracker.update(len(page_data))
                        progress_tracker.page_complete()
                        
                        logger.info(f"Page {page_num + 1}: Extracted {len(page_data)} items")
                        
                        # Find next page URL if not last page
                        if page_num < pages - 1:
                            next_url = pagination_handler.get_next_page_url(
                                soup, 
                                current_url,
                                custom_selector=next_page_selector
                            )
                            
                            if next_url and pagination_handler.validate_next_page(next_url, current_url):
                                current_url = next_url
                                logger.info(f"Moving to next page: {current_url}")
                            else:
                                logger.warning("No valid next page found, stopping pagination")
                                break
                    
                    except Exception as e:
                        logger.error(f"Error scraping page {page_num + 1}: {str(e)}")
                        progress_tracker.page_complete()
                        if page_num == 0:  # Fail on first page
                            raise
                        else:  # Continue from error on subsequent pages
                            continue
                
                progress = progress_tracker.get_progress()
                summary = progress_tracker.get_summary()
                
                logger.info(f"Advanced scraping completed. Total items: {len(all_data)}")
                
                return jsonify({
                    'success': True,
                    'url': url,
                    'selector': selector,
                    'pages_scraped': progress['pages_completed'],
                    'total_items': len(all_data),
                    'data': all_data,
                    'progress': progress,
                    'summary': summary,
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
            
            except Exception as e:
                logger.error(f"Error in advanced scraping: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Scraping Error',
                    'message': str(e),
                    'partial_data': all_data if all_data else [],
                    'progress': progress_tracker.get_progress()
                }), 400
        
        except Exception as e:
            logger.error(f"Error in scrape-advanced endpoint: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Server Error',
                'message': 'An unexpected error occurred'
            }), 500
    
    logger.info("All routes registered successfully")
