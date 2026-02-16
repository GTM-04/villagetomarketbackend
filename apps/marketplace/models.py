"""
Marketplace models - Orders and transactions.
"""

from django.db import models
from apps.core.models import TimestampedModel, UUIDModel
from apps.users.models import User
from apps.listings.models import Listing


class Order(UUIDModel, TimestampedModel):
    """
    Order placed by buyer for a listing.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Order number
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # Parties
    buyer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='orders_as_buyer'
    )
    farmer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='orders_as_farmer'
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    
    # Order details
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='ZWL')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Delivery
    delivery_method = models.CharField(
        max_length=20,
        choices=[('pickup', 'Pickup'), ('delivery', 'Delivery')]
    )
    delivery_address = models.TextField(blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    
    # Notes
    buyer_notes = models.TextField(blank=True)
    farmer_notes = models.TextField(blank=True)
    
    # Timestamps
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'orders'
        indexes = [
            models.Index(fields=['buyer', '-created_at']),
            models.Index(fields=['farmer', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
    
    def __str__(self):
        return f"Order {self.order_number} - {self.buyer.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = f"ORD{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate total if not set
        if not self.total_amount:
            self.total_amount = float(self.quantity) * float(self.unit_price)
        
        super().save(*args, **kwargs)


class Transaction(UUIDModel, TimestampedModel):
    """
    Payment transaction for orders.
    """
    TRANSACTION_TYPE_CHOICES = [
        ('payment', 'Payment'),
        ('refund', 'Refund'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='ZWL')
    
    payment_method = models.CharField(max_length=50)
    payment_reference = models.CharField(max_length=255, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['order', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
        ordering = ['-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
    
    def __str__(self):
        return f"Transaction {self.id} - {self.order.order_number}"
