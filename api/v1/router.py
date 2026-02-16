"""
Main API router - combines all endpoint routers.
"""

from fastapi import APIRouter

from api.v1.endpoints import (
    auth,
    users,
    listings,
    messaging,
    pricing,
    notifications,
    marketplace,
    offline_sync,
)

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(listings.router, prefix="/listings", tags=["Listings"])
api_router.include_router(messaging.router, prefix="/messaging", tags=["Messaging"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["Pricing"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(marketplace.router, prefix="/marketplace", tags=["Marketplace"])
api_router.include_router(offline_sync.router, prefix="/sync", tags=["Offline Sync"])
