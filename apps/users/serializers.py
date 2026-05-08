"""
User DRF serializers.
"""

from rest_framework import serializers
from .models import User, UserSettings, DeviceToken
from ..core.utils import normalize_phone_number


class UserSettingsSerializer(serializers.ModelSerializer):
    """Serializer for user settings."""
    
    class Meta:
        model = UserSettings
        exclude = ['id', 'user', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    settings = UserSettingsSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'phone_number',
            'email',
            'full_name',
            'user_type',
            'profile_picture',
            'cover_photo',
            'bio',
            'district',
            'location',
            'latitude',
            'longitude',
            'is_verified',
            'phone_verified',
            'is_active',
            'created_at',
            'settings',
        ]
        read_only_fields = ['id', 'is_verified', 'phone_verified', 'created_at']
    
    def validate_phone_number(self, value):
        """Normalize and validate phone number."""
        normalized = normalize_phone_number(value)
        if not normalized:
            raise serializers.ValidationError("Invalid phone number format")
        return normalized


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'phone_number',
            'password',
            'password_confirm',
            'email',
            'full_name',
            'district',
            'location',
        ]
    
    def validate(self, data):
        """Validate password match."""
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({"password": "Passwords must match"})
        return data
    
    def validate_phone_number(self, value):
        """Normalize and validate phone number."""
        normalized = normalize_phone_number(value)
        if not normalized:
            raise serializers.ValidationError("Invalid phone number format")
        return normalized
    
    def create(self, validated_data):
        """Create user with hashed password."""
        password = validated_data.pop('password')
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class DeviceTokenSerializer(serializers.ModelSerializer):
    """Serializer for device tokens."""
    
    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'device_type', 'device_name', 'is_active']
        read_only_fields = ['id']
