"""
Core URL patterns - Health check and system status.
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.health_check, name='health_check'),
    path('status/', views.system_status, name='system_status'),
]
