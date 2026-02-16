"""
User endpoints - Profile management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
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
    ward: str
    is_verified: bool
    profile: Optional[dict] = None


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    district: Optional[str] = None
    ward: Optional[str] = None


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile.
    """
    profile_data = None
    
    if current_user.user_type == 'farmer':
        profile = current_user.farmer_profile
        profile_data = {
            "farm_name": profile.farm_name,
            "farm_size": str(profile.farm_size),
            "verified": profile.verified,
        }
    elif current_user.user_type == 'buyer':
        profile = current_user.buyer_profile
        profile_data = {
            "organization_name": profile.organization_name,
            "buyer_type": profile.buyer_type,
        }
    
    return {
        "id": str(current_user.id),
        "full_name": current_user.full_name,
        "phone_number": current_user.phone_number,
        "email": current_user.email,
        "user_type": current_user.user_type,
        "district": current_user.district,
        "ward": current_user.ward,
        "is_verified": current_user.is_verified,
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
    if data.full_name:
        current_user.full_name = data.full_name
    if data.email:
        current_user.email = data.email
    if data.district:
        current_user.district = data.district
    if data.ward:
        current_user.ward = data.ward
    
    current_user.save()
    
    return await get_current_user_profile(current_user)
