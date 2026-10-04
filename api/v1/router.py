"""
Main API router - combines all endpoint routers.
"""

from typing import List
from fastapi import APIRouter
from channels.db import database_sync_to_async as sync_to_async

from api.v1.endpoints import (
    auth,
    users,
    listings,
    messaging,
    pricing,
    notifications,
    marketplace,
    offline_sync,
    payments,
)
from apps.listings.reference_data import ensure_reference_data

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
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])


# Top-level endpoints (commonly used across features)
@api_router.get("/produce-types", response_model=List[dict], tags=["Reference Data"])
async def get_produce_types():
    """
    Get all available produce types (top-level convenience endpoint).
    """
    from apps.listings.models import ProduceType

    await sync_to_async(ensure_reference_data)()
    
    @sync_to_async
    def fetch_produce_types():
        return [
            {
                "id": pt.id,
                "name": pt.name,
                "category": pt.category.name if pt.category else None,
            }
            for pt in ProduceType.objects.select_related('category').all()
        ]
    
    return await fetch_produce_types()
