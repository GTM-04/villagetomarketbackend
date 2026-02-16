"""
Marketplace admin configuration.
"""

from django.contrib import admin
from .models import Order, Transaction


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number',
        'buyer',
        'farmer',
        'listing',
        'total_amount',
        'status',
        'created_at'
    ]
    list_filter = ['status', 'delivery_method', 'created_at']
    search_fields = [
        'order_number',
        'buyer__full_name',
        'farmer__full_name',
        'listing__title'
    ]
    readonly_fields = [
        'order_number',
        'created_at',
        'confirmed_at',
        'completed_at',
        'cancelled_at'
    ]
    raw_id_fields = ['buyer', 'farmer', 'listing']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'order',
        'transaction_type',
        'amount',
        'payment_method',
        'status',
        'created_at'
    ]
    list_filter = ['transaction_type', 'status', 'payment_method', 'created_at']
    search_fields = ['order__order_number', 'payment_reference']
    readonly_fields = ['created_at']
    raw_id_fields = ['order']
