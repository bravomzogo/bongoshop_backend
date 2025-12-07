# products/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Rating


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'seller',
        'price',
        'region',
        'condition',
        'is_active',
        'display_average_rating',   # ← fixed
        'total_ratings',
        'created_at'
    )
    list_filter = (
        'condition',
        'region',
        'is_active',
        'created_at',
    )
    search_fields = ('name', 'description', 'seller__email', 'seller__shop_name', 'phone_number')
    readonly_fields = ('created_at', 'updated_at', 'display_average_rating', 'total_ratings')
    raw_id_fields = ('seller',)

    fieldsets = (
        ('Product Info', {
            'fields': ('seller', 'name', 'description', 'price', 'region', 'condition', 'phone_number')
        }),
        ('Media', {
            'fields': ('image_url',),
            'description': 'Image uploaded via Cloudinary → URL appears here'
        }),
        ('Status & Stats', {
            'fields': ('is_active', 'display_average_rating', 'total_ratings', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('seller').prefetch_related('ratings')

    # Fixed method to display average rating
    def display_average_rating(self, obj):
        avg = obj.average_rating
        if avg > 0:
            stars = '★★★★★☆☆☆☆☆'[:int(avg)] + '☆' * (5 - int(avg))
            return format_html(f'<b>{avg}</b> {stars}')
        return "No ratings"
    display_average_rating.short_description = 'Avg Rating'


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'buyer', 'rating', 'comment_preview', 'created_at')
    list_filter = ('rating', 'created_at', 'product__region')
    search_fields = ('product__name', 'buyer__email', 'buyer__shop_name', 'comment')
    readonly_fields = ('created_at', 'updated_at')

    def comment_preview(self, obj):
        if len(obj.comment or '') > 50:
            return obj.comment[:50] + '...'
        return obj.comment or '—'
    comment_preview.short_description = 'Comment'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'buyer')



from .models import Reel, ReelLike, ReelComment

@admin.register(Reel)
class ReelAdmin(admin.ModelAdmin):
    list_display = ['title', 'seller', 'price', 'views_count', 'likes_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'seller__email']

@admin.register(ReelLike)
class ReelLikeAdmin(admin.ModelAdmin):
    list_display = ['reel', 'user', 'created_at']
    list_filter = ['created_at']

@admin.register(ReelComment)
class ReelCommentAdmin(admin.ModelAdmin):
    list_display = ['reel', 'user', 'text', 'created_at']
    list_filter = ['created_at']
    search_fields = ['text', 'user__email']