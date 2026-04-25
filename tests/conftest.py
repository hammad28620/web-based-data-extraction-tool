"""
Pytest configuration and fixtures for test suite
"""

import pytest
import os
import sys
import tempfile
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app import create_app


@pytest.fixture
def app():
    """Create Flask application for testing"""
    app_instance = create_app('testing')  # Use lowercase 'testing'
    return app_instance


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI runner for Flask commands"""
    return app.test_cli_runner()


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_html():
    """Sample HTML for testing"""
    return """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Main Heading</h1>
            <p>First paragraph</p>
            <p>Second paragraph</p>
            <div class="items">
                <span class="item">Item 1</span>
                <span class="item">Item 2</span>
                <span class="item">Item 3</span>
            </div>
            <div class="pagination">
                <a href="/page/1" class="current">1</a>
                <a href="/page/2" class="next">2</a>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for testing"""
    import pandas as pd
    return pd.DataFrame({
        'name': ['Product 1', 'Product 2', 'Product 3'],
        'price': ['$10', '$20', '$15'],
        'description': ['Desc 1', 'Desc 2', 'Desc 3']
    })


@pytest.fixture
def sample_data_list():
    """Sample data list for processing"""
    return [
        'Item 1',
        'Item 2',
        '  Item 3  ',  # Extra spaces
        'Item 2',  # Duplicate
        'Item 4'
    ]


@pytest.fixture
def celery_app():
    """Create Celery app for testing"""
    from celery_app import celery_app as app
    app.conf.update(
        CELERY_ALWAYS_EAGER=True,
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    )
    yield app

