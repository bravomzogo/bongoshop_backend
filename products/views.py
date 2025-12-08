# products/views.py

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from .models import Product, ProductImage, Rating
from .serializers import (
    ProductListSerializer, 
    ProductDetailSerializer, 
    ProductCreateSerializer,
    ProductCreateResponseSerializer,
    RatingSerializer
)
from .models import Reel, ReelLike, ReelComment
from .serializers import ReelListSerializer, ReelCreateSerializer, ReelCommentSerializer


from django.db.models import Count
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Reel, ReelLike, ReelComment
from .serializers import ReelListSerializer, ReelCreateSerializer, ReelCommentSerializer
import json


class ProductListView(generics.ListAPIView):
    """List all active products (public access)"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by region(s) if provided
        regions = self.request.query_params.getlist('region', [])
        if regions:
            # If regions is a string, split it by commas
            if isinstance(regions, str):
                regions = [r.strip() for r in regions.split(',')]
            queryset = queryset.filter(region__in=regions)
        
        # Filter by condition
        condition = self.request.query_params.get('condition', None)
        if condition:
            queryset = queryset.filter(condition=condition)
        
        # Search by name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset


class ProductDetailView(generics.RetrieveAPIView):
    """Get product details (public access)"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductDetailSerializer
    
    def get_serializer_context(self):
        """Add context to make RelatedManager iterable"""
        context = super().get_serializer_context()
        return context


class ProductCreateView(generics.CreateAPIView):
    """Create a product (sellers only - must be authenticated and verified)"""
    serializer_class = ProductCreateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def perform_create(self, serializer):
        if not self.request.user.is_email_verified:
            raise PermissionDenied("Email must be verified to create products")
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        """Override to handle both success and error responses properly"""
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class SellerProductListView(generics.ListAPIView):
    """List all products of a specific seller"""
    serializer_class = ProductListSerializer
    
    def get_queryset(self):
        seller_id = self.kwargs.get('seller_id')
        return Product.objects.filter(seller_id=seller_id, is_active=True)


class MyProductsView(generics.ListAPIView):
    """List products of the authenticated seller"""
    serializer_class = ProductDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user)


class ProductUpdateView(generics.UpdateAPIView):
    """Update a product (only by owner)"""
    serializer_class = ProductCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user)


class ProductDeleteView(generics.DestroyAPIView):
    """Delete/deactivate a product (only by owner)"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user)
    
    def perform_destroy(self, instance):
        # Soft delete - just mark as inactive
        instance.is_active = False
        instance.save()


class RatingCreateView(generics.CreateAPIView):
    """Create a rating for a product (buyers only - must be authenticated)"""
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        product_id = self.request.data.get('product')
        product = get_object_or_404(Product, id=product_id)
        
        # Prevent sellers from rating their own products
        if product.seller == self.request.user:
            raise PermissionDenied("You cannot rate your own product")
        
        # Check if user already rated this product
        if Rating.objects.filter(product=product, buyer=self.request.user).exists():
            raise ValidationError({"detail": "You have already rated this product"})
        
        serializer.save()


class RatingUpdateView(generics.UpdateAPIView):
    """Update a rating (only by the rating creator)"""
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Rating.objects.filter(buyer=self.request.user)


class RatingDeleteView(generics.DestroyAPIView):
    """Delete a rating (only by the rating creator)"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Rating.objects.filter(buyer=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProductRatingsView(generics.ListAPIView):
    """List all ratings for a specific product"""
    serializer_class = RatingSerializer
    
    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        return Rating.objects.filter(product_id=product_id)






# Add this to ReelListView to get is_liked context
class ReelListView(generics.ListAPIView):
    """List all active reels (public access)"""
    serializer_class = ReelListSerializer
    
    def get_queryset(self):
        return Reel.objects.filter(is_active=True).annotate(
            like_count=Count('likes'),
            comment_count=Count('comments')
        )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ReelDetailView(generics.RetrieveAPIView):
    """Get reel details and increment view count"""
    queryset = Reel.objects.filter(is_active=True)
    serializer_class = ReelListSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ReelCreateView(generics.CreateAPIView):
    """Create a reel (sellers only - must be authenticated and verified)"""
    serializer_class = ReelCreateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def perform_create(self, serializer):
        if not self.request.user.is_email_verified:
            raise PermissionDenied("Email must be verified to create reels")
        serializer.save()


class MyReelsView(generics.ListAPIView):
    """List reels of the authenticated seller"""
    serializer_class = ReelListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Reel.objects.filter(seller=self.request.user)


class ReelDeleteView(generics.DestroyAPIView):
    """Delete/deactivate a reel (only by owner)"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Reel.objects.filter(seller=self.request.user)
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.is_active = False
        instance.save()


# Add this new view for sharing
class ReelShareView(APIView):
    """Increment share count for a reel"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def post(self, request, reel_id):
        reel = get_object_or_404(Reel, id=reel_id, is_active=True)
        
        # Increment share count
        reel.shares_count += 1
        reel.save(update_fields=['shares_count'])
        
        return Response({
            'success': True,
            'message': 'Share recorded',
            'shares_count': reel.shares_count
        })

# Update ReelLikeToggleView to use context
class ReelLikeToggleView(APIView):
    """Toggle like on a reel"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, reel_id):
        reel = get_object_or_404(Reel, id=reel_id, is_active=True)
        user = request.user
        
        like, created = ReelLike.objects.get_or_create(reel=reel, user=user)
        
        if not created:
            # Unlike
            like.delete()
            reel.likes_count = max(0, reel.likes_count - 1)
            reel.save()
            return Response({
                'liked': False, 
                'likes_count': reel.likes_count,
                'is_liked': False
            })
        else:
            # Like
            reel.likes_count += 1
            reel.save()
            return Response({
                'liked': True, 
                'likes_count': reel.likes_count,
                'is_liked': True
            })


class ReelCommentsView(generics.ListAPIView):
    """List comments for a reel"""
    serializer_class = ReelCommentSerializer
    
    def get_queryset(self):
        reel_id = self.kwargs.get('reel_id')
        return ReelComment.objects.filter(reel_id=reel_id)


class ReelCommentCreateView(generics.CreateAPIView):
    """Create a comment on a reel"""
    serializer_class = ReelCommentSerializer
    permission_classes = [IsAuthenticated]


class ReelCommentDeleteView(generics.DestroyAPIView):
    """Delete a comment (only by comment creator)"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ReelComment.objects.filter(user=self.request.user)
    
    def perform_destroy(self, instance):
        # Decrement comments count
        reel = instance.reel
        reel.comments_count = max(0, reel.comments_count - 1)
        reel.save()
        instance.delete()