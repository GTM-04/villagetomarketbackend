"""
Messaging models - Conversations and messages.
"""

from django.db import models
from apps.core.models import TimestampedModel, UUIDModel
from apps.users.models import User


class Conversation(UUIDModel, TimestampedModel):
    """
    Chat conversation between two users.
    """
    # Participants
    participant_1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_p1'
    )
    participant_2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_p2'
    )
    
    # Related listing (optional - conversation might be about a listing)
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Last message info (denormalized for performance)
    last_message_at = models.DateTimeField(null=True, blank=True)
    last_message_text = models.TextField(blank=True)
    last_message_sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    
    # Unread counts
    unread_count_p1 = models.IntegerField(default=0)
    unread_count_p2 = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'conversations'
        unique_together = [
            ['participant_1', 'participant_2', 'listing']
        ]
        indexes = [
            models.Index(fields=['participant_1', '-last_message_at']),
            models.Index(fields=['participant_2', '-last_message_at']),
            models.Index(fields=['listing']),
        ]
        ordering = ['-last_message_at', '-created_at']
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
    
    def __str__(self):
        return f"Conversation between {self.participant_1.full_name} and {self.participant_2.full_name}"
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation."""
        if user == self.participant_1:
            return self.participant_2
        return self.participant_1
    
    def get_unread_count(self, user):
        """Get unread count for a specific user."""
        if user == self.participant_1:
            return self.unread_count_p1
        return self.unread_count_p2
    
    def mark_read(self, user):
        """Mark conversation as read for a user."""
        if user == self.participant_1:
            self.unread_count_p1 = 0
        else:
            self.unread_count_p2 = 0
        self.save(update_fields=['unread_count_p1' if user == self.participant_1 else 'unread_count_p2'])


class Message(UUIDModel, TimestampedModel):
    """
    Individual message in a conversation.
    """
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('location', 'Location'),
        ('system', 'System'),
    ]
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    
    # Message content
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default='text'
    )
    text = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='messages/%Y/%m/',
        null=True,
        blank=True
    )
    
    # Location data
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Offline sync
    client_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Client-side message ID for offline sync"
    )
    
    class Meta:
        db_table = 'messages'
        indexes = [
            models.Index(fields=['conversation', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
        ]
        ordering = ['created_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
    
    def __str__(self):
        return f"Message from {self.sender.full_name} at {self.created_at}"
    
    def save(self, *args, **kwargs):
        """Update conversation when message is saved."""
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new:
            # Update conversation
            self.conversation.last_message_at = self.created_at
            self.conversation.last_message_text = self.text[:100]
            self.conversation.last_message_sender = self.sender
            
            # Increment unread count for receiver
            if self.sender == self.conversation.participant_1:
                self.conversation.unread_count_p2 += 1
            else:
                self.conversation.unread_count_p1 += 1
            
            self.conversation.save()
    
    def mark_as_read(self):
        """Mark message as read."""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class MessageAttachment(UUIDModel, TimestampedModel):
    """
    File attachments for messages.
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='message_attachments/%Y/%m/')
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text="Size in bytes")
    mime_type = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'message_attachments'
        verbose_name = 'Message Attachment'
        verbose_name_plural = 'Message Attachments'
    
    def __str__(self):
        return f"Attachment: {self.file_name}"
