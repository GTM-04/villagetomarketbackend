"""
Messaging endpoints - Conversations and messages.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from asgiref.sync import sync_to_async
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.messaging.models import Conversation, Message
from apps.users.models import User
from api.core.security import get_current_user

router = APIRouter()


# Pydantic models
class ConversationResponse(BaseModel):
    id: str
    other_user: dict
    last_message: Optional[str]
    last_message_at: Optional[str]
    unread_count: int


class MessageResponse(BaseModel):
    id: str
    sender_id: str
    text: str
    created_at: str
    is_read: bool


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(current_user: User = Depends(get_current_user)):
    """
    List user's conversations.
    """
    from django.db.models import Q
    
    conversations = await sync_to_async(lambda: list(Conversation.objects.filter(
        Q(participant_1=current_user) | Q(participant_2=current_user)
    ).select_related('participant_1', 'participant_2')) )()
    
    return [
        {
            "id": str(conv.id),
            "other_user": {
                "id": str(conv.get_other_participant(current_user).id),
                "name": conv.get_other_participant(current_user).full_name,
            },
            "last_message": conv.last_message_text,
            "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
            "unread_count": conv.get_unread_count(current_user),
        }
        for conv in conversations
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get messages in a conversation.
    """
    @sync_to_async
    def fetch_messages():
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return None, None

        if current_user.id not in [conversation.participant_1_id, conversation.participant_2_id]:
            return "forbidden", None

        msgs = list(conversation.messages.select_related('sender').all())
        conversation.mark_read(current_user)
        return "ok", [
            {
                "id": str(msg.id),
                "sender_id": str(msg.sender.id),
                "text": msg.text,
                "created_at": msg.created_at.isoformat(),
                "is_read": msg.is_read,
            }
            for msg in msgs
        ]

    result, data = await fetch_messages()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    if result == "forbidden":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    return data
