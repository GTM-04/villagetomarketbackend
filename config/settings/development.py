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
import socket as _socket

def _es_is_reachable(host: str = 'localhost', port: int = 9200, timeout: float = 0.5) -> bool:
    """Fast socket probe — returns False instantly when ES is not running."""
    try:
        with _socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ConnectionRefusedError):
        return False

_es_host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
_es_port = int(os.getenv('ELASTICSEARCH_PORT', '9200'))

if not _es_is_reachable(_es_host, _es_port):
    ELASTICSEARCH_DSL = {}
    print("[INFO] Elasticsearch not available — search features disabled (skipped)")

# Channel Layers - Use in-memory for development (no Redis needed)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

print("[INFO] Running in DEVELOPMENT mode")
