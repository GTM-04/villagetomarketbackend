"""
URL configuration for From Village to Market Backend project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # API v1 (Django REST Framework)
    # path('api/v1/', include('apps.users.urls')),
    # path('api/v1/', include('apps.listings.urls')),
    # path('api/v1/', include('apps.messaging.urls')),
    # path('api/v1/', include('apps.pricing.urls')),
    
    # Health check endpoint
    path('health/', include('apps.core.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    except ImportError:
        pass

# Customize admin site
admin.site.site_header = "From Village to Market Admin"
admin.site.site_title = "Village to Market Admin Portal"
admin.site.index_title = "Welcome to Village to Market Administration"
