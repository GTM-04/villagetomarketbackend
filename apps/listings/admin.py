"""
Listings admin configuration.
"""

from django.contrib import admin
from .models import Category, ProduceType, Listing, ListingImage, ListingView


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']


@admin.register(ProduceType)
class ProduceTypeAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'category',
        'typical_price_min',
        'typical_price_max',
        'is_active'
    ]
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1
    fields = ['image', 'caption', 'order', 'is_primary']


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = [
        'listing_number',
        'title',
        'farmer',
        'category',
        'price_per_unit',
        'status',
        'view_count',
        'created_at'
    ]
    list_filter = [
        'status',
        'category',
        'district',
        'is_organic',
        'created_at'
    ]
    search_fields = [
        'listing_number',
        'title',
        'description',
        'farmer__full_name',
        'farmer__phone_number'
    ]
    readonly_fields = [
        'listing_number',
        'view_count',
        'inquiry_count',
        'share_count',
        'save_count',
        'created_at',
        'updated_at'
    ]
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ListingImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'listing_number',
                'farmer',
                'title',
                'description',
                'slug'
            )
        }),
        ('Produce Details', {
            'fields': (
                'category',
                'produce_type',
                'variety',
                'grade',
                'is_organic',
                'quality_tags'
            )
        }),
        ('Quantity & Pricing', {
            'fields': (
                'quantity_available',
                'unit',
                'minimum_order',
                'price_per_unit',
                'currency',
                'is_negotiable'
            )
        }),
        ('Location', {
            'fields': (
                'district',
                'farm_location',
                'latitude',
                'longitude'
            )
        }),
        ('Availability', {
            'fields': (
                'available_from',
                'available_until',
                'harvest_date',
                'delivery_available',
                'delivery_radius_km',
                'pickup_available'
            )
        }),
        ('Status', {
            'fields': ('status', 'published_at')
        }),
        ('Statistics', {
            'fields': (
                'view_count',
                'inquiry_count',
                'share_count',
                'save_count'
            )
        }),
        ('Sync', {
            'fields': ('version', 'last_synced_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ['listing', 'order', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['listing__title', 'caption']


@admin.register(ListingView)
class ListingViewAdmin(admin.ModelAdmin):
    list_display = ['listing', 'viewer', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['listing__title', 'viewer__full_name', 'ip_address']
    readonly_fields = ['viewed_at']
