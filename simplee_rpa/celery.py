import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simplee_rpa.settings')

app = Celery('simplee_rpa', broker=settings.BROKER_URL)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

app.conf.beat_schedule = {
    'check-bidding-list': {
        'task': 'core.tasks.check_bidding_list',
        'schedule': crontab(hour="*/6"),
    },
    'send_to_ac': {
        'task': 'core.tasks.send_biddings_to_active_campaing',
        'schedule': 30,
        # 'schedule': crontab(hour="*/12"),
    },

}