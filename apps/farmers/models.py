"""
Farmer models - Extended profiles for farmer users.
"""

from django.db import models
from apps.core.models import TimestampedModel
from apps.users.models import User


class FarmerProfile(TimestampedModel):
    """
    Extended profile for farmers.
    """
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    FARM_SIZE_UNIT_CHOICES = [
        ('hectares', 'Hectares'),
        ('acres', 'Acres'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='farmer_profile'
    )
    
    # Farm details
    farm_name = models.CharField(max_length=255, blank=True)
    farm_size = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Farm size in selected unit"
    )
    farm_size_unit = models.CharField(
        max_length=20,
        default='hectares',
        choices=FARM_SIZE_UNIT_CHOICES
    )
    farm_description = models.TextField(blank=True, max_length=1000)
    
    # Crops grown
    primary_crops = models.JSONField(
        default=list,
        help_text="List of primary crop types"
    )
    
    # Certifications
    is_organic_certified = models.BooleanField(default=False)
    certifications = models.JSONField(default=list, blank=True)
    farming_experience_years = models.IntegerField(null=True, blank=True)
    
    # Statistics
    total_listings = models.IntegerField(default=0)
    active_listings = models.IntegerField(default=0)
    successful_sales = models.IntegerField(default=0)
    total_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Rating
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        help_text="Average rating from buyers (0-5)"
    )
    total_ratings = models.IntegerField(default=0)
    
    # Verification
    verification_status = models.CharField(
        max_length=20,
        default='pending',
        choices=VERIFICATION_STATUS_CHOICES
    )
    verification_documents = models.JSONField(default=list, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    
    # Badges and achievements
    badges = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'farmer_profiles'
        indexes = [
            models.Index(fields=['verification_status']),
            models.Index(fields=['-average_rating']),
            models.Index(fields=['-total_listings']),
        ]
        verbose_name = 'Farmer Profile'
        verbose_name_plural = 'Farmer Profiles'
    
    def __str__(self):
        return f"Farmer: {self.user.full_name}"
    
    def update_stats(self):
        """Update farmer statistics."""
        from apps.listings.models import Listing
        
        listings = Listing.objects.filter(farmer=self.user)
        self.total_listings = listings.count()
        self.active_listings = listings.filter(status='active').count()
        self.save(update_fields=['total_listings', 'active_listings'])


class FarmerRating(TimestampedModel):
    """
    Ratings given to farmers by buyers.
    """
    farmer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_ratings'
    )
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='given_ratings'
    )
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Rating (1-5 stars)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    review = models.TextField(blank=True, max_length=500)
    
    # Response from farmer
    farmer_response = models.TextField(blank=True, max_length=500)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'farmer_ratings'
        unique_together = ['farmer', 'buyer', 'listing']
        indexes = [
            models.Index(fields=['farmer', '-created_at']),
            models.Index(fields=['rating']),
        ]
        ordering = ['-created_at']
        verbose_name = 'Farmer Rating'
        verbose_name_plural = 'Farmer Ratings'
    
    def __str__(self):
        return f"{self.rating}⭐ for {self.farmer.full_name}"
    
    def save(self, *args, **kwargs):
        """Update farmer's average rating when saving."""
        super().save(*args, **kwargs)
        self._update_farmer_rating()
    
    def _update_farmer_rating(self):
        """Recalculate farmer's average rating."""
        from django.db.models import Avg, Count
        
        stats = FarmerRating.objects.filter(farmer=self.farmer).aggregate(
            avg_rating=Avg('rating'),
            total=Count('id')
        )
        
        profile = self.farmer.farmer_profile
        profile.average_rating = stats['avg_rating'] or 0
        profile.total_ratings = stats['total']
        profile.save(update_fields=['average_rating', 'total_ratings'])
