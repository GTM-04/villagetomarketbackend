"""
Listings Celery tasks.
"""

from celery import shared_task
from django.utils import timezone
from datetime import date
import logging

logger = logging.getLogger(__name__)


@shared_task
def expire_old_listings():
    """
    Mark listings as expired if available_until date has passed.
    """
    from .models import Listing
    
    expired_count = Listing.objects.filter(
        status='active',
        available_until__lt=date.today()
    ).update(status='expired')
    
    logger.info(f"Expired {expired_count} listings")
    return f"Expired {expired_count} listings"


@shared_task
def update_listing_stats():
    """
    Update farmer listing statistics.
    """
    from apps.farmers.models import FarmerProfile
    
    updated = 0
    for profile in FarmerProfile.objects.all():
        profile.update_stats()
        updated += 1
    
    logger.info(f"Updated stats for {updated} farmer profiles")
    return f"Updated {updated} profiles"


@shared_task
def notify_followers_new_listing(listing_id):
    """
    Notify followers when farmer posts new listing.
    """
    from .models import Listing
    from apps.buyers.models import FollowedFarmer
    from apps.notifications.services import NotificationService
    
    try:
        listing = Listing.objects.get(id=listing_id)
        
        # Get followers who want notifications
        followers = FollowedFarmer.objects.filter(
            farmer=listing.farmer,
            notify_new_listings=True
        )
        
        for follow in followers:
            NotificationService.send_notification(
                user=follow.buyer,
                notification_type='new_listing',
                title=f"New listing from {listing.farmer.full_name}",
                message=f"{listing.title} - {listing.price_per_unit} {listing.currency}/{listing.unit}",
                action_url=f"/listings/{listing.id}"
            )
        
        logger.info(f"Notified {followers.count()} followers about listing {listing_id}")
        return f"Notified {followers.count()} followers"
        
    except Listing.DoesNotExist:
        logger.error(f"Listing {listing_id} not found")
        return "Listing not found"
