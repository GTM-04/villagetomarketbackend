"""
Farmer admin configuration.
"""

from django.contrib import admin
from .models import FarmerProfile, FarmerRating


@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'farm_name',
        'verification_status',
        'average_rating',
        'total_listings',
        'active_listings',
        'created_at'
    ]
    list_filter = [
        'verification_status',
        'is_organic_certified',
        'created_at'
    ]
    search_fields = [
        'user__full_name',
        'user__phone_number',
        'farm_name'
    ]
    readonly_fields = [
        'total_listings',
        'active_listings',
        'successful_sales',
        'total_revenue',
        'average_rating',
        'total_ratings',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Farm Information', {
            'fields': (
                'farm_name',
                'farm_description',
                'farm_size',
                'farm_size_unit',
                'primary_crops',
                'farming_experience_years'
            )
        }),
        ('Certifications', {
            'fields': (
                'is_organic_certified',
                'certifications',
                'badges'
            )
        }),
        ('Statistics', {
            'fields': (
                'total_listings',
                'active_listings',
                'successful_sales',
                'total_revenue',
                'average_rating',
                'total_ratings'
            )
        }),
        ('Verification', {
            'fields': (
                'verification_status',
                'verification_documents',
                'verified_at',
                'verification_notes'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(FarmerRating)
class FarmerRatingAdmin(admin.ModelAdmin):
    list_display = [
        'farmer',
        'buyer',
        'rating',
        'created_at'
    ]
    list_filter = ['rating', 'created_at']
    search_fields = [
        'farmer__full_name',
        'buyer__full_name',
        'review'
    ]
    readonly_fields = ['created_at', 'updated_at']
