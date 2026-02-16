"""
Buyer models - Extended profiles for buyer users.
"""

from django.db import models
from apps.core.models import TimestampedModel
from apps.users.models import User


class BuyerProfile(TimestampedModel):
    """
    Extended profile for buyers.
    """
    BUYER_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('restaurant', 'Restaurant'),
        ('retailer', 'Retailer'),
        ('wholesaler', 'Wholesaler'),
        ('institution', 'Institution'),
        ('exporter', 'Exporter'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='buyer_profile'
    )
    
    # Business details
    business_name = models.CharField(max_length=255, blank=True)
    buyer_type = models.CharField(
        max_length=20,
        choices=BUYER_TYPE_CHOICES,
        default='individual'
    )
    business_registration = models.CharField(max_length=100, blank=True)
    business_description = models.TextField(blank=True, max_length=1000)
    
    # Preferences
    preferred_categories = models.JSONField(
        default=list,
        help_text="Preferred produce categories"
    )
    preferred_districts = models.JSONField(
        default=list,
        help_text="Preferred sourcing locations"
    )
    preferred_delivery_method = models.CharField(
        max_length=20,
        default='pickup',
        choices=[
            ('pickup', 'Pickup'),
            ('delivery', 'Delivery'),
            ('both', 'Both'),
        ]
    )
    
    # Statistics
    total_purchases = models.IntegerField(default=0)
    total_spent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    successful_transactions = models.IntegerField(default=0)
    
    # Favorites
    saved_listings_count = models.IntegerField(default=0)
    followed_farmers_count = models.IntegerField(default=0)
    
    # Buyer rating (for farmers to rate buyers)
    buyer_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0
    )
    
    class Meta:
        db_table = 'buyer_profiles'
        verbose_name = 'Buyer Profile'
        verbose_name_plural = 'Buyer Profiles'
    
    def __str__(self):
        business_name = f" - {self.business_name}" if self.business_name else ""
        return f"Buyer: {self.user.full_name}{business_name}"


class SavedListing(TimestampedModel):
    """
    Buyer's saved/wishlisted listings.
    """
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_listings'
    )
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='saved_by'
    )
    notes = models.TextField(blank=True, max_length=500)
    
    class Meta:
        db_table = 'saved_listings'
        unique_together = ['buyer', 'listing']
        indexes = [
            models.Index(fields=['buyer', '-created_at']),
        ]
        ordering = ['-created_at']
        verbose_name = 'Saved Listing'
        verbose_name_plural = 'Saved Listings'
    
    def __str__(self):
        return f"{self.buyer.full_name} saved {self.listing.title}"


class FollowedFarmer(TimestampedModel):
    """
    Buyer following farmers to get updates.
    """
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followed_farmers'
    )
    farmer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers'
    )
    notify_new_listings = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'followed_farmers'
        unique_together = ['buyer', 'farmer']
        indexes = [
            models.Index(fields=['buyer']),
            models.Index(fields=['farmer']),
        ]
        ordering = ['-created_at']
        verbose_name = 'Followed Farmer'
        verbose_name_plural = 'Followed Farmers'
    
    def __str__(self):
        return f"{self.buyer.full_name} follows {self.farmer.full_name}"
