# chat/urls.py - SIMPLEST FIX
from django.urls import path
from .views import (
    ConversationListView,  # This will be both root AND conversations list
    ConversationDetailView,
    CreateConversationView,
    MessageListView,
    MarkConversationReadView,
    CreateMessageView,
    FileUploadView,
)

urlpatterns = [
    # ✅ Make conversations list the root (like products app)
    path('', ConversationListView.as_view(), name='chat-root'),
    
    # Keep the conversations/ path for consistency
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    
    # The rest stay the same
    path('conversations/create/', CreateConversationView.as_view(), name='create-conversation'),
    path('conversations/<int:pk>/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('conversations/<int:conversation_id>/messages/', MessageListView.as_view(), name='message-list'),
    path('conversations/<int:conversation_id>/mark-read/', MarkConversationReadView.as_view(), name='mark-conversation-read'),
    path('messages/create/', CreateMessageView.as_view(), name='create-message'),
    path('files/upload/', FileUploadView.as_view(), name='file-upload'),
]