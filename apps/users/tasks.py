"""
User Celery tasks - Background tasks for user-related operations.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_welcome_sms(user_id):
    """
    Send welcome SMS to new user.
    """
    from .models import User
    from apps.notifications.services import NotificationService
    
    try:
        user = User.objects.get(id=user_id)
        message = f"Welcome to Village to Market, {user.full_name}! Your account has been created successfully."
        
        # Send SMS via Twilio
        NotificationService.send_sms(
            phone_number=user.phone_number,
            message=message
        )
        
        logger.info(f"Welcome SMS sent to {user.phone_number}")
        return f"SMS sent to {user.phone_number}"
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found")
        return "User not found"


@shared_task
def cleanup_expired_verifications():
    """
    Clean up expired phone verifications.
    """
    from .models import PhoneVerification
    
    deleted_count = PhoneVerification.objects.filter(
        expires_at__lt=timezone.now(),
        is_verified=False
    ).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} expired phone verifications")
    return f"Deleted {deleted_count} verifications"


@shared_task
def cleanup_inactive_device_tokens():
    """
    Clean up device tokens that haven't been used in 90 days.
    """
    from .models import DeviceToken
    
    cutoff_date = timezone.now() - timedelta(days=90)
    deleted_count = DeviceToken.objects.filter(
        last_used__lt=cutoff_date
    ).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} inactive device tokens")
    return f"Deleted {deleted_count} tokens"
