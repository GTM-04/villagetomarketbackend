"""
Notification endpoints.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from asgiref.sync import sync_to_async
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.notifications.models import Notification
from apps.users.models import User
from api.core.security import get_current_user

router = APIRouter()


# Pydantic models
class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: str


@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(current_user: User = Depends(get_current_user)):
    """
    Get user's notifications.
    """
    notifications = current_user.notifications.all()[:50]
    
    return [
        {
            "id": str(notif.id),
            "title": notif.title,
            "message": notif.message,
            "notification_type": notif.notification_type,
            "is_read": notif.is_read,
            "created_at": notif.created_at.isoformat(),
        }
        for notif in notifications
    ]


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Mark notification as read.
    """
    try:
        notification = await sync_to_async(Notification.objects.get)(id=notification_id, user=current_user)
        await sync_to_async(notification.mark_as_read)()
        return {"message": "Notification marked as read"}
    except Notification.DoesNotExist:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
