# chat/views.py

from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    MessageSerializer,
    CreateConversationSerializer,
)
from accounts.models import User
from products.models import Product
from rest_framework.parsers import MultiPartParser, FormParser
import cloudinary.uploader
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.conversations.all().prefetch_related(
            'participants', 'messages'
        )


class ConversationDetailView(generics.RetrieveAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.conversations.all()


class CreateConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        other_user_id = serializer.validated_data['other_user_id']
        product_id = serializer.validated_data.get('product_id')

        if other_user_id == request.user.id:
            return Response(
                {'detail': 'Cannot create conversation with yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        other_user = get_object_or_404(User, id=other_user_id)
        product = None
        if product_id:
            product = get_object_or_404(Product, id=product_id)

        conversation = Conversation.get_or_create_conversation(
            request.user, other_user, product
        )

        serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=self.request.user
        )
        return conversation.messages.all().select_related('sender')


# FIXED: Only ONE MarkMessagesReadView
class MarkConversationReadView(APIView):
    """Mark all unread messages in a conversation as read"""
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user
        )

        # Mark all unread messages from the other user as read
        updated_count = conversation.messages.filter(
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)

        return Response({
            'detail': 'Messages marked as read',
            'marked_count': updated_count
        }, status=status.HTTP_200_OK)


class CreateMessageView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        conversation_id = self.request.data.get('conversation')
        conversation = get_object_or_404(Conversation, id=conversation_id)

        if self.request.user not in conversation.participants.all():
            raise permissions.PermissionDenied("You are not part of this conversation.")

        message = serializer.save(sender=self.request.user, conversation=conversation)

        # Broadcast the message to WebSocket group
        channel_layer = get_channel_layer()
        broadcast_msg = {
            'id': message.id,
            'sender_id': message.sender.id,
            'sender_name': message.sender.shop_name or message.sender.email,
            'sender_profile': message.sender.profile_picture.url if hasattr(message.sender, 'profile_picture') and message.sender.profile_picture else None,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'is_read': False,
            'type': 'text'
        }

        async_to_sync(channel_layer.group_send)(
            f'chat_{conversation.id}',
            {
                'type': 'new_message',
                'message': broadcast_msg
            }
        )


class FileUploadView(generics.CreateAPIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist('files')
        types = request.POST.getlist('types')
        conversation_id = request.POST.get('conversation')

        if not conversation_id:
            return Response({'detail': 'Conversation ID required.'}, status=400)

        conversation = get_object_or_404(Conversation, id=conversation_id)
        if request.user not in conversation.participants.all():
            return Response({'detail': 'Not authorized.'}, status=403)

        uploaded = []
        for file, file_type in zip(files, types):
            try:
                result = cloudinary.uploader.upload(
                    file,
                    folder=f"bongoshop/chat/{conversation_id}",
                    resource_type="auto"
                )
                message = Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=f"Sent a {file_type}",
                    type=file_type,
                    file_data={
                        'name': file.name,
                        'size': file.size,
                        'type': file.content_type,
                        'url': result['secure_url']
                    }
                )
                
                # Broadcast file message too
                channel_layer = get_channel_layer()
                broadcast_msg = {
                    'id': message.id,
                    'sender_id': message.sender.id,
                    'sender_name': message.sender.shop_name or message.sender.email,
                    'sender_profile': message.sender.profile_picture.url if hasattr(message.sender, 'profile_picture') and message.sender.profile_picture else None,
                    'content': message.content,
                    'created_at': message.created_at.isoformat(),
                    'is_read': False,
                    'type': file_type,
                    'file_data': message.file_data
                }

                async_to_sync(channel_layer.group_send)(
                    f'chat_{conversation.id}',
                    {
                        'type': 'new_message',
                        'message': broadcast_msg
                    }
                )
                
                uploaded.append(MessageSerializer(message).data)
            except Exception as e:
                return Response({'detail': str(e)}, status=500)

        return Response(uploaded, status=201)