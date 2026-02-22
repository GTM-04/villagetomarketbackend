"""
ASGI config for From Village to Market Backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import FastAPI app
from api.main import app as fastapi_app

# Import WebSocket routing
from apps.messaging.routing import websocket_urlpatterns


async def http_router(scope, receive, send):
    """Route HTTP requests between Django and FastAPI based on path."""
    if scope["type"] == "http":
        path = scope.get("path", "")
        # Route /api/* to FastAPI (handles /api/docs, /api/v1/*, etc.)
        if path.startswith("/api/"):
            await fastapi_app(scope, receive, send)
        else:
            # All other paths go to Django
            await django_asgi_app(scope, receive, send)
    else:
        # Non-HTTP requests go to Django
        await django_asgi_app(scope, receive, send)


application = ProtocolTypeRouter({
    "http": http_router,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
