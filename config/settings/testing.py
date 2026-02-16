"""
Test settings for From Village to Market Backend.
Optimized for fast test execution.
"""

from .base import *

DEBUG = True

# Use in-memory SQLite for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable password hashing for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use simple email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Use file-based cache for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Disable Celery in tests - run synchronously
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable channel layers in tests
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# Disable Elasticsearch in tests
ELASTICSEARCH_DSL = {}

# Disable Twilio in tests
TWILIO_ACCOUNT_SID = 'test_sid'
TWILIO_AUTH_TOKEN = 'test_token'
TWILIO_PHONE_NUMBER = '+1234567890'

# Disable Firebase in tests
FIREBASE_SERVER_KEY = 'test_key'

# Simple logging for tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'ERROR',
    },
}

print("🧪 Running in TEST mode")
