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


class CreateConversationRequest(BaseModel):
    recipient_id: int
    listing_id: Optional[str] = None
    initial_message: Optional[str] = None


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_or_get_conversation(
    data: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Start or retrieve an existing conversation with another user.
    Optionally linked to a listing.
    """
    from django.db.models import Q

    @sync_to_async
    def get_or_create_conv():
        try:
            recipient = User.objects.get(id=data.recipient_id)
        except User.DoesNotExist:
            return "no_recipient", None

        if recipient.id == current_user.id:
            return "self", None

        listing = None
        if data.listing_id:
            from apps.listings.models import Listing
            try:
                listing = Listing.objects.get(id=data.listing_id)
            except Listing.DoesNotExist:
                pass  # listing not found — proceed without it

        # Look up existing conversation regardless of participant order
        existing = Conversation.objects.filter(
            Q(participant_1=current_user, participant_2=recipient) |
            Q(participant_1=recipient, participant_2=current_user)
        )
        if listing:
            existing = existing.filter(listing=listing)

        conv = existing.select_related('participant_1', 'participant_2').first()

        if conv is None:
            conv = Conversation.objects.create(
                participant_1=current_user,
                participant_2=recipient,
                listing=listing,
            )

        # Send initial message if provided and conversation is new
        if data.initial_message and conv.last_message_text == "":
            from apps.messaging.models import Message
            msg = Message.objects.create(
                conversation=conv,
                sender=current_user,
                text=data.initial_message,
            )
            conv.last_message_text = msg.text
            conv.last_message_at = msg.created_at
            conv.last_message_sender = current_user
            conv.unread_count_p2 = 1 if conv.participant_1 == current_user else 0
            conv.unread_count_p1 = 1 if conv.participant_2 == current_user else 0
            conv.save(update_fields=[
                'last_message_text', 'last_message_at',
                'last_message_sender', 'unread_count_p1', 'unread_count_p2',
            ])

        other = conv.get_other_participant(current_user)
        return "ok", {
            "id": str(conv.id),
            "other_user": {
                "id": str(other.id),
                "name": other.full_name,
            },
            "last_message": conv.last_message_text or None,
            "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
            "unread_count": conv.get_unread_count(current_user),
        }

    result, data_out = await get_or_create_conv()
    if result == "no_recipient":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")
    if result == "self":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot start a conversation with yourself")
    return data_out


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get a single conversation by ID.
    """
    @sync_to_async
    def fetch_conv():
        from django.db.models import Q
        try:
            conv = Conversation.objects.select_related(
                'participant_1', 'participant_2'
            ).get(
                id=conversation_id
            )
        except Conversation.DoesNotExist:
            return None
        if current_user.id not in [conv.participant_1_id, conv.participant_2_id]:
            return "forbidden"
        other = conv.get_other_participant(current_user)
        return {
            "id": str(conv.id),
            "other_user": {
                "id": str(other.id),
                "name": other.full_name,
            },
            "last_message": conv.last_message_text or None,
            "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
            "unread_count": conv.get_unread_count(current_user),
        }

    result = await fetch_conv()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if result == "forbidden":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return result


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
