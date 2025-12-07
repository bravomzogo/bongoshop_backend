# products/urls.py
from django.urls import path
from .views import (
    ProductListView, ProductDetailView, ProductCreateView,
    SellerProductListView, MyProductsView, ProductUpdateView, ProductDeleteView,
    RatingCreateView, RatingUpdateView, RatingDeleteView, ProductRatingsView,
    ReelListView, ReelDetailView, ReelCreateView, MyReelsView, ReelDeleteView,
    ReelLikeToggleView, ReelCommentsView, ReelCommentCreateView, ReelCommentDeleteView,ReelShareView
)

urlpatterns = [
    # Product endpoints
    path('', ProductListView.as_view(), name='product-list'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('create/', ProductCreateView.as_view(), name='product-create'),
    path('my-products/', MyProductsView.as_view(), name='my-products'),
    path('<int:pk>/update/', ProductUpdateView.as_view(), name='product-update'),
    path('<int:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),
    path('seller/<int:seller_id>/', SellerProductListView.as_view(), name='seller-products'),
    
    # Rating endpoints
    path('ratings/create/', RatingCreateView.as_view(), name='rating-create'),
    path('ratings/<int:pk>/update/', RatingUpdateView.as_view(), name='rating-update'),
    path('ratings/<int:pk>/delete/', RatingDeleteView.as_view(), name='rating-delete'),
    path('<int:product_id>/ratings/', ProductRatingsView.as_view(), name='product-ratings'),

    # Reel endpoints
    path('reels/', ReelListView.as_view(), name='reel-list'),
    path('reels/<int:pk>/', ReelDetailView.as_view(), name='reel-detail'),
    path('reels/create/', ReelCreateView.as_view(), name='reel-create'),
    path('reels/my-reels/', MyReelsView.as_view(), name='my-reels'),
    path('reels/<int:pk>/delete/', ReelDeleteView.as_view(), name='reel-delete'),
    path('reels/<int:reel_id>/like/', ReelLikeToggleView.as_view(), name='reel-like'),
    path('reels/<int:reel_id>/comments/', ReelCommentsView.as_view(), name='reel-comments'),
    path('reels/comments/create/', ReelCommentCreateView.as_view(), name='reel-comment-create'),
    path('reels/comments/<int:pk>/delete/', ReelCommentDeleteView.as_view(), name='reel-comment-delete'),
    path('reels/<int:reel_id>/share/', ReelShareView.as_view(), name='reel-share'),
]