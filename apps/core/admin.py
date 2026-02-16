"""
Core admin configuration.
"""

from django.contrib import admin
from .models import SyncLog, OfflineCache


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'sync_type', 'status', 'created_at', 'processed_at']
    list_filter = ['sync_type', 'status', 'created_at']
    search_fields = ['user__full_name', 'user__phone_number', 'operation_id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(OfflineCache)
class OfflineCacheAdmin(admin.ModelAdmin):
    list_display = ['user', 'cache_type', 'cache_key', 'size_bytes', 'expires_at']
    list_filter = ['cache_type', 'created_at']
    search_fields = ['user__full_name', 'cache_key']
    readonly_fields = ['created_at', 'updated_at', 'last_accessed_at']
