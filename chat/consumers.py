# ============================================
# chat/consumers.py - COMPLETE UPDATED VERSION
# ============================================
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Conversation, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        # Verify participant
        if not await self.is_participant():
            await self.close()
            return

        # Join group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Notify online
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': str(self.user.id),  # Ensure string for consistency
                'is_online': True
            }
        )

        # Send recent messages
        recent = await self.get_recent_messages()
        await self.send(text_data=json.dumps({
            'type': 'messages_loaded',
            'messages': recent
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name') and hasattr(self, 'user'):
            # Notify offline
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': str(self.user.id),
                    'is_online': False
                }
            )
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except:
            return

        msg_type = data.get('type')

        if msg_type == 'new_message':
            content = data.get('message', {}).get('content', '').strip()
            if not content:
                return

            message = await self.save_message(content)

            broadcast_msg = {
                'id': message.id,
                'sender_id': str(message.sender.id),
                'sender_name': message.sender.shop_name or message.sender.email,
                'sender_profile': message.sender.profile_picture.url if message.sender.profile_picture else None,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'is_read': False,
                'type': 'text'
            }

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'new_message',
                    'message': broadcast_msg
                }
            )

        elif msg_type == 'typing_indicator':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': str(data.get('user_id', self.user.id)),
                    'is_typing': data.get('is_typing', False)
                }
            )

        elif msg_type == 'message_read':
            message_id = data.get('message_id')
            if message_id:
                await self.mark_as_read(message_id)
                # Broadcast read receipt to ALL users in conversation
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_read',
                        'message_id': message_id
                    }
                )

        elif msg_type == 'user_online':
            # Handle explicit online status
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': str(data.get('user_id', self.user.id)),
                    'is_online': True
                }
            )

        elif msg_type == 'user_offline':
            # Handle explicit offline status
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': str(data.get('user_id', self.user.id)),
                    'is_online': False
                }
            )

    # Handlers - These receive events from channel layer and send to WebSocket
    async def new_message(self, event):
        """Send new message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message']
        }))

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket (except to the typer themselves)"""
        # Don't send typing indicator back to the person who's typing
        if str(event.get('user_id')) != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'is_typing': event['is_typing']
            }))

    async def message_read(self, event):
        """Send read receipt to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'message_id': event['message_id']
        }))

    async def user_status(self, event):
        """Send user online/offline status to WebSocket (except to themselves)"""
        # Don't send status update back to the user themselves
        if str(event.get('user_id')) != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'user_id': event['user_id'],
                'is_online': event['is_online']
            }))

    # DB Helpers
    @database_sync_to_async
    def is_participant(self):
        return Conversation.objects.filter(
            id=self.conversation_id,
            participants=self.user
        ).exists()

    @database_sync_to_async
    def get_recent_messages(self):
        msgs = Message.objects.filter(conversation_id=self.conversation_id)\
            .select_related('sender')\
            .order_by('created_at')[:100]
        return [{
            'id': m.id,
            'sender_id': str(m.sender.id),
            'sender_name': m.sender.shop_name or m.sender.email,
            'sender_profile': m.sender.profile_picture.url if m.sender.profile_picture else None,
            'content': m.content,
            'created_at': m.created_at.isoformat(),
            'is_read': m.is_read,
            'type': 'text'
        } for m in msgs]

    @database_sync_to_async
    def save_message(self, content):
        conversation = Conversation.objects.get(id=self.conversation_id)
        msg = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content,
            type='text'
        )
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])
        return msg

    @database_sync_to_async
    def mark_as_read(self, message_id):
        """Mark a specific message as read"""
        try:
            message = Message.objects.get(
                id=message_id,
                conversation_id=self.conversation_id
            )
            # Only mark as read if the current user is NOT the sender
            if message.sender.id != self.user.id:
                message.is_read = True
                message.read_at = timezone.now()
                message.save(update_fields=['is_read', 'read_at'])
                return True
            return False
        except Message.DoesNotExist:
            return False# ============================================
# chat/consumers.py - COMPLETE UPDATED VERSION
# ============================================
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Conversation, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        # Verify participant
        if not await self.is_participant():
            await self.close()
            return

        # Join group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Notify online
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': str(self.user.id),  # Ensure string for consistency
                'is_online': True
            }
        )

        # Send recent messages
        recent = await self.get_recent_messages()
        await self.send(text_data=json.dumps({
            'type': 'messages_loaded',
            'messages': recent
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name') and hasattr(self, 'user'):
            # Notify offline
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': str(self.user.id),
                    'is_online': False
                }
            )
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except:
            return

        msg_type = data.get('type')

        if msg_type == 'new_message':
            content = data.get('message', {}).get('content', '').strip()
            if not content:
                return

            message = await self.save_message(content)

            broadcast_msg = {
                'id': message.id,
                'sender_id': str(message.sender.id),
                'sender_name': message.sender.shop_name or message.sender.email,
                'sender_profile': message.sender.profile_picture.url if message.sender.profile_picture else None,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'is_read': False,
                'type': 'text'
            }

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'new_message',
                    'message': broadcast_msg
                }
            )

        elif msg_type == 'typing_indicator':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': str(data.get('user_id', self.user.id)),
                    'is_typing': data.get('is_typing', False)
                }
            )

        elif msg_type == 'message_read':
            message_id = data.get('message_id')
            if message_id:
                await self.mark_as_read(message_id)
                # Broadcast read receipt to ALL users in conversation
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_read',
                        'message_id': message_id
                    }
                )

        elif msg_type == 'user_online':
            # Handle explicit online status
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': str(data.get('user_id', self.user.id)),
                    'is_online': True
                }
            )

        elif msg_type == 'user_offline':
            # Handle explicit offline status
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': str(data.get('user_id', self.user.id)),
                    'is_online': False
                }
            )

    # Handlers - These receive events from channel layer and send to WebSocket
    async def new_message(self, event):
        """Send new message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message']
        }))

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket (except to the typer themselves)"""
        # Don't send typing indicator back to the person who's typing
        if str(event.get('user_id')) != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'is_typing': event['is_typing']
            }))

    async def message_read(self, event):
        """Send read receipt to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'message_id': event['message_id']
        }))

    async def user_status(self, event):
        """Send user online/offline status to WebSocket (except to themselves)"""
        # Don't send status update back to the user themselves
        if str(event.get('user_id')) != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'user_id': event['user_id'],
                'is_online': event['is_online']
            }))

    # DB Helpers
    @database_sync_to_async
    def is_participant(self):
        return Conversation.objects.filter(
            id=self.conversation_id,
            participants=self.user
        ).exists()

    @database_sync_to_async
    def get_recent_messages(self):
        msgs = Message.objects.filter(conversation_id=self.conversation_id)\
            .select_related('sender')\
            .order_by('created_at')[:100]
        return [{
            'id': m.id,
            'sender_id': str(m.sender.id),
            'sender_name': m.sender.shop_name or m.sender.email,
            'sender_profile': m.sender.profile_picture.url if m.sender.profile_picture else None,
            'content': m.content,
            'created_at': m.created_at.isoformat(),
            'is_read': m.is_read,
            'type': 'text'
        } for m in msgs]

    @database_sync_to_async
    def save_message(self, content):
        conversation = Conversation.objects.get(id=self.conversation_id)
        msg = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content,
            type='text'
        )
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])
        return msg

    @database_sync_to_async
    def mark_as_read(self, message_id):
        """Mark a specific message as read"""
        try:
            message = Message.objects.get(
                id=message_id,
                conversation_id=self.conversation_id
            )
            # Only mark as read if the current user is NOT the sender
            if message.sender.id != self.user.id:
                message.is_read = True
                message.read_at = timezone.now()
                message.save(update_fields=['is_read', 'read_at'])
                return True
            return False
        except Message.DoesNotExist:
            return False