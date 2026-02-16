"""
Listing models - Core marketplace functionality.
"""

from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from apps.core.models import TimestampedModel, UUIDModel
from apps.users.models import User
from apps.core.validators import validate_positive_number


class Category(TimestampedModel):
    """
    Produce categories (Vegetables, Fruits, Grains, etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class or emoji")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'order']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class ProduceType(TimestampedModel):
    """
    Specific produce types under categories (e.g., Tomatoes under Vegetables).
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='produce_types'
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    common_units = models.JSONField(
        default=list,
        help_text="Common units: ['kg', 'tonnes', 'bags']"
    )
    typical_price_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    typical_price_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'produce_types'
        unique_together = ['category', 'slug']
        ordering = ['name']
        verbose_name = 'Produce Type'
        verbose_name_plural = 'Produce Types'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Listing(UUIDModel, TimestampedModel):
    """
    Product listing created by farmers.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]
    
    UNIT_CHOICES = [
        ('kg', 'Kilograms'),
        ('g', 'Grams'),
        ('tonnes', 'Tonnes'),
        ('bags', 'Bags'),
        ('crates', 'Crates'),
        ('trays', 'Trays'),
        ('bundles', 'Bundles'),
        ('pieces', 'Pieces'),
        ('heads', 'Heads'),
        ('litres', 'Litres'),
    ]
    
    # Unique identifier
    listing_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # Farmer
    farmer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='listings'
    )
    
    # Produce details
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    produce_type = models.ForeignKey(ProduceType, on_delete=models.PROTECT)
    variety = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., Roma tomatoes, Yellow maize"
    )
    grade = models.CharField(
        max_length=50,
        blank=True,
        help_text="Grade A, Premium, Export Quality, etc."
    )
    
    # Quantity
    quantity_available = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    minimum_order = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum order quantity"
    )
    
    # Pricing
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    currency = models.CharField(max_length=3, default='ZWL')
    is_negotiable = models.BooleanField(default=False)
    
    # Description
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Quality indicators
    is_organic = models.BooleanField(default=False)
    quality_tags = models.JSONField(
        default=list,
        blank=True,
        help_text="['fresh', 'pesticide-free', 'locally-grown']"
    )
    
    # Location
    farm_location = models.CharField(max_length=255, blank=True)
    district = models.CharField(max_length=100)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    
    # Availability
    available_from = models.DateField()
    available_until = models.DateField()
    harvest_date = models.DateField(null=True, blank=True)
    delivery_available = models.BooleanField(default=False)
    delivery_radius_km = models.IntegerField(null=True, blank=True)
    pickup_available = models.BooleanField(default=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Statistics
    view_count = models.IntegerField(default=0)
    inquiry_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    save_count = models.IntegerField(default=0)
    
    # SEO
    slug = models.SlugField(max_length=255, blank=True)
    
    # Sync tracking (for offline)
    version = models.IntegerField(default=1)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    
    # Publishing
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'listings'
        indexes = [
            models.Index(fields=['farmer', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['produce_type', 'status']),
            models.Index(fields=['district', 'status']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['-published_at']),
            models.Index(fields=['available_from', 'available_until']),
        ]
        ordering = ['-created_at']
        verbose_name = 'Listing'
        verbose_name_plural = 'Listings'
    
    def save(self, *args, **kwargs):
        # Generate unique listing number
        if not self.listing_number:
            import uuid
            self.listing_number = f"LST{uuid.uuid4().hex[:8].upper()}"
        
        # Generate slug
        if not self.slug:
            self.slug = slugify(f"{self.title}-{str(self.id)[:8]}")
        
        # Auto-publish if status is active
        if self.status == 'active' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.farmer.full_name}"
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def total_value(self):
        """Calculate total value of listing."""
        return float(self.quantity_available) * float(self.price_per_unit)


class ListingImage(TimestampedModel):
    """
    Images for listings (multiple images per listing).
    """
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='listings/%Y/%m/%d/')
    caption = models.CharField(max_length=255, blank=True)
    order = models.IntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    file_size = models.IntegerField(null=True, blank=True, help_text="Size in bytes")
    
    class Meta:
        db_table = 'listing_images'
        ordering = ['order', '-is_primary']
        indexes = [
            models.Index(fields=['listing', 'order']),
        ]
        verbose_name = 'Listing Image'
        verbose_name_plural = 'Listing Images'
    
    def __str__(self):
        return f"Image for {self.listing.title}"
    
    def save(self, *args, **kwargs):
        # Set as primary if it's the first image
        if not self.listing.images.exists():
            self.is_primary = True
        
        # Only one primary image per listing
        if self.is_primary:
            ListingImage.objects.filter(
                listing=self.listing,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        
        super().save(*args, **kwargs)


class ListingView(TimestampedModel):
    """
    Track listing views for analytics.
    """
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='views'
    )
    viewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'listing_views'
        indexes = [
            models.Index(fields=['listing', '-viewed_at']),
            models.Index(fields=['viewer', '-viewed_at']),
        ]
        verbose_name = 'Listing View'
        verbose_name_plural = 'Listing Views'
    
    def __str__(self):
        viewer_info = self.viewer.full_name if self.viewer else self.ip_address
        return f"{self.listing.title} viewed by {viewer_info}"
