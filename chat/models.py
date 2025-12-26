# chat/models.py
from django.db import models
from django.conf import settings
from django.db.models import Q

class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation {self.id}"
    
    @property
    def last_message(self):
        return self.messages.first()
    
    def get_other_user(self, user):
        """Get the other participant in the conversation"""
        return self.participants.exclude(id=user.id).first()
    
    def unread_count(self, user):
        """Get unread message count for a specific user"""
        return self.messages.filter(
            ~Q(sender=user),
            is_read=False
        ).count()
    
    @classmethod
    def get_or_create_conversation(cls, user1, user2, product=None):
        """Get existing conversation or create new one"""
        # Find conversation with these two users
        conversations = cls.objects.filter(
            participants=user1
        ).filter(
            participants=user2
        )
        
        if product:
            conversations = conversations.filter(product=product)
        
        conversation = conversations.first()
        
        if not conversation:
            conversation = cls.objects.create(product=product)
            conversation.participants.add(user1, user2)
        
        return conversation


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.sender.shop_name} in conversation {self.conversation.id}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
