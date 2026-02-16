"""
Core models - Base models and mixins for all apps.
"""

from django.db import models
from django.utils import timezone
import uuid


class TimestampedModel(models.Model):
    """
    Abstract base class with created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    Abstract base class with UUID primary key.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract base class for soft delete functionality.
    """
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete the object."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def hard_delete(self):
        """Permanently delete the object."""
        super().delete()


class SyncLog(TimestampedModel):
    """
    Track offline sync operations.
    """
    SYNC_TYPE_CHOICES = [
        ('listing_create', 'Create Listing'),
        ('listing_update', 'Update Listing'),
        ('message_send', 'Send Message'),
        ('profile_update', 'Update Profile'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='sync_logs')
    sync_type = models.CharField(max_length=30, choices=SYNC_TYPE_CHOICES)
    operation_id = models.CharField(max_length=100, help_text="Client-side operation ID")
    payload = models.JSONField(help_text="Data to be synced")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'sync_logs'
        indexes = [
            models.Index(fields=['user', 'status', '-created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sync_type} - {self.status} - {self.user}"


class OfflineCache(TimestampedModel):
    """
    Track what data is cached for offline access.
    """
    CACHE_TYPE_CHOICES = [
        ('listings', 'Listings'),
        ('messages', 'Messages'),
        ('prices', 'Market Prices'),
        ('profile', 'Profile Data'),
    ]
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='offline_cache')
    cache_key = models.CharField(max_length=255)
    cache_type = models.CharField(max_length=50, choices=CACHE_TYPE_CHOICES)
    data_hash = models.CharField(max_length=64, help_text="Hash of cached data for validation")
    size_bytes = models.BigIntegerField(default=0)
    expires_at = models.DateTimeField()
    last_accessed_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'offline_cache'
        unique_together = ['user', 'cache_key']
        ordering = ['-last_accessed_at']
    
    def __str__(self):
        return f"{self.cache_type} - {self.user}"
