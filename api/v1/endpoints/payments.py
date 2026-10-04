"""
Payments endpoints - Paynow integration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from paynow import Paynow
import os
import uuid

from api.core.security import get_current_user
from apps.users.models import User

router = APIRouter()

# Paynow Config - In a real app these should come from .env
# Using test credentials or placeholders if not available
PAYNOW_INTEGRATION_ID = os.getenv("PAYNOW_INTEGRATION_ID", "12345")
PAYNOW_INTEGRATION_KEY = os.getenv("PAYNOW_INTEGRATION_KEY", "test-key-replace-me")
PAYNOW_RETURN_URL = os.getenv("PAYNOW_RETURN_URL", "http://localhost:5173/payment-return")
PAYNOW_RESULT_URL = os.getenv("PAYNOW_RESULT_URL", "http://localhost:8000/api/v1/payments/update")

paynow = Paynow(
    PAYNOW_INTEGRATION_ID, 
    PAYNOW_INTEGRATION_KEY,
    PAYNOW_RETURN_URL, 
    PAYNOW_RESULT_URL
)

class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    email: str
    phone_number: Optional[str] = None
    method: str = "ecocash" # ecocash, onemoney, paynow (for web)

class PaymentResponse(BaseModel):
    success: bool
    url: Optional[str] = None
    poll_url: Optional[str] = None
    error: Optional[str] = None

@router.post("/initiate", response_model=PaymentResponse)
async def initiate_payment(data: PaymentRequest, current_user: User = Depends(get_current_user)):
    """
    Initiate a payment via Paynow (EcoCash, OneMoney, or Web).
    """
    payment = paynow.create_payment(data.order_id, data.email)
    payment.add("Order " + data.order_id, data.amount)

    try:
        if data.method in ['ecocash', 'onemoney']:
            if not data.phone_number:
                raise HTTPException(status_code=400, detail="Phone number is required for mobile money payments.")
            response = paynow.send_mobile(payment, data.phone_number, data.method)
        else:
            response = paynow.send(payment)

        if response.success:
            return {
                "success": True,
                "url": response.redirect_url,
                "poll_url": response.poll_url
            }
        else:
            return {
                "success": False,
                "error": response.error
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def check_payment_status(poll_url: str):
    """
    Check the status of a payment.
    """
    try:
        response = paynow.check_transaction_status(poll_url)
        return {
            "status": response.status,
            "paid": response.status.lower() == 'paid',
            "reference": response.reference
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
