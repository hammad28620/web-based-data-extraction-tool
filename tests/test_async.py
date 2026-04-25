"""
Tests for async task functionality
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from celery import Celery, states
from celery.result import AsyncResult


class TestAsyncScrapeEndpointMocked:
    """Test async scraping endpoints with mocked Celery"""
    
    @patch('app.scrape_url')
    def test_scrape_async_submit_mocked(self, mock_scrape_url, client):
        """Test submitting an async scrape task with mocked Celery"""
        # Mock the Celery task
        mock_task = MagicMock()
        mock_task.id = 'mock_task_id_123'
        mock_scrape_url.apply_async.return_value = mock_task
        
        payload = {
            'url': 'https://httpbin.org/html',
            'pages': 1
        }
        
        response = client.post(
            '/scrape-async',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 202
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'task_id' in data
        assert 'status_url' in data
        assert 'result_url' in data
    
    def test_scrape_async_missing_url(self, client):
        """Test async scrape without URL"""
        payload = {
            'pages': 1
        }
        
        response = client.post(
            '/scrape-async',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
    
    def test_scrape_async_invalid_url(self, client):
        """Test async scrape with invalid URL"""
        payload = {
            'url': 'not a valid url',
            'pages': 1
        }
        
        response = client.post(
            '/scrape-async',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_scrape_async_invalid_content_type(self, client):
        """Test async scrape with invalid content type"""
        response = client.post(
            '/scrape-async',
            data='not json',
            content_type='text/plain'
        )
        
        # Flask returns 415 for unsupported media type (or 500 if caught by error handler)
        assert response.status_code in [415, 500]


class TestTaskStatusEndpointMocked:
    """Test task status endpoints with mocked Celery"""
    
    @patch('app.celery_app.AsyncResult')
    def test_get_task_status_pending(self, mock_async_result, client):
        """Test getting status of a pending task"""
        mock_result = MagicMock()
        mock_result.status = 'PENDING'
        mock_result.ready.return_value = False
        mock_async_result.return_value = mock_result
        
        response = client.get('/task/mock_task_id')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['task_id'] == 'mock_task_id'
        assert data['status'] == 'PENDING'
        assert data['ready'] is False
    
    @patch('app.celery_app.AsyncResult')
    def test_get_task_status_success(self, mock_async_result, client):
        """Test getting status of a successful task"""
        mock_result = MagicMock()
        mock_result.status = 'SUCCESS'
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = {
            'success': True,
            'data': [{'name': 'item1'}],
            'count': 1
        }
        mock_async_result.return_value = mock_result
        
        response = client.get('/task/mock_task_id')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['task_id'] == 'mock_task_id'
        assert data['status'] == 'SUCCESS'
        assert data['ready'] is True
        assert data['successful'] is True
    
    @patch('app.celery_app.AsyncResult')
    def test_get_task_status_failure(self, mock_async_result, client):
        """Test getting status of a failed task"""
        mock_result = MagicMock()
        mock_result.status = 'FAILURE'
        mock_result.ready.return_value = True
        mock_result.successful.return_value = False
        mock_result.info = Exception('Connection timeout')
        mock_result.traceback = 'Traceback...'
        mock_async_result.return_value = mock_result
        
        response = client.get('/task/mock_task_id')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['task_id'] == 'mock_task_id'
        assert data['status'] == 'FAILURE'
        assert data['ready'] is True
        assert data['successful'] is False


class TestTaskResultEndpointMocked:
    """Test task result endpoints with mocked Celery"""
    
    @patch('app.celery_app.AsyncResult')
    def test_get_task_result_success(self, mock_async_result, client):
        """Test getting result of a successful task"""
        mock_result = MagicMock()
        mock_result.ready.return_value = True
        mock_result.state = 'SUCCESS'
        mock_result.result = {
            'success': True,
            'data': [{'name': 'item1'}],
            'count': 1,
            'message': 'Success'
        }
        mock_async_result.return_value = mock_result
        
        response = client.get('/task/mock_task_id/result')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'result' in data
    
    @patch('app.celery_app.AsyncResult')
    def test_get_task_result_not_ready(self, mock_async_result, client):
        """Test getting result of a task that's not ready"""
        mock_result = MagicMock()
        mock_result.ready.return_value = False
        mock_result.status = 'PROGRESS'
        mock_async_result.return_value = mock_result
        
        response = client.get('/task/mock_task_id/result')
        
        assert response.status_code == 202
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Not Ready' in data['error']
    
    @patch('app.celery_app.AsyncResult')
    def test_get_task_result_failed(self, mock_async_result, client):
        """Test getting result of a failed task"""
        mock_result = MagicMock()
        mock_result.ready.return_value = True
        mock_result.state = 'FAILURE'
        mock_result.info = Exception('Connection error')
        mock_async_result.return_value = mock_result
        
        response = client.get('/task/mock_task_id/result')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False


class TestTaskCancelEndpointMocked:
    """Test task cancellation endpoints with mocked Celery"""
    
    @patch('app.celery_app.AsyncResult')
    @patch('app.celery_app.control.revoke')
    def test_cancel_task_running(self, mock_revoke, mock_async_result, client):
        """Test cancelling a running task"""
        mock_result = MagicMock()
        mock_result.status = 'PROGRESS'
        mock_async_result.return_value = mock_result
        
        response = client.post('/task/mock_task_id/cancel')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['task_id'] == 'mock_task_id'
    
    @patch('app.celery_app.AsyncResult')
    def test_cancel_task_already_complete(self, mock_async_result, client):
        """Test cancelling a task that's already complete"""
        mock_result = MagicMock()
        mock_result.status = 'SUCCESS'
        mock_async_result.return_value = mock_result
        
        response = client.post('/task/mock_task_id/cancel')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Already Complete' in data['error']


class TestListTasksEndpointMocked:
    """Test task listing endpoint with mocked Celery"""
    
    @patch('celery.app.control.Inspect')
    def test_list_tasks(self, mock_inspect_class, client):
        """Test listing all tasks"""
        # Mock the Inspect class
        mock_inspect = MagicMock()
        mock_inspect.active.return_value = {
            'worker1': [
                {
                    'id': 'task1',
                    'name': 'tasks.scrape_url',
                    'time_start': 123456
                }
            ]
        }
        mock_inspect.scheduled.return_value = {}
        mock_inspect.reserved.return_value = {}
        mock_inspect_class.return_value = mock_inspect
        
        response = client.get('/tasks')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'summary' in data
        assert 'active' in data['summary']


class TestAsyncIntegrationMocked:
    """Integration tests for async functionality with mocks"""
    
    @patch('app.scrape_url')
    @patch('app.celery_app.AsyncResult')
    def test_full_async_workflow_mocked(self, mock_async_result, mock_scrape_url, client):
        """Test complete async workflow: submit -> check status -> get result"""
        # Mock submit
        mock_task = MagicMock()
        mock_task.id = 'task_workflow_123'
        mock_scrape_url.apply_async.return_value = mock_task
        
        # Submit task
        payload = {
            'url': 'https://httpbin.org/html',
            'pages': 1
        }
        
        response = client.post(
            '/scrape-async',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 202
        submit_data = json.loads(response.data)
        task_id = submit_data['task_id']
        
        # Mock status check - simulate task completion
        mock_result = MagicMock()
        mock_result.status = 'SUCCESS'
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = {
            'success': True,
            'data': [{'text': 'Sample content'}],
            'count': 1
        }
        mock_async_result.return_value = mock_result
        
        # Check status
        response = client.get(f'/task/{task_id}')
        assert response.status_code == 200
        status_data = json.loads(response.data)
        assert status_data['task_id'] == task_id
        assert status_data['status'] == 'SUCCESS'


class TestAsyncWithSelector:
    """Test async scraping with CSS selector"""
    
    @patch('app.scrape_url')
    def test_async_with_selector(self, mock_scrape_url, client):
        """Test async scraping with CSS selector"""
        mock_task = MagicMock()
        mock_task.id = 'task_with_selector_456'
        mock_scrape_url.apply_async.return_value = mock_task
        
        payload = {
            'url': 'https://httpbin.org/html',
            'selector': 'h1',
            'pages': 1
        }
        
        response = client.post(
            '/scrape-async',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 202
        data = json.loads(response.data)
        assert 'task_id' in data
        
        # Verify scrape_url.apply_async was called
        assert mock_scrape_url.apply_async.called


class TestAsyncErrorHandling:
    """Test error handling in async endpoints"""
    
    @patch('app.scrape_url')
    def test_async_task_submission_error(self, mock_scrape_url, client):
        """Test handling of task submission errors"""
        mock_scrape_url.apply_async.side_effect = Exception('Redis connection failed')
        
        payload = {
            'url': 'https://httpbin.org/html',
            'pages': 1
        }
        
        response = client.post(
            '/scrape-async',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should still return 500 on server error
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_invalid_json_payload(self, client):
        """Test handling of invalid JSON"""
        response = client.post(
            '/scrape-async',
            data='{"invalid": json}',
            content_type='application/json'
        )
        
        # Should return 400 for bad request
        assert response.status_code in [400, 415]

