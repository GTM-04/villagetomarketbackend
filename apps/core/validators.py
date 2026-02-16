"""
Core validators.
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import phonenumbers
from phonenumbers import NumberParseException


def validate_zimbabwe_phone_number(value):
    """
    Validate that the phone number is a valid Zimbabwe number.
    """
    try:
        parsed_number = phonenumbers.parse(value, 'ZW')
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValidationError(
                _('%(value)s is not a valid phone number.'),
                params={'value': value},
            )
        if parsed_number.country_code != 263:
            raise ValidationError(
                _('Phone number must be a Zimbabwe number (+263).'),
            )
    except NumberParseException:
        raise ValidationError(
            _('%(value)s is not a valid phone number format.'),
            params={'value': value},
        )


def validate_positive_number(value):
    """
    Validate that the value is a positive number.
    """
    if value <= 0:
        raise ValidationError(
            _('%(value)s must be a positive number.'),
            params={'value': value},
        )
