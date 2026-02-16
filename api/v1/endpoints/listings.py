"""
Listing endpoints - CRUD operations for produce listings.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.listings.models import Listing, ProduceType, Category
from apps.users.models import User
from api.core.security import get_current_user, get_current_active_farmer

router = APIRouter()


# Pydantic models
class ListingResponse(BaseModel):
    id: str
    title: str
    produce_type: dict
    quantity_available: float
    unit: str
    price_per_unit: float
    currency: str
    district: str
    status: str
    is_organic: bool
    harvest_date: Optional[date]
    images: List[str] = []


class CreateListingRequest(BaseModel):
    produce_type_id: int
    quantity_available: float = Field(..., gt=0)
    unit: str
    price_per_unit: float = Field(..., gt=0)
    description: str
    is_organic: bool = False
    harvest_date: Optional[date] = None


@router.get("/", response_model=List[ListingResponse])
async def list_listings(
    district: Optional[str] = None,
    produce_type: Optional[int] = None,
    status: str = "active",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    List all active listings with optional filters.
    """
    from django.db.models import Q
    
    queryset = Listing.objects.select_related('produce_type', 'farmer').filter(status=status)
    
    if district:
        queryset = queryset.filter(district__iexact=district)
    if produce_type:
        queryset = queryset.filter(produce_type_id=produce_type)
    
    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    listings = queryset[start:end]
    
    return [
        {
            "id": str(listing.id),
            "title": listing.title,
            "produce_type": {
                "id": listing.produce_type.id,
                "name": listing.produce_type.name,
            },
            "quantity_available": float(listing.quantity_available),
            "unit": listing.unit,
            "price_per_unit": float(listing.price_per_unit),
            "currency": listing.currency,
            "district": listing.district,
            "status": listing.status,
            "is_organic": listing.is_organic,
            "harvest_date": listing.harvest_date,
            "images": [img.image.url for img in listing.images.all()],
        }
        for listing in listings
    ]


@router.post("/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    data: CreateListingRequest,
    current_user: User = Depends(get_current_active_farmer)
):
    """
    Create a new listing (farmers only).
    """
    try:
        produce_type = ProduceType.objects.get(id=data.produce_type_id)
    except ProduceType.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produce type not found"
        )
    
    listing = Listing.objects.create(
        farmer=current_user,
        produce_type=produce_type,
        title=f"{produce_type.name} - {current_user.district}",
        quantity_available=data.quantity_available,
        unit=data.unit,
        price_per_unit=data.price_per_unit,
        description=data.description,
        district=current_user.district,
        ward=current_user.ward,
        is_organic=data.is_organic,
        harvest_date=data.harvest_date,
        status='active',
    )
    
    return {
        "id": str(listing.id),
        "title": listing.title,
        "produce_type": {
            "id": listing.produce_type.id,
            "name": listing.produce_type.name,
        },
        "quantity_available": float(listing.quantity_available),
        "unit": listing.unit,
        "price_per_unit": float(listing.price_per_unit),
        "currency": listing.currency,
        "district": listing.district,
        "status": listing.status,
        "is_organic": listing.is_organic,
        "harvest_date": listing.harvest_date,
        "images": [],
    }


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: str):
    """
    Get a specific listing by ID.
    """
    try:
        listing = Listing.objects.select_related('produce_type').get(id=listing_id)
    except Listing.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    return {
        "id": str(listing.id),
        "title": listing.title,
        "produce_type": {
            "id": listing.produce_type.id,
            "name": listing.produce_type.name,
        },
        "quantity_available": float(listing.quantity_available),
        "unit": listing.unit,
        "price_per_unit": float(listing.price_per_unit),
        "currency": listing.currency,
        "district": listing.district,
        "status": listing.status,
        "is_organic": listing.is_organic,
        "harvest_date": listing.harvest_date,
        "images": [img.image.url for img in listing.images.all()],
    }


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: str,
    current_user: User = Depends(get_current_active_farmer)
):
    """
    Delete a listing (owner only).
    """
    try:
        listing = Listing.objects.get(id=listing_id, farmer=current_user)
    except Listing.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    listing.delete()
