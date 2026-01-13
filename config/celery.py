"""
Celery Configuration for Ecommerce Application

This module configures Celery for asynchronous task processing.
Tasks include:
- SMS notifications (OTP, order updates, admin notifications)
- Email notifications (future)
- Background jobs (future)
"""
from celery import Celery
import os

# Set default Django settings module
# Using dev settings to match runserver environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Create Celery app
app = Celery('ecommerce')

# Load configuration from Django settings
# - namespace='CELERY' means all celery-related settings will have a `CELERY_` prefix
# - This will load CELERY_BROKER_URL, CELERY_RESULT_BACKEND, etc. from settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django app configs
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')
    print(f'Broker: {self.app.conf.broker_url}')


# CRITICAL: Verify broker configuration on startup
if __name__ == '__main__':
    print(f"Celery Broker URL: {app.conf.broker_url}")
    print(f"Celery Result Backend: {app.conf.result_backend}")
