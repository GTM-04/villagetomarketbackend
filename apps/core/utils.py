"""
Core utility functions.
"""

import hashlib
import phonenumbers
from phonenumbers import NumberParseException
from django.conf import settings
from typing import Optional


def normalize_phone_number(phone_number: str, region: str = None) -> Optional[str]:
    """
    Normalize phone number to E.164 format.
    
    Args:
        phone_number: Phone number string
        region: ISO country code (defaults to Zimbabwe)
    
    Returns:
        Normalized phone number or None if invalid
    """
    if region is None:
        region = settings.DEFAULT_PHONE_REGION
    
    try:
        parsed_number = phonenumbers.parse(phone_number, region)
        if phonenumbers.is_valid_number(parsed_number):
            return phonenumbers.format_number(
                parsed_number,
                phonenumbers.PhoneNumberFormat.E164
            )
    except NumberParseException:
        pass
    
    return None


def validate_zimbabwe_phone(phone_number: str) -> bool:
    """
    Validate Zimbabwe phone number format.
    
    Args:
        phone_number: Phone number to validate
    
    Returns:
        True if valid Zimbabwe number
    """
    try:
        parsed_number = phonenumbers.parse(phone_number, 'ZW')
        return (
            phonenumbers.is_valid_number(parsed_number) and
            parsed_number.country_code == 263
        )
    except NumberParseException:
        return False


def calculate_hash(data: str) -> str:
    """
    Calculate SHA256 hash of data.
    
    Args:
        data: String data to hash
    
    Returns:
        Hex digest of hash
    """
    return hashlib.sha256(data.encode()).hexdigest()


def format_currency(amount: float, currency: str = None) -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Amount to format
        currency: Currency code (defaults to ZWL)
    
    Returns:
        Formatted currency string
    """
    if currency is None:
        currency = settings.DEFAULT_CURRENCY
    
    return f"{currency} {amount:,.2f}"
