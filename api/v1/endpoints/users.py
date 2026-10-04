"""
User endpoints - Profile management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from channels.db import database_sync_to_async as sync_to_async
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.users.models import User
from api.core.security import get_current_user

router = APIRouter()


# Pydantic models
class UserProfile(BaseModel):
    id: str
    full_name: str
    phone_number: str
    email: Optional[str]
    user_type: str
    district: str
    is_verified: bool
    profile: Optional[dict] = None


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    district: Optional[str] = None
    # Allow switching between farmer and buyer on the same account
    user_type: Optional[str] = None


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile.
    """
    profile_data = None
    
    if current_user.user_type == 'farmer':
        # Use sync_to_async to access related field
        @sync_to_async
        def get_farmer_profile():
            return current_user.farmer_profile
        
        profile = await get_farmer_profile()
        profile_data = {
            "farm_name": profile.farm_name,
            "farm_size": str(profile.farm_size) if profile.farm_size else None,
            "verified": getattr(profile, 'verified', False),
        }
    elif current_user.user_type == 'buyer':
        # Use sync_to_async to access related field
        @sync_to_async
        def get_buyer_profile():
            return current_user.buyer_profile
        
        profile = await get_buyer_profile()
        profile_data = {
            "organization_name": getattr(profile, 'organization_name', ''),
            "buyer_type": getattr(profile, 'buyer_type', ''),
        }
    
    return {
        "id": str(current_user.id),
        "full_name": current_user.full_name,
        "phone_number": current_user.phone_number,
        "email": getattr(current_user, 'email', ''),
        "user_type": current_user.user_type,
        "district": getattr(current_user, 'district', ''),
        "is_verified": getattr(current_user, 'is_verified', False),
        "profile": profile_data,
    }


@router.patch("/me", response_model=UserProfile)
async def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's profile.
    """
    # Basic profile fields
    if data.full_name:
        current_user.full_name = data.full_name
    if data.email:
        current_user.email = data.email
    if data.district:
        current_user.district = data.district

    # Optional role switch between farmer and buyer
    if data.user_type is not None:
        if data.user_type not in {"farmer", "buyer"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_type must be either 'farmer' or 'buyer'",
            )

        # Only do work when role is actually changing
        if current_user.user_type != data.user_type:
            current_user.user_type = data.user_type

            # Ensure the corresponding extended profile exists so subsequent
            # profile calls don't fail.
            if data.user_type == "farmer":
                from apps.farmers.models import FarmerProfile

                await sync_to_async(FarmerProfile.objects.get_or_create)(
                    user=current_user
                )
            elif data.user_type == "buyer":
                from apps.buyers.models import BuyerProfile

                await sync_to_async(BuyerProfile.objects.get_or_create)(
                    user=current_user
                )

    await sync_to_async(current_user.save)()

    return await get_current_user_profile(current_user)


class SwitchModeRequest(BaseModel):
    mode: str  # 'farmer' or 'buyer'


class SwitchModeResponse(BaseModel):
    user_type: str
    message: str


@router.post("/switch-mode", response_model=SwitchModeResponse)
async def switch_mode(
    data: SwitchModeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Switch the user's active mode between farmer and buyer.
    Both profiles already exist — this just toggles the active one.
    """
    if data.mode not in {'farmer', 'buyer'}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="mode must be 'farmer' or 'buyer'",
        )

    if current_user.user_type != data.mode:
        current_user.user_type = data.mode

        # Ensure the corresponding profile exists (safety net)
        if data.mode == 'farmer':
            from apps.farmers.models import FarmerProfile
            await sync_to_async(FarmerProfile.objects.get_or_create)(user=current_user)
        else:
            from apps.buyers.models import BuyerProfile
            await sync_to_async(BuyerProfile.objects.get_or_create)(user=current_user)

        await sync_to_async(current_user.save)()

    return {
        "user_type": current_user.user_type,
        "message": f"Switched to {data.mode} mode",
    }


class PublicFarmerProfile(BaseModel):
    id: str
    username: str
    full_name: str
    district: str
    profile_picture: Optional[str]
    bio: Optional[str]
    farm_name: str
    farm_size: Optional[str]
    is_verified: bool

@router.get("/farmer/{username}", response_model=PublicFarmerProfile)
async def get_public_farmer_profile(username: str):
    """
    Get a farmer's public profile by username or phone number.
    """
    from django.db.models import Q
    @sync_to_async
    def fetch_farmer():
        try:
            # allow fetching by username or phone_number
            user = User.objects.select_related('farmer_profile').get(
                Q(username=username) | Q(phone_number=username), 
                user_type='farmer'
            )
            profile = user.farmer_profile
            return {
                "id": str(user.id),
                "username": user.username,
                "full_name": user.full_name,
                "district": getattr(user, 'district', ''),
                "profile_picture": user.profile_picture.url if user.profile_picture else None,
                "bio": getattr(user, 'bio', ''),
                "farm_name": getattr(profile, 'farm_name', ''),
                "farm_size": str(profile.farm_size) if getattr(profile, 'farm_size', None) else None,
                "is_verified": getattr(user, 'is_verified', False)
            }
        except User.DoesNotExist:
            return None
            
    data = await fetch_farmer()
    if not data:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return data
