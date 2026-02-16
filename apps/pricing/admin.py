"""
Pricing admin configuration.
"""

from django.contrib import admin
from .models import MarketPrice, PriceTrend, PriceAlert


@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    list_display = [
        'produce_type',
        'district',
        'price_min',
        'price_avg',
        'price_max',
        'recorded_date',
        'source'
    ]
    list_filter = ['district', 'source', 'recorded_date']
    search_fields = ['produce_type__name', 'district']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'recorded_date'


@admin.register(PriceTrend)
class PriceTrendAdmin(admin.ModelAdmin):
    list_display = [
        'produce_type',
        'district',
        'trend_direction',
        'price_change_percent',
        'period_start',
        'period_end'
    ]
    list_filter = ['trend_direction', 'district', 'period_end']
    search_fields = ['produce_type__name', 'district']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'produce_type',
        'district',
        'alert_type',
        'target_price',
        'is_active',
        'trigger_count'
    ]
    list_filter = ['alert_type', 'is_active', 'district']
    search_fields = ['user__full_name', 'produce_type__name']
    readonly_fields = ['created_at', 'updated_at', 'last_triggered_at', 'trigger_count']
