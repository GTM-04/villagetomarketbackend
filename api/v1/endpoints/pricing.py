"""
Pricing endpoints - Market prices, trends, and ML-based price recommendation.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from asgiref.sync import sync_to_async
import io
import os
import django
import numpy as np

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.pricing.models import MarketPrice, PriceTrend
from api.core.security import get_current_user
from api.v1.ml.pricing_recommender import recommend_price

router = APIRouter()


# ── Pydantic models ───────────────────────────────────────────────────────────

class MarketPriceResponse(BaseModel):
    produce_type: str
    district: str
    price_min: float
    price_avg: float
    price_max: float
    unit: str
    recorded_date: date


class PriceTrendResponse(BaseModel):
    produce_type: str
    district: str
    period_start: date
    period_end: date
    trend_direction: str
    price_change_percent: float
    average_price: float
    forecast_next_period: Optional[float] = None


class PriceRecommendRequest(BaseModel):
    """
    Fields required to recommend a price for a new crop listing.
    Mirrors the Django Listing model fields used during feature engineering.
    """
    produce_type: str = Field(..., examples=["Tomatoes"],
                              description="Crop type — must match a known ProduceType name")
    variety: str      = Field("Standard", examples=["Roma"],
                              description="Sub-variety, e.g. Roma, Yellow, Hybrid")
    grade: str        = Field("Grade B", examples=["Grade A"],
                              description="Quality grade: Grade A/B/C, Premium, Export Quality, Standard")
    unit: str         = Field("kg", examples=["kg"],
                              description="Measurement unit: kg, bags, crates, tonnes …")
    district: str     = Field("Harare", examples=["Harare"],
                              description="Growing / delivery district")
    is_organic: bool  = Field(False, examples=[False],
                              description="Organic certification flag")
    quality_tags: List[str] = Field(
        default_factory=list,
        examples=[["fresh", "pesticide-free"]],
        description="Quality descriptors: fresh, pesticide-free, locally-grown, non-gmo, …",
    )
    quantity_available: float = Field(..., gt=0, examples=[300.0],
                                      description="Total quantity available for sale")
    minimum_order: Optional[float] = Field(None, gt=0, examples=[30.0],
                                           description="Minimum order quantity (defaults to 10 % of total)")
    harvest_date: Optional[date]   = Field(None, examples=["2026-02-24"],
                                           description="Date the crop was harvested (ISO format)")
    confidence_margin: float = Field(0.10, ge=0.01, le=0.50,
                                     description="Half-width of the price band as a fraction (0.10 = ±10 %)")


class PriceRecommendResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    recommended_price: float
    price_min: float
    price_max: float
    currency: str
    unit: str
    model_used: str
    confidence_margin: str
    note: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/market-prices", response_model=List[MarketPriceResponse])
async def get_market_prices(
    district: Optional[str] = None,
    produce_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
):
    """
    Get current market prices for all produce types.
    Filter by district or produce type name.
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
            for price in queryset[:limit]
        ]

    return await get_prices()


@router.get("/trends", response_model=List[PriceTrendResponse])
async def get_price_trends(
    produce_type: Optional[str] = None,
    district: Optional[str] = None,
    days: int = Query(30, ge=7, le=120),
    limit: int = Query(12, ge=1, le=100),
):
    """
    Get trend summaries for produce pricing.

    Prefers persisted PriceTrend rows. If none exist, derives lightweight trend
    summaries from recent MarketPrice data so buyers still see trend direction.
    """

    @sync_to_async
    def fetch_trends():
        trends_qs = PriceTrend.objects.select_related('produce_type').all()

        if district:
            trends_qs = trends_qs.filter(district__iexact=district)
        if produce_type:
            trends_qs = trends_qs.filter(produce_type__name__icontains=produce_type)

        trends = list(trends_qs.order_by('-period_end')[:limit])
        if trends:
            return [
                {
                    "produce_type": t.produce_type.name,
                    "district": t.district,
                    "period_start": t.period_start,
                    "period_end": t.period_end,
                    "trend_direction": t.trend_direction,
                    "price_change_percent": float(t.price_change_percent),
                    "average_price": float(t.average_price),
                    "forecast_next_period": float(t.forecast_next_period)
                    if t.forecast_next_period is not None
                    else None,
                }
                for t in trends
            ]

        from datetime import timedelta
        from django.db.models import Avg

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        mp_qs = MarketPrice.objects.select_related('produce_type').filter(
            recorded_date__gte=start_date,
            recorded_date__lte=end_date,
        )
        if district:
            mp_qs = mp_qs.filter(district__iexact=district)
        if produce_type:
            mp_qs = mp_qs.filter(produce_type__name__icontains=produce_type)

        grouped = {}
        for row in mp_qs.order_by('produce_type__name', 'district', 'recorded_date'):
            key = (row.produce_type.name, row.district)
            grouped.setdefault(key, []).append(row)

        derived = []
        for (name, location), rows in grouped.items():
            first_price = float(rows[0].price_avg)
            last_price = float(rows[-1].price_avg)
            avg_price = float(sum(float(r.price_avg) for r in rows) / len(rows))
            if first_price <= 0:
                pct = 0.0
            else:
                pct = ((last_price - first_price) / first_price) * 100.0

            if pct > 2:
                direction = 'increasing'
            elif pct < -2:
                direction = 'decreasing'
            else:
                direction = 'stable'

            derived.append(
                {
                    "produce_type": name,
                    "district": location,
                    "period_start": rows[0].recorded_date,
                    "period_end": rows[-1].recorded_date,
                    "trend_direction": direction,
                    "price_change_percent": round(pct, 2),
                    "average_price": round(avg_price, 2),
                    "forecast_next_period": round(last_price * (1 + (pct / 100.0)), 2),
                }
            )

        derived.sort(key=lambda item: abs(item['price_change_percent']), reverse=True)
        return derived[:limit]

    return await fetch_trends()


@router.post(
    "/recommend",
    response_model=PriceRecommendResponse,
    summary="Recommend a price for a new crop listing",
    description=(
        "Accepts the crop listing fields and an optional crop photo. "
        "Returns a recommended price per unit (ZWL) with a confidence band. "
        "Uses the trained ML model when available; falls back to a "
        "market-heuristic if the model has not yet been trained."
    ),
)
async def recommend_crop_price(
    produce_type: str       = "Tomatoes",
    variety: str            = "Standard",
    grade: str              = "Grade B",
    unit: str               = "kg",
    district: str           = "Harare",
    is_organic: bool        = False,
    quality_tags: str       = "",          # comma-separated in form data
    quantity_available: float = 100.0,
    minimum_order: Optional[float] = None,
    harvest_date: Optional[str]    = None,
    confidence_margin: float       = 0.10,
    image: Optional[UploadFile]    = File(None),
):
    """
    **Multipart form** endpoint so a crop photo can be uploaded alongside
    the listing fields.

    - `quality_tags` — pass as a comma-separated string, e.g. `"fresh,pesticide-free"`
    - `image`        — optional JPEG/PNG crop photo (improves accuracy when ML model is trained)
    """
    # Parse quality tags from comma-separated string
    tags = [t.strip() for t in quality_tags.split(",") if t.strip()] if quality_tags else []

    # Parse harvest date
    harvest_d: Optional[date] = None
    if harvest_date:
        try:
            harvest_d = date.fromisoformat(harvest_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid harvest_date format '{harvest_date}'. Use YYYY-MM-DD.",
            )

    listing_fields = {
        "produce_type":       produce_type,
        "variety":            variety,
        "grade":              grade,
        "unit":               unit,
        "district":           district,
        "is_organic":         is_organic,
        "quality_tags":       tags,
        "quantity_available": quantity_available,
        "minimum_order":      minimum_order,
        "harvest_date":       harvest_d,
    }

    # Load image if provided
    img_array: Optional[np.ndarray] = None
    if image is not None:
        if not image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must be an image (JPEG, PNG, …).",
            )
        contents = await image.read()
        try:
            from PIL import Image as PILImage
            pil_img   = PILImage.open(io.BytesIO(contents)).convert("RGB").resize((224, 224))
            img_array = np.array(pil_img, dtype=np.uint8)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not decode image: {exc}",
            )

    result = recommend_price(
        listing_fields,
        image=img_array,
        confidence_margin=confidence_margin,
    )

    return result


@router.post(
    "/recommend/json",
    response_model=PriceRecommendResponse,
    summary="Recommend a price (JSON body, no image)",
    description=(
        "JSON-body version of the price recommendation endpoint. "
        "Use this when no crop photo is available. "
        "For photo-assisted recommendations use POST /recommend (multipart)."
    ),
)
async def recommend_crop_price_json(payload: PriceRecommendRequest):
    """
    Convenience endpoint for clients that send JSON (no image upload).
    The model uses tabular features only; the image branch runs on a
    neutral synthetic image derived from the crop colour palette.
    """
    listing_fields = payload.model_dump(exclude={"confidence_margin"})
    result = recommend_price(
        listing_fields,
        image=None,
        confidence_margin=payload.confidence_margin,
    )
    return result
