"""
Pricing endpoints - Market prices and trends.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from asgiref.sync import sync_to_async
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.pricing.models import MarketPrice, PriceTrend
from api.core.security import get_current_user

router = APIRouter()


# Pydantic models
class MarketPriceResponse(BaseModel):
    produce_type: str
    district: str
    price_min: float
    price_avg: float
    price_max: float
    unit: str
    recorded_date: date


@router.get("/market-prices", response_model=List[MarketPriceResponse])
async def get_market_prices(
    district: Optional[str] = None,
    produce_type: Optional[str] = None,
):
    """
    Get current market prices.
    """
    @sync_to_async
    def get_prices():
        queryset = MarketPrice.objects.select_related('produce_type').all()

        if district:
            queryset = queryset.filter(district__iexact=district)
        if produce_type:
            queryset = queryset.filter(produce_type__name__icontains=produce_type)

        return [
            {
                "produce_type": price.produce_type.name,
                "district": price.district,
                "price_min": float(price.price_min),
                "price_avg": float(price.price_avg),
                "price_max": float(price.price_max),
                "unit": price.unit,
                "recorded_date": price.recorded_date,
            }
            for price in queryset[:50]
        ]

    return await get_prices()
