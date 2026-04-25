"""
Celery Application Configuration
Handles async task processing for scraping operations
"""

from celery import Celery
import os

# Initialize Celery app
celery_app = Celery(__name__)

# Celery configuration
class CeleryConfig:
    """Celery configuration settings"""
    # Broker settings
    broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
    
    # Task settings
    task_serializer = 'json'
    accept_content = ['json']
    result_serializer = 'json'
    timezone = 'UTC'
    enable_utc = True
    
    # Task execution settings
    task_track_started = True
    task_time_limit = 30 * 60  # 30 minutes hard limit
    task_soft_time_limit = 25 * 60  # 25 minutes soft limit
    
    # Result settings
    result_expires = 3600  # Results expire after 1 hour
    result_backend_transport_options = {
        'master_name': 'mymaster',
        'socket_connect_timeout': 5,
        'socket_timeout': 5,
        'retry_on_timeout': True
    }
    
    # Worker settings
    worker_prefetch_multiplier = 1
    worker_max_tasks_per_child = 1000

# Apply configuration
celery_app.config_from_object(CeleryConfig)

# Auto-discover tasks
celery_app.autodiscover_tasks(['tasks'], force=True)

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery setup"""
    print(f'Request: {self.request!r}')
