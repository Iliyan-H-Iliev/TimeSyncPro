# myproject/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TimeSyncPro.settings')

app = Celery('TimeSyncPro')
app.conf.broker_url = 'redis://localhost:6379/0'  # Add this line
app.conf.result_backend = 'redis://localhost:6379/0'  # Add this line

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.update(
    broker_connection_retry_on_startup=True,  # Add this line
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True

# Load task modules from all registered Django  app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
