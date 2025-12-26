# chat/urls.py
from django.urls import path
from .views import (
    ConversationListView,
    ConversationDetailView,
    CreateConversationView,
    MessageListView,
    MarkConversationReadView,  # ← Renamed for clarity
    CreateMessageView,
    FileUploadView,
)

urlpatterns = [
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('conversations/create/', CreateConversationView.as_view(), name='create-conversation'),
    path('conversations/<int:pk>/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('conversations/<int:conversation_id>/messages/', MessageListView.as_view(), name='message-list'),
    
    # NEW: Clean, simple endpoint
    path('conversations/<int:conversation_id>/mark-read/', MarkConversationReadView.as_view(), name='mark-conversation-read'),
    
    path('messages/create/', CreateMessageView.as_view(), name='create-message'),
    path('files/upload/', FileUploadView.as_view(), name='file-upload'),
    
]