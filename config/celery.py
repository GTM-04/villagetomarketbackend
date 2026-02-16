"""
Celery configuration for From Village to Market Backend.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('from_village_to_market')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'update-market-prices-daily': {
        'task': 'apps.pricing.tasks.update_market_prices',
        'schedule': crontab(hour=6, minute=0),  # 6 AM daily
    },
    'calculate-price-trends-weekly': {
        'task': 'apps.pricing.tasks.calculate_price_trends',
        'schedule': crontab(day_of_week=1, hour=7, minute=0),  # Monday 7 AM
    },
    'expire-old-listings-daily': {
        'task': 'apps.listings.tasks.expire_old_listings',
        'schedule': crontab(hour=1, minute=0),  # 1 AM daily
    },
    'send-weekly-market-report': {
        'task': 'apps.notifications.tasks.send_weekly_market_report',
        'schedule': crontab(day_of_week=0, hour=8, minute=0),  # Sunday 8 AM
    },
    'check-price-alerts-hourly': {
        'task': 'apps.pricing.tasks.send_price_alerts',
        'schedule': crontab(minute=0),  # Every hour
    },
    'cleanup-old-sync-logs': {
        'task': 'apps.core.tasks.cleanup_old_sync_logs',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Sunday 2 AM
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
