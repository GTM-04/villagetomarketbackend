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
    user_type: Optional[str] = Field(default='farmer', pattern='^(farmer|buyer)$')
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


class PasswordResetRequestModel(BaseModel):
    phone_number: str


class PasswordResetConfirmModel(BaseModel):
    reset_token: str
    new_password: str = Field(..., min_length=6)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegisterRequest):
    """
    Register a new user. One account serves as both farmer and buyer.
    The user_type field represents the currently active mode (defaults to 'farmer').
    Both FarmerProfile and BuyerProfile are created automatically.
    """
    # Check if user already exists
    existing_user = await sync_to_async(User.objects.filter(phone_number=data.phone_number).first)()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered. Please sign in."
        )
    
    # Create new user — user_type is just the initial active mode
    user = await sync_to_async(User.objects.create)(
        full_name=data.full_name,
        phone_number=data.phone_number,
        user_type=data.user_type or 'farmer',
        district=data.district or '',
        is_active=True,
    )
    await sync_to_async(user.set_password)(data.password)
    await sync_to_async(user.save)()
    
    # Create BOTH profiles so user can switch modes freely
    from apps.farmers.models import FarmerProfile
    from apps.buyers.models import BuyerProfile
    
    farmer_exists = await sync_to_async(FarmerProfile.objects.filter(user=user).exists)()
    if not farmer_exists:
        await sync_to_async(FarmerProfile.objects.create)(user=user)
    
    buyer_exists = await sync_to_async(BuyerProfile.objects.filter(user=user).exists)()
    if not buyer_exists:
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
            "district": user.district,
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


@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
@router.post("/forgot-password", status_code=status.HTTP_200_OK)        # alias
async def password_reset_request(data: PasswordResetRequestModel):
    """
    Request a password reset token for the given phone number.

    In production this token would be delivered via SMS.
    For development it is returned directly in the response.
    The token expires in 15 minutes.
    """
    from datetime import timedelta
    from api.core.config import settings
    from jose import jwt

    @sync_to_async
    def find_user():
        try:
            return User.objects.get(phone_number=data.phone_number)
        except User.DoesNotExist:
            return None

    user = await find_user()

    # Always return 200 to avoid leaking whether a phone number is registered.
    if user is None:
        return {
            "message": "If that number is registered a reset code will appear.",
            "reset_token": None,
            "display_for_seconds": 30,
        }

    # Build a short-lived reset token
    from datetime import datetime
    expire = datetime.utcnow() + timedelta(minutes=15)
    payload = {
        "sub": str(user.id),
        "exp": expire,
        "type": "password_reset",
    }
    reset_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    return {
        "message": "Use this code to reset your password. It expires in 15 minutes.",
        "reset_token": reset_token,
        "display_for_seconds": 30,
    }


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
@router.post("/password-reset", status_code=status.HTTP_200_OK)          # alias
async def password_reset_confirm(data: PasswordResetConfirmModel):
    """
    Confirm password reset using the token received from /password-reset/request.
    Sets the new password if the token is valid and unexpired.
    """
    from jose import jwt, JWTError
    from api.core.config import settings

    # Decode and validate token
    try:
        payload = jwt.decode(data.reset_token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    if payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")

    @sync_to_async
    def set_new_password():
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
        user.set_password(data.new_password)
        user.save(update_fields=["password"])
        return user

    user = await set_new_password()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Issue fresh tokens so the user is logged in immediately after reset
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "message": "Password updated successfully.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "user_type": user.user_type,
            "district": user.district,
            "ward": user.ward,
            "is_verified": user.is_verified,
        },
    }
