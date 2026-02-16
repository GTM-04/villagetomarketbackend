"""
WebSocket consumers for real-time messaging.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        
        # Verify user is participant in conversation
        is_participant = await self.verify_participant()
        
        if not is_participant:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing_indicator(data)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(data)
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON'
            }))
    
    async def handle_chat_message(self, data):
        """Handle incoming chat message."""
        message_text = data.get('message', '')
        client_id = data.get('client_id', '')
        
        # Save message to database
        message = await self.save_message(message_text, client_id)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': str(message.id),
                    'text': message.text,
                    'sender_id': str(message.sender.id),
                    'sender_name': message.sender.full_name,
                    'created_at': message.created_at.isoformat(),
                    'client_id': message.client_id,
                }
            }
        )
    
    async def handle_typing_indicator(self, data):
        """Handle typing indicator."""
        is_typing = data.get('is_typing', False)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': str(self.scope['user'].id),
                'user_name': self.scope['user'].full_name,
                'is_typing': is_typing,
            }
        )
    
    async def handle_read_receipt(self, data):
        """Handle read receipt."""
        message_id = data.get('message_id')
        
        if message_id:
            await self.mark_message_read(message_id)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'message_id': message_id,
                    'user_id': str(self.scope['user'].id),
                }
            )
    
    async def chat_message(self, event):
        """Send chat message to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket."""
        # Don't send typing indicator to the sender
        if event['user_id'] != str(self.scope['user'].id):
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing'],
            }))
    
    async def read_receipt(self, event):
        """Send read receipt to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
        }))
    
    @database_sync_to_async
    def verify_participant(self):
        """Verify user is participant in conversation."""
        from .models import Conversation
        
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            user = self.scope['user']
            return user == conversation.participant_1 or user == conversation.participant_2
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, message_text, client_id):
        """Save message to database."""
        from .models import Conversation, Message
        
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.scope['user'],
            text=message_text,
            message_type='text',
            client_id=client_id,
            is_delivered=True,
            delivered_at=timezone.now()
        )
        return message
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark message as read."""
        from .models import Message
        
        try:
            message = Message.objects.get(id=message_id)
            message.mark_as_read()
        except Message.DoesNotExist:
            pass
