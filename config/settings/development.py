"""
Development settings for From Village to Market Backend.
Uses SQLite for easier local development.
"""

from .base import *

DEBUG = True

# Database - SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email backend - Console for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Django Debug Toolbar (optional)
try:
    import debug_toolbar
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
except ImportError:
    pass

# Celery - Eager execution for development (tasks run synchronously)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable Elasticsearch in development if not available
try:
    from elasticsearch import Elasticsearch
    es = Elasticsearch([f"http://{os.getenv('ELASTICSEARCH_HOST', 'localhost')}:9200"])
    es.ping()
except:
    ELASTICSEARCH_DSL = {}
    print("[WARNING] Elasticsearch not available - search features disabled")

# Channel Layers - Use in-memory for development (no Redis needed)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

print("[INFO] Running in DEVELOPMENT mode")
