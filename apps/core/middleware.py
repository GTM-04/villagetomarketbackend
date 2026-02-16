"""
Core middleware.
"""

import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log request information and timing.
    """
    
    def process_request(self, request):
        """Start timer for request."""
        request.start_time = time.time()
    
    def process_response(self, request, response):
        """Log request details."""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log slow requests (> 1 second)
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s - Status: {response.status_code}"
                )
            
            # Add timing header
            response['X-Request-Duration'] = f"{duration:.3f}s"
        
        return response
