# Celery Configuration
# Broker and backend use Redis
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/2')

# Celery task settings
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'

# Task result expiration (7 days)
CELERY_RESULT_EXPIRES = 60 * 60 * 24 * 7

# Task routing (optional - for advanced setups with multiple queues)
CELERY_TASK_ROUTES = {
    'apps.core.tasks.send_sms_async': {'queue': 'sms'},
    'apps.core.tasks.send_otp_sms_async': {'queue': 'sms'},
}

# Retry configuration
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
