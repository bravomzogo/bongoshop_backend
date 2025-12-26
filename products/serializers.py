# products/serializers.py - Updated version without currency field

from rest_framework import serializers
from .models import Product, ProductImage, Rating, Reel, ReelComment, ReelLike
from accounts.serializers import UserSerializer
import cloudinary.uploader
import json


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image_url', 'created_at')
        read_only_fields = ('id', 'created_at')


class RatingSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    buyer_name = serializers.CharField(source='buyer.shop_name', read_only=True)

    class Meta:
        model = Rating
        fields = ('id', 'product', 'buyer', 'buyer_name', 'rating', 'comment', 'created_at')
        read_only_fields = ('buyer',)

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def create(self, validated_data):
        validated_data['buyer'] = self.context['request'].user
        return super().create(validated_data)


class ProductListSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    seller_name = serializers.CharField(source='seller.shop_name', read_only=True)
    seller_id = serializers.IntegerField(source='seller.id', read_only=True)
    average_rating = serializers.ReadOnlyField()
    total_ratings = serializers.ReadOnlyField()
    primary_image = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'description', 'region', 'primary_image', 
            'seller', 'seller_id', 'seller_name', 'average_rating', 'total_ratings', 
            'created_at', 'condition', 'is_active'
        ]
        read_only_fields = ('id', 'created_at')


class ProductDetailSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    seller_id = serializers.IntegerField(source='seller.id', read_only=True)
    average_rating = serializers.ReadOnlyField()
    total_ratings = serializers.ReadOnlyField()
    images = ProductImageSerializer(many=True, read_only=True)
    ratings = RatingSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'region', 'condition',
            'phone_number', 'images', 'image_url', 'seller', 'seller_id',
            'average_rating', 'total_ratings', 'ratings', 'created_at', 
            'updated_at', 'is_active',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')


class ProductCreateResponseSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    seller_id = serializers.IntegerField(source='seller.id', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()
    total_ratings = serializers.ReadOnlyField()
    ratings = RatingSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'region', 'condition',
            'phone_number', 'images', 'image_url', 'seller', 'seller_id',
            'average_rating', 'total_ratings', 'ratings', 'created_at', 
            'updated_at', 'is_active', 'location_lat',
            'location_lng', 'delivery_option', 'is_negotiable', 'is_featured'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')


class ProductCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(write_only=True, allow_null=False),
        required=True,
        allow_empty=False,
        max_length=10
    )

    class Meta:
        model = Product
        fields = (
            'name', 'description', 'price', 'region', 'condition',
            'phone_number', 'images', 'location_lat',
            'location_lng', 'delivery_option', 'is_negotiable'
        )
    
    def create(self, validated_data):
        image_files = validated_data.pop('images', [])
        validated_data['seller'] = self.context['request'].user
        product = Product.objects.create(**validated_data)

        uploaded_images = []
        for image_file in image_files:
            try:
                upload_result = cloudinary.uploader.upload(
                    image_file,
                    folder="bongoshop/products",
                    transformation=[
                        {'width': 1000, 'height': 1000, 'crop': 'limit'},
                        {'quality': "auto"},
                        {'fetch_format': "auto"}
                    ]
                )
                product_image = ProductImage.objects.create(
                    product=product,
                    image_url=upload_result['secure_url']
                )
                uploaded_images.append(product_image)
            except Exception as e:
                for img in uploaded_images:
                    img.delete()
                product.delete()
                raise serializers.ValidationError({"images": f"Upload failed: {str(e)}"})

        return product
    
    def to_representation(self, instance):
        return ProductCreateResponseSerializer(instance, context=self.context).data


class ReelListSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    seller_id = serializers.IntegerField(source='seller.id', read_only=True)
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Reel
        fields = [
            'id', 'title', 'description', 'price', 'video_url', 'thumbnail_url',
            'duration', 'views_count', 'likes_count', 'comments_count', 
            'shares_count', 'seller', 'seller_id', 'is_liked', 'created_at', 
            'phone_number'
        ]
        read_only_fields = [
            'id', 'views_count', 'likes_count', 'comments_count', 
            'shares_count', 'created_at', 'phone_number'
        ]
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class ReelCreateSerializer(serializers.ModelSerializer):
    video = serializers.FileField(write_only=True, allow_null=False)
    thumbnail = serializers.ImageField(write_only=True, allow_null=True, required=False)
    
    class Meta:
        model = Reel
        fields = ('title', 'description', 'price', 'video', 'thumbnail', 'phone_number')
    
    def create(self, validated_data):
        video_file = validated_data.pop('video')
        thumbnail_file = validated_data.pop('thumbnail', None)
        validated_data['seller'] = self.context['request'].user
        
        try:
            video_result = cloudinary.uploader.upload(
                video_file,
                folder="bongoshop/reels",
                resource_type="video",
                transformation=[
                    {'quality': "auto"},
                    {'fetch_format': "auto"}
                ]
            )
            validated_data['video_url'] = video_result['secure_url']
            validated_data['duration'] = int(video_result.get('duration', 0))
            
            if thumbnail_file:
                thumbnail_result = cloudinary.uploader.upload(
                    thumbnail_file,
                    folder="bongoshop/reels/thumbnails",
                    transformation=[
                        {'width': 720, 'height': 1280, 'crop': 'fill'},
                        {'quality': "auto"},
                        {'fetch_format': "auto"}
                    ]
                )
                validated_data['thumbnail_url'] = thumbnail_result['secure_url']
            else:
                validated_data['thumbnail_url'] = video_result['secure_url'].replace(
                    '/video/upload/', 
                    '/video/upload/so_0,w_720,h_1280,c_fill/'
                ).replace('.mp4', '.jpg')
            
            reel = Reel.objects.create(**validated_data)
            return reel
            
        except Exception as e:
            raise serializers.ValidationError({"video": f"Upload failed: {str(e)}"})
    
    def to_representation(self, instance):
        return ReelListSerializer(instance, context=self.context).data


class ReelCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_name = serializers.CharField(source='user.shop_name', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    
    class Meta:
        model = ReelComment
        fields = ('id', 'reel', 'user', 'user_id', 'user_name', 'text', 'created_at')
        read_only_fields = ('user',)
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        reel = validated_data['reel']
        reel.comments_count += 1
        reel.save()
        return super().create(validated_data)