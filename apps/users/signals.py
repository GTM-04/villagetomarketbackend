"""
User signals - Automatic profile creation and notifications.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserSettings


@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """
    Automatically create UserSettings when a User is created.
    """
    if created:
        UserSettings.objects.create(user=instance)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create appropriate profile (Farmer or Buyer) when User is created.
    """
    if created:
        if instance.user_type == 'farmer':
            from apps.farmers.models import FarmerProfile
            FarmerProfile.objects.get_or_create(user=instance)
        elif instance.user_type == 'buyer':
            from apps.buyers.models import BuyerProfile
            BuyerProfile.objects.get_or_create(user=instance)
