"""
Notification service - Send notifications via various channels.
"""

from django.conf import settings
from .models import Notification
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Unified notification service for push, SMS, and email.
    """
    
    @staticmethod
    def send_notification(user, notification_type, title, message, action_url='', extra_data=None):
        """
        Create notification and send via appropriate channels.
        
        Args:
            user: User to notify
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            action_url: Optional action URL
            extra_data: Additional data
        
        Returns:
            Notification instance
        """
        # Create notification in database
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            extra_data=extra_data or {}
        )
        
        # Get user settings
        settings_obj = user.settings
        
        # Send push notification
        if settings_obj.push_notifications:
            NotificationService.send_push_notification(user, title, message, extra_data)
        
        # Send SMS for important notifications
        if settings_obj.sms_notifications and notification_type in ['inquiry', 'order_status']:
            NotificationService.send_sms(user.phone_number, f"{title}: {message}")
        
        # Send email if enabled
        if settings_obj.email_notifications and user.email:
            NotificationService.send_email(user.email, title, message)
        
        return notification
    
    @staticmethod
    def send_push_notification(user, title, message, extra_data=None):
        """Send push notification to user's devices."""
        from apps.users.models import DeviceToken
        
        # Get active device tokens
        device_tokens = DeviceToken.objects.filter(
            user=user,
            is_active=True
        )
        
        for device in device_tokens:
            try:
                if device.device_type in ['ios', 'android']:
                    # Use Firebase Cloud Messaging
                    NotificationService._send_fcm(device.token, title, message, extra_data)
                elif device.device_type == 'web':
                    # Use Web Push
                    NotificationService._send_web_push(device.token, title, message)
            except Exception as e:
                logger.error(f"Failed to send push to device {device.id}: {str(e)}")
    
    @staticmethod
    def _send_fcm(token, title, message, data=None):
        """Send Firebase Cloud Messaging notification."""
        # TODO: Implement FCM integration
        # This is a placeholder - integrate with Firebase Admin SDK
        logger.info(f"FCM: {title} - {message}")
        pass
    
    @staticmethod
    def _send_web_push(token, title, message):
        """Send Web Push notification."""
        # TODO: Implement Web Push
        logger.info(f"Web Push: {title} - {message}")
        pass
    
    @staticmethod
    def send_sms(phone_number, message):
        """
        Send SMS via Twilio.
        
        Args:
            phone_number: Recipient phone number
            message: SMS message text
        """
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.warning("Twilio not configured - SMS not sent")
            return False
        
        try:
            from twilio.rest import Client
            
            client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            
            message_obj = client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            
            logger.info(f"SMS sent to {phone_number}: {message_obj.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
            return False
    
    @staticmethod
    def send_email(email, subject, message):
        """
        Send email.
        
        Args:
            email: Recipient email
            subject: Email subject
            message: Email message
        """
        try:
            from django.core.mail import send_mail
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@villagetomarket.zw',
                recipient_list=[email],
                fail_silently=False,
            )
            
            logger.info(f"Email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {str(e)}")
            return False
    
    @staticmethod
    def mark_all_read(user):
        """Mark all notifications as read for a user."""
        from django.utils import timezone
        
        unread_count = Notification.objects.filter(
            user=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return unread_count
