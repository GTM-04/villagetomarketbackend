"""
Notification models.
"""

from django.db import models
from apps.core.models import TimestampedModel, UUIDModel
from apps.users.models import User


class Notification(UUIDModel, TimestampedModel):
    """
    User notifications.
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('new_message', 'New Message'),
        ('new_listing', 'New Listing'),
        ('price_alert', 'Price Alert'),
        ('inquiry', 'Inquiry'),
        ('order_status', 'Order Status'),
        ('system', 'System'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Action
    action_url = models.CharField(max_length=500, blank=True)
    action_text = models.CharField(max_length=100, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    extra_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.notification_type} - {self.user.full_name}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
