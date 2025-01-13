import os

from celery import Celery
from time import sleep

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quantifiedante.settings')

app = Celery('quantifiedante')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()

@app.task
def add(x,y):
    return x+y

# @app.task(bind=True, ignore_result=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')

app.conf.broker_connection_retry_on_startup = True

from celery.schedules import crontab

app.conf.beat_schedule = {
    'my_periodic_task': {
        'task': 'userside.tasks.renew_access_token',
        'schedule': crontab(minute='*/35'),  # Run every 5 minutes
    },
}