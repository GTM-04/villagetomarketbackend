"""
User models - Custom user with phone authentication.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator
from apps.core.models import TimestampedModel
from apps.core.validators import validate_zimbabwe_phone_number


class UserManager(BaseUserManager):
    """
    Custom user manager for phone-based authentication.
    """
    
    def create_user(self, phone_number, password=None, **extra_fields):
        """
        Create and save a User with the given phone number and password.
        """
        if not phone_number:
            raise ValueError('Users must have a phone number')
        
        extra_fields.setdefault('is_active', True)
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given phone number and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')
        extra_fields.setdefault('full_name', 'Admin User')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractUser, TimestampedModel):
    """
    Custom user model with phone-based authentication.
    Zimbabwe-specific phone number format: +263...
    """
    USER_TYPE_CHOICES = [
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
        ('admin', 'Admin'),
    ]
    
    # Override username to make it optional
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    
    # Phone number as primary identifier
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_zimbabwe_phone_number],
        help_text="Zimbabwe phone number format: +263..."
    )
    
    # Email is optional
    email = models.EmailField(blank=True, null=True)
    
    # User type
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='farmer')
    
    # Profile fields
    full_name = models.CharField(max_length=255)
    profile_picture = models.ImageField(
        upload_to='profiles/%Y/%m/',
        blank=True,
        null=True
    )
    cover_photo = models.ImageField(
        upload_to='covers/%Y/%m/',
        blank=True,
        null=True
    )
    bio = models.TextField(blank=True, max_length=500)
    
    # Location
    district = models.CharField(max_length=100)
    location = models.CharField(max_length=255, blank=True)
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
    
    # Verification status
    is_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Security
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Set phone_number as the username field
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name', 'district']
    
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['user_type']),
            models.Index(fields=['district']),
            models.Index(fields=['is_active', 'user_type']),
        ]
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"
    
    def save(self, *args, **kwargs):
        # Auto-generate username from phone if not provided
        if not self.username:
            self.username = self.phone_number
        super().save(*args, **kwargs)
    
    @property
    def is_farmer(self):
        return self.user_type == 'farmer'
    
    @property
    def is_buyer(self):
        return self.user_type == 'buyer'
    
    @property
    def display_name(self):
        return self.full_name or self.phone_number


class UserSettings(TimestampedModel):
    """
    User preferences and settings.
    """
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('sn', 'Shona'),
        ('nd', 'Ndebele'),
    ]
    
    SYNC_FREQUENCY_CHOICES = [
        ('realtime', 'Real-time'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    
    # Notification preferences
    push_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=False)
    
    # Specific notification types
    notify_new_messages = models.BooleanField(default=True)
    notify_price_alerts = models.BooleanField(default=True)
    notify_new_listings = models.BooleanField(default=True)
    notify_inquiries = models.BooleanField(default=True)
    notify_order_status = models.BooleanField(default=True)
    
    # Language
    language = models.CharField(
        max_length=10,
        default='en',
        choices=LANGUAGE_CHOICES
    )
    
    # Sync settings
    sync_on_wifi_only = models.BooleanField(default=True)
    sync_frequency = models.CharField(
        max_length=20,
        default='realtime',
        choices=SYNC_FREQUENCY_CHOICES
    )
    
    # Privacy settings
    show_phone_number = models.BooleanField(default=False)
    show_location = models.BooleanField(default=True)
    allow_messages_from_anyone = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_settings'
        verbose_name = 'User Settings'
        verbose_name_plural = 'User Settings'
    
    def __str__(self):
        return f"Settings for {self.user.full_name}"


class DeviceToken(TimestampedModel):
    """
    Store device tokens for push notifications.
    """
    DEVICE_TYPE_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='device_tokens'
    )
    token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPE_CHOICES)
    device_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'device_tokens'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token']),
        ]
        verbose_name = 'Device Token'
        verbose_name_plural = 'Device Tokens'
    
    def __str__(self):
        return f"{self.device_type} - {self.user.full_name}"


class PhoneVerification(TimestampedModel):
    """
    Store phone verification codes.
    """
    phone_number = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'phone_verifications'
        indexes = [
            models.Index(fields=['phone_number', 'code']),
            models.Index(fields=['expires_at']),
        ]
        verbose_name = 'Phone Verification'
        verbose_name_plural = 'Phone Verifications'
    
    def __str__(self):
        return f"{self.phone_number} - {'Verified' if self.is_verified else 'Pending'}"
