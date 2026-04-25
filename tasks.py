"""
Async Tasks
Background task definitions for scraping operations
"""

import logging
from celery_app import celery_app
from scraper.scraper_engine import ScraperEngine
from scraper.data_processor import DataProcessor
from scraper.csv_exporter import CSVExporter
import os

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='tasks.scrape_url')
def scrape_url(self, url, selector=None, pages=1, include_attributes=False):
    """
    Async task to scrape a URL
    
    Args:
        url (str): URL to scrape
        selector (str): Optional CSS selector
        pages (int): Number of pages to scrape
        include_attributes (bool): Include element attributes
        
    Returns:
        dict: Scraping result with data
    """
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': pages})
        
        logger.info(f"Starting async scrape task: {self.request.id}")
        logger.info(f"URL: {url}, Selector: {selector}, Pages: {pages}")
        
        # Initialize scraper
        scraper = ScraperEngine(request_timeout=30, scraping_delay=1)
        
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
        
        # Update completion status
        self.update_state(
            state='SUCCESS',
            meta={
                'current': pages,
                'total': pages,
                'status': 'Scraping completed successfully'
            }
        )
        
        logger.info(f"Async scrape completed: {len(result.get('data', []))} items")
        
        return {
            'success': True,
            'task_id': self.request.id,
            'url': url,
            'selector': selector or 'all_content',
            'pages': pages,
            'count': result.get('count', 0),
            'data': result.get('data', []),
            'message': f'Successfully extracted {result.get("count", 0)} items'
        }
        
    except Exception as e:
        logger.error(f"Async scrape failed: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        return {
            'success': False,
            'task_id': self.request.id,
            'error': str(e),
            'message': 'Scraping task failed'
        }


@celery_app.task(bind=True, name='tasks.process_and_export')
def process_and_export(self, data, export_format='csv', filename_prefix='export'):
    """
    Async task to process data and export to CSV
    
    Args:
        data (list): Data to process
        export_format (str): Export format (csv)
        filename_prefix (str): Prefix for export filename
        
    Returns:
        dict: Export result with file info
    """
    try:
        self.update_state(state='PROGRESS', meta={'current': 50, 'total': 100})
        
        logger.info(f"Starting async process and export task: {self.request.id}")
        
        # Initialize processor and exporter
        processor = DataProcessor()
        exporter = CSVExporter()
        
        # Process data
        df = processor.create_dataframe(data)
        df = processor.clean_dataframe(df)
        df = processor.remove_duplicates(df)
        
        self.update_state(state='PROGRESS', meta={'current': 75, 'total': 100})
        
        # Export data
        if export_format.lower() == 'csv':
            filepath = exporter.export_to_csv(df, timestamp=True, prefix=filename_prefix)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")
        
        self.update_state(state='SUCCESS', meta={'current': 100, 'total': 100})
        
        logger.info(f"Async export completed: {filepath}")
        
        return {
            'success': True,
            'task_id': self.request.id,
            'filepath': filepath,
            'filename': os.path.basename(filepath),
            'rows': len(df),
            'columns': list(df.columns),
            'message': f'Data exported successfully to {os.path.basename(filepath)}'
        }
        
    except Exception as e:
        logger.error(f"Async export failed: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        return {
            'success': False,
            'task_id': self.request.id,
            'error': str(e),
            'message': 'Export task failed'
        }


@celery_app.task(bind=True, name='tasks.scrape_and_export')
def scrape_and_export(self, url, selector=None, pages=1, export_format='csv'):
    """
    Async task to scrape URL and directly export to CSV
    Combined task for efficiency
    
    Args:
        url (str): URL to scrape
        selector (str): Optional CSS selector
        pages (int): Number of pages
        export_format (str): Export format (csv)
        
    Returns:
        dict: Combined scrape and export result
    """
    try:
        # Step 1: Scrape
        self.update_state(state='PROGRESS', meta={'step': 'scraping', 'percent': 25})
        
        logger.info(f"Starting combined scrape and export task: {self.request.id}")
        
        scraper = ScraperEngine(request_timeout=30, scraping_delay=1)
        
        if pages > 1:
            scrape_result = scraper.scrape_multiple_pages(
                start_url=url,
                selector=selector,
                pages=pages
            )
        else:
            scrape_result = scraper.scrape(
                url=url,
                selector=selector
            )
        
        if not scrape_result['success']:
            raise Exception(scrape_result.get('error', 'Scraping failed'))
        
        data = scrape_result.get('data', [])
        
        # Step 2: Process and Export
        self.update_state(state='PROGRESS', meta={'step': 'processing', 'percent': 50})
        
        processor = DataProcessor()
        exporter = CSVExporter()
        
        df = processor.create_dataframe(data)
        df = processor.clean_dataframe(df)
        df = processor.remove_duplicates(df)
        
        self.update_state(state='PROGRESS', meta={'step': 'exporting', 'percent': 75})
        
        filepath = exporter.export_to_csv(df, timestamp=True, prefix='scrape')
        
        self.update_state(state='SUCCESS', meta={'step': 'completed', 'percent': 100})
        
        logger.info(f"Combined task completed: {filepath}")
        
        return {
            'success': True,
            'task_id': self.request.id,
            'url': url,
            'selector': selector or 'all_content',
            'pages': pages,
            'items_scraped': len(data),
            'items_exported': len(df),
            'filepath': filepath,
            'filename': os.path.basename(filepath),
            'message': f'Successfully scraped {len(data)} items and exported to {os.path.basename(filepath)}'
        }
        
    except Exception as e:
        logger.error(f"Combined task failed: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        return {
            'success': False,
            'task_id': self.request.id,
            'error': str(e),
            'message': 'Combined scrape and export task failed'
        }
