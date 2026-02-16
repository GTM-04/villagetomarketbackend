"""
Pricing Celery tasks.
"""

from celery import shared_task
from django.utils import timezone
from django.db.models import Avg, Min, Max, Count
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_market_prices():
    """
    Update market prices from active listings.
    """
    from .models import MarketPrice
    from apps.listings.models import Listing, ProduceType
    
    today = date.today()
    updated_count = 0
    
    # Get all produce types with active listings
    produce_types = ProduceType.objects.filter(
        listings__status='active'
    ).distinct()
    
    for produce_type in produce_types:
        # Get districts with listings for this produce
        districts = Listing.objects.filter(
            produce_type=produce_type,
            status='active'
        ).values_list('district', flat=True).distinct()
        
        for district in districts:
            # Calculate price statistics
            stats = Listing.objects.filter(
                produce_type=produce_type,
                district=district,
                status='active'
            ).aggregate(
                price_min=Min('price_per_unit'),
                price_max=Max('price_per_unit'),
                price_avg=Avg('price_per_unit'),
                count=Count('id')
            )
            
            if stats['count'] > 0:
                # Update or create market price
                MarketPrice.objects.update_or_create(
                    produce_type=produce_type,
                    district=district,
                    recorded_date=today,
                    defaults={
                        'price_min': stats['price_min'],
                        'price_max': stats['price_max'],
                        'price_avg': stats['price_avg'],
                        'unit': 'kg',  # TODO: Handle different units
                        'source': 'listing',
                        'sample_size': stats['count'],
                        'confidence_score': min(1.0, stats['count'] / 10.0)
                    }
                )
                updated_count += 1
    
    logger.info(f"Updated {updated_count} market prices")
    return f"Updated {updated_count} market prices"


@shared_task
def calculate_price_trends():
    """
    Calculate price trends for the past week/month.
    """
    from .models import MarketPrice, PriceTrend
    from apps.listings.models import ProduceType
    
    today = date.today()
    week_ago = today - timedelta(days=7)
    trends_created = 0
    
    # Get all produce types with price data
    produce_types = ProduceType.objects.filter(
        market_prices__recorded_date__gte=week_ago
    ).distinct()
    
    for produce_type in produce_types:
        # Get districts
        districts = MarketPrice.objects.filter(
            produce_type=produce_type,
            recorded_date__gte=week_ago
        ).values_list('district', flat=True).distinct()
        
        for district in districts:
            # Get price data for the period
            prices = MarketPrice.objects.filter(
                produce_type=produce_type,
                district=district,
                recorded_date__gte=week_ago
            ).order_by('recorded_date')
            
            if prices.count() >= 2:
                first_price = prices.first().price_avg
                last_price = prices.last().price_avg
                avg_price = prices.aggregate(Avg('price_avg'))['price_avg__avg']
                
                # Calculate change
                price_change = ((last_price - first_price) / first_price) * 100
                
                # Determine trend
                if abs(price_change) < 5:
                    trend_direction = 'stable'
                elif price_change > 0:
                    trend_direction = 'increasing'
                else:
                    trend_direction = 'decreasing'
                
                # Calculate volatility (simplified)
                price_values = list(prices.values_list('price_avg', flat=True))
                volatility = (max(price_values) - min(price_values)) / avg_price * 100
                
                # Create trend
                PriceTrend.objects.update_or_create(
                    produce_type=produce_type,
                    district=district,
                    period_start=week_ago,
                    period_end=today,
                    defaults={
                        'trend_direction': trend_direction,
                        'price_change_percent': price_change,
                        'average_price': avg_price,
                        'volatility_index': min(volatility, 100),
                    }
                )
                trends_created += 1
    
    logger.info(f"Calculated {trends_created} price trends")
    return f"Calculated {trends_created} trends"


@shared_task
def send_price_alerts():
    """
    Check price alerts and send notifications.
    """
    from .models import PriceAlert, MarketPrice
    from apps.notifications.services import NotificationService
    
    alerts_triggered = 0
    
    # Get active alerts
    active_alerts = PriceAlert.objects.filter(is_active=True)
    
    for alert in active_alerts:
        # Get latest market price
        try:
            market_price = MarketPrice.objects.filter(
                produce_type=alert.produce_type,
                district=alert.district if alert.district else None
            ).latest('recorded_date')
            
            should_trigger = False
            message = ""
            
            if alert.alert_type == 'above' and market_price.price_avg >= alert.target_price:
                should_trigger = True
                message = f"{alert.produce_type.name} price is now {market_price.price_avg} (above your target of {alert.target_price})"
            
            elif alert.alert_type == 'below' and market_price.price_avg <= alert.target_price:
                should_trigger = True
                message = f"{alert.produce_type.name} price is now {market_price.price_avg} (below your target of {alert.target_price})"
            
            if should_trigger:
                # Send notification
                NotificationService.send_notification(
                    user=alert.user,
                    notification_type='price_alert',
                    title='Price Alert Triggered',
                    message=message
                )
                
                # Update alert
                alert.last_triggered_at = timezone.now()
                alert.trigger_count += 1
                alert.save(update_fields=['last_triggered_at', 'trigger_count'])
                
                alerts_triggered += 1
        
        except MarketPrice.DoesNotExist:
            continue
    
    logger.info(f"Triggered {alerts_triggered} price alerts")
    return f"Triggered {alerts_triggered} alerts"
