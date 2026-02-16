"""
Core views - Health check and system status.
"""

from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import sys


def health_check(request):
    """
    Simple health check endpoint.
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'From Village to Market Backend',
        'version': '1.0.0',
    })


def system_status(request):
    """
    System status endpoint with database and dependencies check.
    """
    status_data = {
        'status': 'operational',
        'python_version': sys.version,
        'django_version': settings.VERSION if hasattr(settings, 'VERSION') else 'Unknown',
        'database': 'disconnected',
        'redis': 'unknown',
        'celery': 'unknown',
    }
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status_data['database'] = 'connected'
    except Exception as e:
        status_data['database'] = f'error: {str(e)}'
        status_data['status'] = 'degraded'
    
    # Check Redis connectivity
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 30)
        if cache.get('health_check') == 'ok':
            status_data['redis'] = 'connected'
    except Exception as e:
        status_data['redis'] = f'error: {str(e)}'
    
    # Check Celery
    try:
        from config.celery import app
        inspector = app.control.inspect()
        if inspector.active():
            status_data['celery'] = 'running'
        else:
            status_data['celery'] = 'no workers'
    except Exception:
        status_data['celery'] = 'unavailable'
    
    return JsonResponse(status_data)
