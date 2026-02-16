"""
Pricing models - Market prices, trends, and alerts.
"""

from django.db import models
from apps.core.models import TimestampedModel
from apps.users.models import User
from apps.listings.models import ProduceType


class MarketPrice(TimestampedModel):
    """
    Current market prices for produce types.
    """
    SOURCE_CHOICES = [
        ('manual', 'Manual Entry'),
        ('listing', 'From Listings'),
        ('external', 'External Source'),
        ('survey', 'Market Survey'),
    ]
    
    produce_type = models.ForeignKey(
        ProduceType,
        on_delete=models.CASCADE,
        related_name='market_prices'
    )
    district = models.CharField(max_length=100)
    
    # Price data
    price_min = models.DecimalField(max_digits=10, decimal_places=2)
    price_max = models.DecimalField(max_digits=10, decimal_places=2)
    price_avg = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    currency = models.CharField(max_length=3, default='ZWL')
    
    # Metadata
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    sample_size = models.IntegerField(
        default=1,
        help_text="Number of listings/data points"
    )
    recorded_date = models.DateField()
    
    # Quality indicators
    confidence_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.0,
        help_text="0-1, confidence in this price data"
    )
    
    class Meta:
        db_table = 'market_prices'
        unique_together = ['produce_type', 'district', 'recorded_date']
        indexes = [
            models.Index(fields=['produce_type', 'district', '-recorded_date']),
            models.Index(fields=['recorded_date']),
        ]
        ordering = ['-recorded_date']
        verbose_name = 'Market Price'
        verbose_name_plural = 'Market Prices'
    
    def __str__(self):
        return f"{self.produce_type.name} - {self.district} - {self.recorded_date}"


class PriceTrend(TimestampedModel):
    """
    Price trend analysis over time.
    """
    TREND_CHOICES = [
        ('increasing', 'Increasing'),
        ('decreasing', 'Decreasing'),
        ('stable', 'Stable'),
        ('volatile', 'Volatile'),
    ]
    
    produce_type = models.ForeignKey(
        ProduceType,
        on_delete=models.CASCADE,
        related_name='price_trends'
    )
    district = models.CharField(max_length=100, blank=True)
    
    # Time period
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Trend data
    trend_direction = models.CharField(max_length=20, choices=TREND_CHOICES)
    price_change_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Percentage change (positive or negative)"
    )
    average_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Analysis
    volatility_index = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="0-100, higher = more volatile"
    )
    forecast_next_period = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'price_trends'
        unique_together = ['produce_type', 'district', 'period_start', 'period_end']
        indexes = [
            models.Index(fields=['produce_type', '-period_end']),
            models.Index(fields=['district', '-period_end']),
        ]
        ordering = ['-period_end']
        verbose_name = 'Price Trend'
        verbose_name_plural = 'Price Trends'
    
    def __str__(self):
        location = f" - {self.district}" if self.district else ""
        return f"{self.produce_type.name}{location} ({self.period_start} to {self.period_end})"


class PriceAlert(TimestampedModel):
    """
    Price alerts set by users.
    """
    ALERT_TYPE_CHOICES = [
        ('above', 'Price Above'),
        ('below', 'Price Below'),
        ('change', 'Significant Change'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='price_alerts'
    )
    produce_type = models.ForeignKey(
        ProduceType,
        on_delete=models.CASCADE,
        related_name='price_alerts'
    )
    district = models.CharField(max_length=100, blank=True)
    
    # Alert settings
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    target_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    change_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="For 'change' alerts"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    trigger_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'price_alerts'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['produce_type', 'is_active']),
        ]
        ordering = ['-created_at']
        verbose_name = 'Price Alert'
        verbose_name_plural = 'Price Alerts'
    
    def __str__(self):
        return f"{self.user.full_name} - {self.produce_type.name} - {self.alert_type}"
