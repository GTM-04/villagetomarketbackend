"""
Listing endpoints - CRUD operations for produce listings.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from asgiref.sync import sync_to_async
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.listings.models import Listing, ListingImage, ProduceType, Category
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
    available_from: Optional[date] = None
    available_until: Optional[date] = None


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
    @sync_to_async
    def fetch_listings():
        queryset = Listing.objects.select_related('produce_type', 'farmer').filter(status=status)

        if district:
            queryset = queryset.filter(district__iexact=district)
        if produce_type:
            queryset = queryset.filter(produce_type_id=produce_type)

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

    return await fetch_listings()


@router.get("/produce-types", response_model=List[dict])
async def get_produce_types():
    """
    Get all available produce types.
    """
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


@router.post("/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    data: CreateListingRequest,
    current_user: User = Depends(get_current_active_farmer)
):
    """
    Create a new listing (farmers only).
    """
    try:
        produce_type = await sync_to_async(ProduceType.objects.select_related('category').get)(id=data.produce_type_id)
    except ProduceType.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produce type not found"
        )
    
    from datetime import date as date_type, timedelta
    today = date_type.today()
    listing = await sync_to_async(Listing.objects.create)(
        farmer=current_user,
        produce_type=produce_type,
        category=produce_type.category,
        title=f"{produce_type.name} - {getattr(current_user, 'district', '')}",
        quantity_available=data.quantity_available,
        unit=data.unit,
        price_per_unit=data.price_per_unit,
        description=data.description,
        district=getattr(current_user, 'district', ''),
        is_organic=data.is_organic,
        harvest_date=data.harvest_date,
        available_from=data.available_from or today,
        available_until=data.available_until or (today + timedelta(days=30)),
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
    @sync_to_async
    def fetch_listing():
        try:
            listing = Listing.objects.select_related('produce_type').get(id=listing_id)
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
        except Listing.DoesNotExist:
            return None

    result = await fetch_listing()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    return result


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: str,
    current_user: User = Depends(get_current_active_farmer)
):
    """
    Delete a listing (owner only).
    """
    try:
        listing = await sync_to_async(Listing.objects.get)(id=listing_id, farmer=current_user)
    except Listing.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    await sync_to_async(listing.delete)()


@router.post("/{listing_id}/images/", status_code=status.HTTP_201_CREATED)
async def upload_listing_image(
    listing_id: str,
    image: UploadFile = File(...),
    caption: str = Form(""),
    current_user: User = Depends(get_current_active_farmer)
):
    """
    Upload an image for a listing (owner only).
    """
    try:
        listing = await sync_to_async(Listing.objects.get)(id=listing_id, farmer=current_user)
    except Listing.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )

    # Validate content type
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    contents = await image.read()

    def save_image():
        from django.core.files.base import ContentFile
        img = ListingImage(
            listing=listing,
            caption=caption,
        )
        img.image.save(image.filename, ContentFile(contents), save=True)
        return {
            "id": str(img.id),
            "url": img.image.url,
            "caption": img.caption,
            "is_primary": img.is_primary,
        }

    return await sync_to_async(save_image)()
