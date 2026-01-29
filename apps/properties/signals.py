from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Property, RoomType

@receiver(post_save, sender=Property)
def sync_entire_place_room_type(sender, instance, created, **kwargs):
    """
    Automatically creates, updates, or deletes the 'Entire Place' RoomType
    based on the Property's configuration.
    """
    if instance.allow_entire_place_booking:
        # If price or guests are missing, we cannot create a valid RoomType
        if instance.entire_place_price is None or instance.entire_place_max_guests is None:
            return

        # Prepare defaults
        defaults = {
            "name": f"Entire {instance.name}",
            "base_price": instance.entire_place_price,
            "max_guests": instance.entire_place_max_guests,
            "total_units": 1,
            "is_entire_place": True,
            # Fill required fields with defaults or property data
            "bedroom_count": None, 
            "has_breakfast": False,
            "refund_policy": instance.rules or "Standard Property Policy",
            "booking_policy": instance.rules or "Standard Property Policy"
        }

        # Create or Update
        RoomType.objects.update_or_create(
            property=instance,
            is_entire_place=True,
            defaults=defaults
        )
    else:
        # If disabled, remove the Entire Place option
        RoomType.objects.filter(property=instance, is_entire_place=True).delete()
