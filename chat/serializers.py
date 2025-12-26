# chat/serializers.py
from rest_framework import serializers
from .models import Conversation, Message
from accounts.serializers import UserSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ('id', 'sender', 'content', 'is_read', 'read_at', 'created_at')
        read_only_fields = ('id', 'sender', 'created_at')


class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = MessageSerializer(read_only=True)
    other_user = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    product_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ('id', 'participants', 'other_user', 'product', 'product_info', 
                  'last_message', 'unread_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_other_user(self, obj):
        request = self.context.get('request')
        if request and request.user:
            other_user = obj.get_other_user(request.user)
            if other_user:
                return UserSerializer(other_user).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.unread_count(request.user)
        return 0
    
    def get_product_info(self, obj):
        if obj.product:
            return {
                'id': obj.product.id,
                'name': obj.product.name,
                'price': str(obj.product.price),
                'image': obj.product.primary_image
            }
        return None


class CreateConversationSerializer(serializers.Serializer):
    other_user_id = serializers.IntegerField()
    product_id = serializers.IntegerField(required=False, allow_null=True)






class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    sender_name = serializers.CharField(source='sender.shop_name', read_only=True)
    sender_profile = serializers.CharField(source='sender.profile_picture_url', read_only=True, allow_null=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender_id', 'sender_name', 'sender_profile',
            'content', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'sender_id', 'sender_name', 'sender_profile', 'is_read', 'created_at']
        
    def create(self, validated_data):
        # sender and conversation are set in the view
        return Message.objects.create(**validated_data)