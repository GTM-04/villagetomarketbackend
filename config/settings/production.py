"""
Production settings for From Village to Market Backend.
Uses PostgreSQL and enhanced security settings.
"""

from .base import *
import dj_database_url

DEBUG = False

# Use environment variable for allowed hosts
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# Database - PostgreSQL for production
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Email backend - Use actual email service
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = True

# ── Media / File Storage ──────────────────────────────────────────────────────
# Railway has an ephemeral filesystem — files are wiped on every redeploy.
# We use Cloudinary (free tier) so uploaded images persist permanently.
# Set CLOUDINARY_URL in Railway env vars:  cloudinary://api_key:api_secret@cloud_name
if os.getenv('CLOUDINARY_URL'):
    import cloudinary
    cloudinary.config(cloudinary_url=os.getenv('CLOUDINARY_URL'))
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    # Cloudinary returns absolute CDN URLs, so MEDIA_URL can be left as-is.
    MEDIA_URL = '/media/'   # kept for compatibility; not used for serving

elif os.getenv('AWS_ACCESS_KEY_ID'):
    # Fallback: S3-compatible storage (existing config)
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
# else: local filesystem (ephemeral on Railway — images lost on redeploy)

# Sentry error tracking
if os.getenv('SENTRY_DSN'):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
    )

# Logging - More comprehensive in production
# We remove the file handler in production since Railway handles stdout logs.
# This prevents FileNotFoundError for /var/log paths.
if 'file' in LOGGING['handlers']:
    del LOGGING['handlers']['file']
LOGGING['root']['handlers'] = ['console']
LOGGING['loggers']['django']['handlers'] = ['console']
LOGGING['loggers']['apps']['handlers'] = ['console']

LOGGING['root']['level'] = 'WARNING'
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['apps']['level'] = 'INFO'

print("Running in PRODUCTION mode")
