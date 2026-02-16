"""
User admin configuration.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserSettings, DeviceToken, PhoneVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom user admin.
    """
    list_display = [
        'phone_number',
        'full_name',
        'user_type',
        'district',
        'is_verified',
        'is_active',
        'created_at'
    ]
    list_filter = [
        'user_type',
        'is_verified',
        'is_active',
        'district',
        'created_at'
    ]
    search_fields = ['phone_number', 'full_name', 'email']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal Info', {
            'fields': (
                'full_name',
                'email',
                'bio',
                'profile_picture',
                'cover_photo'
            )
        }),
        ('User Type', {'fields': ('user_type',)}),
        ('Location', {
            'fields': ('district', 'location', 'latitude', 'longitude')
        }),
        ('Verification', {
            'fields': ('is_verified', 'phone_verified', 'phone_verified_at')
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        ('Important dates', {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'phone_number',
                'full_name',
                'user_type',
                'district',
                'password1',
                'password2'
            ),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login']


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'language',
        'push_notifications',
        'sms_notifications',
        'sync_frequency'
    ]
    list_filter = ['language', 'push_notifications', 'sync_frequency']
    search_fields = ['user__full_name', 'user__phone_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_type', 'device_name', 'is_active', 'last_used']
    list_filter = ['device_type', 'is_active', 'created_at']
    search_fields = ['user__full_name', 'user__phone_number', 'token']
    readonly_fields = ['created_at', 'updated_at', 'last_used']


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = [
        'phone_number',
        'code',
        'is_verified',
        'attempts',
        'expires_at',
        'created_at'
    ]
    list_filter = ['is_verified', 'created_at']
    search_fields = ['phone_number', 'code']
    readonly_fields = ['created_at', 'updated_at']
