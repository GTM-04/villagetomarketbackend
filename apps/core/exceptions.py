"""
Custom exceptions.
"""

from rest_framework.exceptions import APIException
from rest_framework import status


class InvalidPhoneNumberException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid phone number format.'
    default_code = 'invalid_phone_number'


class OfflineSyncException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Sync conflict detected.'
    default_code = 'sync_conflict'


class ResourceNotFoundException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found.'
    default_code = 'resource_not_found'
