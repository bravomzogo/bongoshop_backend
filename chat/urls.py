# chat/urls.py - UPDATED WITH SLASH REDIRECTS
from django.urls import path
from django.views.generic import RedirectView
from .views import (
    ConversationListView,
    ConversationDetailView,
    CreateConversationView,
    MessageListView,
    MarkConversationReadView,
    CreateMessageView,
    FileUploadView,
)

urlpatterns = [
    # Root with and without slash
    path('', ConversationListView.as_view(), name='chat-root'),
    path('', ConversationListView.as_view(), name='chat-root-no-slash'),  # Also handle no slash
    
    # Conversations with BOTH patterns
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('conversations', ConversationListView.as_view(), name='conversation-list-no-slash'),  # Add this!
    
    # The rest with slashes (should be fine)
    path('conversations/create/', CreateConversationView.as_view(), name='create-conversation'),
    path('conversations/<int:pk>/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('conversations/<int:conversation_id>/messages/', MessageListView.as_view(), name='message-list'),
    path('conversations/<int:conversation_id>/mark-read/', MarkConversationReadView.as_view(), name='mark-conversation-read'),
    path('messages/create/', CreateMessageView.as_view(), name='create-message'),
    path('files/upload/', FileUploadView.as_view(), name='file-upload'),
]