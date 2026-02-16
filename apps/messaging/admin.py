"""
Messaging admin configuration.
"""

from django.contrib import admin
from .models import Conversation, Message, MessageAttachment


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'participant_1',
        'participant_2',
        'listing',
        'last_message_at',
        'is_active'
    ]
    list_filter = ['is_active', 'created_at', 'last_message_at']
    search_fields = [
        'participant_1__full_name',
        'participant_2__full_name',
        'listing__title'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'last_message_at',
        'last_message_text',
        'unread_count_p1',
        'unread_count_p2'
    ]
    raw_id_fields = ['participant_1', 'participant_2', 'listing', 'last_message_sender']


class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0
    readonly_fields = ['file_size', 'mime_type']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'sender',
        'conversation',
        'message_type',
        'is_read',
        'created_at'
    ]
    list_filter = ['message_type', 'is_read', 'is_delivered', 'created_at']
    search_fields = ['text', 'sender__full_name']
    readonly_fields = ['created_at', 'read_at', 'delivered_at']
    raw_id_fields = ['conversation', 'sender']
    inlines = [MessageAttachmentInline]


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'message', 'file_size', 'mime_type', 'created_at']
    list_filter = ['mime_type', 'created_at']
    search_fields = ['file_name']
    readonly_fields = ['created_at', 'file_size', 'mime_type']
    raw_id_fields = ['message']
