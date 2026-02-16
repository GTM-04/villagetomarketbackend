"""
Marketplace endpoints - Orders and transactions.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.marketplace.models import Order
from apps.users.models import User
from api.core.security import get_current_user

router = APIRouter()


# Pydantic models
class OrderResponse(BaseModel):
    id: str
    order_number: str
    listing_title: str
    quantity: float
    total_amount: float
    status: str
    created_at: str


@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(current_user: User = Depends(get_current_user)):
    """
    List user's orders.
    """
    from django.db.models import Q
    
    orders = Order.objects.filter(
        Q(buyer=current_user) | Q(farmer=current_user)
    ).select_related('listing')
    
    return [
        {
            "id": str(order.id),
            "order_number": order.order_number,
            "listing_title": order.listing.title,
            "quantity": float(order.quantity),
            "total_amount": float(order.total_amount),
            "status": order.status,
            "created_at": order.created_at.isoformat(),
        }
        for order in orders
    ]
