"""
Authentication endpoints - Register, login, refresh token.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from asgiref.sync import sync_to_async
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.users.models import User
from api.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

router = APIRouter()


# Pydantic models
class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    phone_number: str = Field(..., pattern=r'^\+263\d{9}$')
    password: str = Field(..., min_length=6)
    user_type: str = Field(..., pattern='^(farmer|buyer)$')
    district: Optional[str] = None
    ward: Optional[str] = None


class UserLoginRequest(BaseModel):
    phone_number: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegisterRequest):
    """
    Register a new user (farmer or buyer).
    """
    # Check if user already exists
    user_exists = await sync_to_async(User.objects.filter(phone_number=data.phone_number).exists)()
    if user_exists:
        # If user exists, return error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    # Create user
    user = await sync_to_async(User.objects.create)(
        full_name=data.full_name,
        phone_number=data.phone_number,
        user_type=data.user_type,
        district=data.district or '',
        is_active=True,
    )
    if hasattr(user, 'ward'):
        user.ward = data.ward or ''
        await sync_to_async(user.save)()
    await sync_to_async(user.set_password)(data.password)
    await sync_to_async(user.save)()
    
    # Create profile based on user type
    if data.user_type == 'farmer':
        from apps.farmers.models import FarmerProfile
        exists = await sync_to_async(FarmerProfile.objects.filter(user=user).exists)()
        if not exists:
            await sync_to_async(FarmerProfile.objects.create)(user=user)
    else:
        from apps.buyers.models import BuyerProfile
        await sync_to_async(BuyerProfile.objects.create)(user=user)
    
    # Create tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "user_type": user.user_type,
        }
    }


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLoginRequest):
    """
    Login with phone number and password.
    """
    # Find user
    try:
        user = await sync_to_async(User.objects.get)(phone_number=data.phone_number)
    except User.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password"
        )
    
    # Verify password
    password_valid = await sync_to_async(user.check_password)(data.password)
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "user_type": user.user_type,
        }
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    """
    payload = decode_token(data.refresh_token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    
    try:
        user = await sync_to_async(User.objects.get)(id=user_id)
    except User.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new tokens
    access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "user_type": user.user_type,
        }
    }
