"""
ASGI config for From Village to Market Backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
from urllib.parse import parse_qs

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.db import database_sync_to_async
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM model.
django_asgi_app = get_asgi_application()

# Safe to import Django auth models only AFTER get_asgi_application()
from django.contrib.auth.models import AnonymousUser

# Import FastAPI app
from api.main import app as fastapi_app

# Import WebSocket routing
from apps.messaging.routing import websocket_urlpatterns


@database_sync_to_async
def _get_user_from_jwt(token: str):
    """Decode a JWT access token and return the corresponding User or AnonymousUser."""
    from apps.users.models import User
    from api.core.security import decode_token
    from fastapi import HTTPException
    try:
        payload = decode_token(token)
        user_id = payload.get('sub')
        if not user_id:
            return AnonymousUser()
        return User.objects.get(id=user_id)
    except (HTTPException, User.DoesNotExist, Exception):
        return AnonymousUser()


class JWTAuthMiddleware:
    """
    Channels middleware that authenticates WebSocket connections using a JWT
    token passed as the ``token`` query-string parameter.
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'websocket':
            query_string = scope.get('query_string', b'').decode()
            params = parse_qs(query_string)
            token_list = params.get('token', [])
            if token_list:
                scope['user'] = await _get_user_from_jwt(token_list[0])
            else:
                scope['user'] = AnonymousUser()
        return await self.inner(scope, receive, send)


async def http_router(scope, receive, send):
    """Route HTTP requests between Django and FastAPI based on path."""
    if scope["type"] == "http":
        path = scope.get("path", "")
        # Route /api/* and /media/* to FastAPI
        # - /api/*   → FastAPI handles all REST endpoints
        # - /media/* → FastAPI has a StaticFiles mount that serves from
        #              Django's MEDIA_ROOT (supports Railway volumes and
        #              local dev).  Django only serves media when DEBUG=True,
        #              so we must route through FastAPI for production.
        if path.startswith("/api/") or path.startswith("/media/"):
            await fastapi_app(scope, receive, send)
        else:
            # All other paths go to Django (admin, health, etc.)
            await django_asgi_app(scope, receive, send)
    else:
        # Non-HTTP requests go to Django
        await django_asgi_app(scope, receive, send)


application = ProtocolTypeRouter({
    "http": http_router,
    "websocket": JWTAuthMiddleware(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
