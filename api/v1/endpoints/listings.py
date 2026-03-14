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
from django.db.models import Q

router = APIRouter()


# Pydantic models
class ListingResponse(BaseModel):
    id: str
    listing_number: str = ""
    title: str
    description: str = ""
    produce_type: dict
    category: dict = {}
    variety: str = ""
    grade: str = ""
    quality_tags: List[str] = []
    quantity_available: float
    unit: str
    minimum_order: Optional[float] = None
    price_per_unit: float
    currency: str
    district: str
    farm_location: str = ""
    status: str
    is_organic: bool
    is_negotiable: bool = False
    delivery_available: bool = False
    delivery_radius_km: Optional[int] = None
    pickup_available: bool = True
    harvest_date: Optional[date]
    available_from: Optional[date] = None
    available_until: Optional[date] = None
    view_count: int = 0
    inquiry_count: int = 0
    images: List[dict] = []
    farmer: dict = {}


class UpdateListingRequest(BaseModel):
    produce_type_id: Optional[int] = None
    quantity_available: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = None
    price_per_unit: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    is_organic: Optional[bool] = None
    is_negotiable: Optional[bool] = None
    delivery_available: Optional[bool] = None
    pickup_available: Optional[bool] = None
    delivery_radius_km: Optional[int] = None
    harvest_date: Optional[date] = None
    available_from: Optional[date] = None
    available_until: Optional[date] = None
    district: Optional[str] = None
    districtName: Optional[str] = None
    farm_location: Optional[str] = None
    status: Optional[str] = None
    grade: Optional[str] = None
    variety: Optional[str] = None
    minimum_order: Optional[float] = None

    def resolved_district(self) -> Optional[str]:
        return self.district or self.districtName or None


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
    # Frontend may send district as 'district' or 'districtName'
    district: Optional[str] = None
    districtName: Optional[str] = None
    # Optional extra fields sent by frontend
    negotiable: bool = False
    deliveryAvailable: bool = False
    produceName: Optional[str] = None
    categoryName: Optional[str] = None

    def resolved_district(self) -> str:
        """Return the district from whichever field was supplied."""
        return self.district or self.districtName or ""


@router.get("/", response_model=List[ListingResponse])
async def list_listings(
    district: Optional[str] = None,
    produce_type: Optional[int] = None,
    q: Optional[str] = None,
    status: str = "active",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    List all active listings with optional filters.
    """
    @sync_to_async
    def fetch_listings():
        queryset = Listing.objects.select_related(
            'produce_type', 'produce_type__category', 'category', 'farmer'
        ).filter(status=status)

        if district:
            queryset = queryset.filter(district__iexact=district)
        if produce_type:
            queryset = queryset.filter(produce_type_id=produce_type)
        if q:
            query = q.strip()
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(district__icontains=query)
                | Q(produce_type__name__icontains=query)
                | Q(farmer__full_name__icontains=query)
            )

        start = (page - 1) * page_size
        end = start + page_size
        listings = queryset[start:end]

        return [
            {
                "id": str(listing.id),
                "listing_number": listing.listing_number,
                "title": listing.title,
                "description": listing.description,
                "produce_type": {
                    "id": listing.produce_type.id,
                    "name": listing.produce_type.name,
                    "slug": listing.produce_type.slug,
                },
                "category": {
                    "id": listing.category.id,
                    "name": listing.category.name,
                    "slug": listing.category.slug,
                },
                "variety": listing.variety,
                "grade": listing.grade,
                "quality_tags": listing.quality_tags or [],
                "quantity_available": float(listing.quantity_available),
                "unit": listing.unit,
                "minimum_order": float(listing.minimum_order) if listing.minimum_order else None,
                "price_per_unit": float(listing.price_per_unit),
                "currency": listing.currency,
                "district": listing.district,
                "farm_location": listing.farm_location,
                "status": listing.status,
                "is_organic": listing.is_organic,
                "is_negotiable": listing.is_negotiable,
                "delivery_available": listing.delivery_available,
                "delivery_radius_km": listing.delivery_radius_km,
                "pickup_available": listing.pickup_available,
                "harvest_date": listing.harvest_date,
                "available_from": listing.available_from,
                "available_until": listing.available_until,
                "view_count": listing.view_count,
                "inquiry_count": listing.inquiry_count,
                "images": [
                    {
                        "id": str(img.id),
                        "url": img.image.url,
                        "caption": img.caption,
                        "is_primary": img.is_primary,
                        "order": img.order,
                    }
                    for img in listing.images.all()
                ],
                "farmer": {
                    "id": listing.farmer.id,
                    "name": listing.farmer.full_name,
                    "district": listing.farmer.district,
                    "is_verified": listing.farmer.is_verified,
                    "profile_picture": listing.farmer.profile_picture.url if listing.farmer.profile_picture else None,
                },
            }
            for listing in listings
        ]

    return await fetch_listings()


@router.get("/my-listings", response_model=List[ListingResponse])
async def my_listings(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_farmer),
):
    """
    Return only the listings that belong to the currently authenticated farmer.
    """
    @sync_to_async
    def fetch_my_listings():
        queryset = Listing.objects.select_related(
            'produce_type', 'produce_type__category', 'category', 'farmer'
        ).filter(farmer=current_user)

        if status:
            queryset = queryset.filter(status=status)

        start = (page - 1) * page_size
        end = start + page_size
        listings = queryset.order_by('-created_at')[start:end]

        return [
            {
                "id": str(listing.id),
                "listing_number": listing.listing_number,
                "title": listing.title,
                "description": listing.description,
                "produce_type": {
                    "id": listing.produce_type.id,
                    "name": listing.produce_type.name,
                    "slug": listing.produce_type.slug,
                },
                "category": {
                    "id": listing.category.id,
                    "name": listing.category.name,
                    "slug": listing.category.slug,
                } if listing.category else {},
                "variety": listing.variety,
                "grade": listing.grade,
                "quality_tags": listing.quality_tags or [],
                "quantity_available": float(listing.quantity_available),
                "unit": listing.unit,
                "minimum_order": float(listing.minimum_order) if listing.minimum_order else None,
                "price_per_unit": float(listing.price_per_unit),
                "currency": listing.currency,
                "district": listing.district,
                "farm_location": listing.farm_location,
                "status": listing.status,
                "is_organic": listing.is_organic,
                "is_negotiable": listing.is_negotiable,
                "delivery_available": listing.delivery_available,
                "delivery_radius_km": listing.delivery_radius_km,
                "pickup_available": listing.pickup_available,
                "harvest_date": listing.harvest_date,
                "available_from": listing.available_from,
                "available_until": listing.available_until,
                "view_count": listing.view_count,
                "inquiry_count": listing.inquiry_count,
                "images": [
                    {
                        "id": str(img.id),
                        "url": img.image.url,
                        "caption": img.caption,
                        "is_primary": img.is_primary,
                        "order": img.order,
                    }
                    for img in listing.images.all()
                ],
                "farmer": {
                    "id": listing.farmer.id,
                    "name": listing.farmer.full_name,
                    "district": listing.farmer.district,
                    "is_verified": listing.farmer.is_verified,
                    "profile_picture": listing.farmer.profile_picture.url if listing.farmer.profile_picture else None,
                },
            }
            for listing in listings
        ]

    return await fetch_my_listings()


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
    # Use district from payload; fall back to farmer's profile district
    district = data.resolved_district() or getattr(current_user, 'district', '')
    listing = await sync_to_async(Listing.objects.create)(
        farmer=current_user,
        produce_type=produce_type,
        category=produce_type.category,
        title=f"{produce_type.name} - {district}",
        quantity_available=data.quantity_available,
        unit=data.unit,
        price_per_unit=data.price_per_unit,
        description=data.description,
        district=district,
        is_organic=data.is_organic,
        is_negotiable=data.negotiable,
        delivery_available=data.deliveryAvailable,
        harvest_date=data.harvest_date,
        available_from=data.available_from or today,
        available_until=data.available_until or (today + timedelta(days=30)),
        status='active',
    )
    
    return {
        "id": str(listing.id),
        "listing_number": listing.listing_number,
        "title": listing.title,
        "description": listing.description,
        "produce_type": {
            "id": listing.produce_type.id,
            "name": listing.produce_type.name,
            "slug": listing.produce_type.slug,
        },
        "category": {
            "id": listing.category.id,
            "name": listing.category.name,
            "slug": listing.category.slug,
        },
        "variety": listing.variety,
        "grade": listing.grade,
        "quality_tags": listing.quality_tags or [],
        "quantity_available": float(listing.quantity_available),
        "unit": listing.unit,
        "minimum_order": None,
        "price_per_unit": float(listing.price_per_unit),
        "currency": listing.currency,
        "district": listing.district,
        "farm_location": listing.farm_location,
        "status": listing.status,
        "is_organic": listing.is_organic,
        "is_negotiable": listing.is_negotiable,
        "delivery_available": listing.delivery_available,
        "delivery_radius_km": listing.delivery_radius_km,
        "pickup_available": listing.pickup_available,
        "harvest_date": listing.harvest_date,
        "available_from": listing.available_from,
        "available_until": listing.available_until,
        "view_count": 0,
        "inquiry_count": 0,
        "images": [],
        "farmer": {
            "id": current_user.id,
            "name": current_user.full_name,
            "district": current_user.district,
            "is_verified": current_user.is_verified,
            "profile_picture": current_user.profile_picture.url if current_user.profile_picture else None,
        },
    }


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: str):
    """
    Get a specific listing by ID — full detail view.
    """
    import uuid as _uuid
    try:
        _uuid.UUID(listing_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )

    @sync_to_async
    def fetch_listing():
        try:
            listing = Listing.objects.select_related(
                'produce_type', 'produce_type__category', 'category', 'farmer'
            ).get(id=listing_id)

            # Increment view count
            Listing.objects.filter(id=listing_id).update(view_count=listing.view_count + 1)

            farmer = listing.farmer
            farmer_picture = None
            if farmer.profile_picture:
                try:
                    farmer_picture = farmer.profile_picture.url
                except Exception:
                    farmer_picture = None

            return {
                "id": str(listing.id),
                "listing_number": listing.listing_number,
                "title": listing.title,
                "description": listing.description,
                "produce_type": {
                    "id": listing.produce_type.id,
                    "name": listing.produce_type.name,
                    "slug": listing.produce_type.slug,
                },
                "category": {
                    "id": listing.category.id,
                    "name": listing.category.name,
                    "slug": listing.category.slug,
                },
                "variety": listing.variety,
                "grade": listing.grade,
                "quality_tags": listing.quality_tags or [],
                "quantity_available": float(listing.quantity_available),
                "unit": listing.unit,
                "minimum_order": float(listing.minimum_order) if listing.minimum_order else None,
                "price_per_unit": float(listing.price_per_unit),
                "currency": listing.currency,
                "district": listing.district,
                "farm_location": listing.farm_location,
                "status": listing.status,
                "is_organic": listing.is_organic,
                "is_negotiable": listing.is_negotiable,
                "delivery_available": listing.delivery_available,
                "delivery_radius_km": listing.delivery_radius_km,
                "pickup_available": listing.pickup_available,
                "harvest_date": listing.harvest_date,
                "available_from": listing.available_from,
                "available_until": listing.available_until,
                "view_count": listing.view_count + 1,
                "inquiry_count": listing.inquiry_count,
                "images": [
                    {
                        "id": str(img.id),
                        "url": img.image.url,
                        "caption": img.caption,
                        "is_primary": img.is_primary,
                        "order": img.order,
                    }
                    for img in listing.images.all()
                ],
                "farmer": {
                    "id": farmer.id,
                    "name": farmer.full_name,
                    "phone": farmer.phone_number,
                    "district": farmer.district,
                    "location": farmer.location,
                    "profile_picture": farmer_picture,
                    "is_verified": farmer.is_verified,
                    "member_since": str(farmer.date_joined.year) if farmer.date_joined else None,
                },
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


@router.patch("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: str,
    data: UpdateListingRequest,
    current_user: User = Depends(get_current_active_farmer)
):
    """
    Partially update a listing (owner only).
    Only supplied fields are changed.
    """
    import uuid as _uuid
    try:
        _uuid.UUID(listing_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    @sync_to_async
    def do_update():
        try:
            listing = Listing.objects.select_related(
                'produce_type', 'produce_type__category', 'category', 'farmer'
            ).get(id=listing_id, farmer=current_user)
        except Listing.DoesNotExist:
            return None, "not_found"

        # Apply only the fields that were explicitly provided
        update_fields = []

        if data.produce_type_id is not None:
            try:
                pt = ProduceType.objects.select_related('category').get(id=data.produce_type_id)
                listing.produce_type = pt
                listing.category = pt.category
                listing.title = f"{pt.name}"
                update_fields += ['produce_type', 'category', 'title']
            except ProduceType.DoesNotExist:
                return None, "invalid_produce_type"

        if data.quantity_available is not None:
            listing.quantity_available = data.quantity_available
            update_fields.append('quantity_available')
        if data.unit is not None:
            listing.unit = data.unit
            update_fields.append('unit')
        if data.price_per_unit is not None:
            listing.price_per_unit = data.price_per_unit
            update_fields.append('price_per_unit')
        if data.description is not None:
            listing.description = data.description
            update_fields.append('description')
        if data.is_organic is not None:
            listing.is_organic = data.is_organic
            update_fields.append('is_organic')
        if data.is_negotiable is not None:
            listing.is_negotiable = data.is_negotiable
            update_fields.append('is_negotiable')
        if data.delivery_available is not None:
            listing.delivery_available = data.delivery_available
            update_fields.append('delivery_available')
        if data.pickup_available is not None:
            listing.pickup_available = data.pickup_available
            update_fields.append('pickup_available')
        if data.delivery_radius_km is not None:
            listing.delivery_radius_km = data.delivery_radius_km
            update_fields.append('delivery_radius_km')
        if data.harvest_date is not None:
            listing.harvest_date = data.harvest_date
            update_fields.append('harvest_date')
        if data.available_from is not None:
            listing.available_from = data.available_from
            update_fields.append('available_from')
        if data.available_until is not None:
            listing.available_until = data.available_until
            update_fields.append('available_until')
        if data.farm_location is not None:
            listing.farm_location = data.farm_location
            update_fields.append('farm_location')
        if data.grade is not None:
            listing.grade = data.grade
            update_fields.append('grade')
        if data.variety is not None:
            listing.variety = data.variety
            update_fields.append('variety')
        if data.minimum_order is not None:
            listing.minimum_order = data.minimum_order
            update_fields.append('minimum_order')
        if data.status is not None:
            listing.status = data.status
            update_fields.append('status')
        district = data.resolved_district()
        if district:
            listing.district = district
            update_fields.append('district')

        if update_fields:
            listing.save(update_fields=update_fields)

        farmer = listing.farmer
        farmer_picture = None
        if farmer.profile_picture:
            try:
                farmer_picture = farmer.profile_picture.url
            except Exception:
                farmer_picture = None

        return {
            "id": str(listing.id),
            "listing_number": listing.listing_number,
            "title": listing.title,
            "description": listing.description,
            "produce_type": {
                "id": listing.produce_type.id,
                "name": listing.produce_type.name,
                "slug": listing.produce_type.slug,
            },
            "category": {
                "id": listing.category.id,
                "name": listing.category.name,
                "slug": listing.category.slug,
            },
            "variety": listing.variety,
            "grade": listing.grade,
            "quality_tags": listing.quality_tags or [],
            "quantity_available": float(listing.quantity_available),
            "unit": listing.unit,
            "minimum_order": float(listing.minimum_order) if listing.minimum_order else None,
            "price_per_unit": float(listing.price_per_unit),
            "currency": listing.currency,
            "district": listing.district,
            "farm_location": listing.farm_location,
            "status": listing.status,
            "is_organic": listing.is_organic,
            "is_negotiable": listing.is_negotiable,
            "delivery_available": listing.delivery_available,
            "delivery_radius_km": listing.delivery_radius_km,
            "pickup_available": listing.pickup_available,
            "harvest_date": listing.harvest_date,
            "available_from": listing.available_from,
            "available_until": listing.available_until,
            "view_count": listing.view_count,
            "inquiry_count": listing.inquiry_count,
            "images": [
                {
                    "id": str(img.id),
                    "url": img.image.url,
                    "caption": img.caption,
                    "is_primary": img.is_primary,
                    "order": img.order,
                }
                for img in listing.images.all()
            ],
            "farmer": {
                "id": farmer.id,
                "name": farmer.full_name,
                "phone": farmer.phone_number,
                "district": farmer.district,
                "location": farmer.location,
                "profile_picture": farmer_picture,
                "is_verified": farmer.is_verified,
                "member_since": str(farmer.date_joined.year) if farmer.date_joined else None,
            },
        }, "ok"

    result, error = await do_update()
    if error == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    if error == "invalid_produce_type":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid produce_type_id")
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
    image: Optional[UploadFile] = File(None),
    caption: str = Form(""),
    current_user: User = Depends(get_current_active_farmer)
):
    """
    Upload an image for a listing (owner only).
    If no image is provided the request succeeds with an empty response,
    allowing the frontend to always call this endpoint after creating a listing.
    """
    try:
        listing = await sync_to_async(Listing.objects.get)(id=listing_id, farmer=current_user)
    except Listing.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )

    # No image supplied — return early so the listing creation flow still succeeds
    if image is None or image.filename == "":
        return {"id": None, "url": None, "caption": caption, "is_primary": False}

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
