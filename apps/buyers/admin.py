"""
Buyer admin configuration.
"""

from django.contrib import admin
from .models import BuyerProfile, SavedListing, FollowedFarmer


@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'buyer_type',
        'business_name',
        'total_purchases',
        'total_spent',
        'created_at'
    ]
    list_filter = ['buyer_type', 'created_at']
    search_fields = [
        'user__full_name',
        'user__phone_number',
        'business_name'
    ]
    readonly_fields = [
        'total_purchases',
        'total_spent',
        'successful_transactions',
        'saved_listings_count',
        '  _count',
        'created_at',
        'updated_at'
    ]


@admin.register(SavedListing)
class SavedListingAdmin(admin.ModelAdmin):
    list_display = ['buyer', 'listing', 'created_at']
    list_filter = ['created_at']
    search_fields = [
        'buyer__full_name',
        'listing__title'
    ]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FollowedFarmer)
class FollowedFarmerAdmin(admin.ModelAdmin):
    list_display = [
        'buyer',
        'farmer',
        'notify_new_listings',
        'created_at'
    ]
    list_filter = ['notify_new_listings', 'created_at']
    search_fields = [
        'buyer__full_name',
        'farmer__full_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
