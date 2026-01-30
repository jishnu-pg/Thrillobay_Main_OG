from django.core.management.base import BaseCommand
from apps.properties.models import RoomType, RoomOption

class Command(BaseCommand):
    help = 'Migrate RoomType pricing to RoomOption'

    def handle(self, *args, **kwargs):
        room_types = RoomType.objects.all()
        count = 0
        for rt in room_types:
            # Check if options already exist to avoid duplication
            if rt.options.exists():
                continue
                
            # Create a default option based on current RoomType settings
            option_name = "Standard Rate"
            if rt.has_breakfast:
                option_name = "Breakfast Included"
            
            RoomOption.objects.create(
                room_type=rt,
                name=option_name,
                description=rt.description,
                base_price=rt.base_price,
                has_breakfast=rt.has_breakfast,
                has_lunch=False,
                has_dinner=False,
                is_refundable=True, # Default assumption or check policy text?
                cancellation_policy=rt.refund_policy
            )
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} RoomOptions'))
