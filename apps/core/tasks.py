"""
Core Celery tasks.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_sync_logs():
    """
    Clean up sync logs older than 30 days.
    """
    from .models import SyncLog
    
    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_count = SyncLog.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['completed', 'failed']
    ).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} old sync logs")
    return f"Deleted {deleted_count} sync logs"


@shared_task
def cleanup_expired_cache():
    """
    Clean up expired offline cache entries.
    """
    from .models import OfflineCache
    
    deleted_count = OfflineCache.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} expired cache entries")
    return f"Deleted {deleted_count} cache entries"
