import os
import sys
import django
import json
from decimal import Decimal
from datetime import date, timedelta
import random

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from apps.properties.models import Property, RoomType, RoomOption
from apps.packages.models import HolidayPackage
from apps.activities.models import Activity
from apps.cabs.models import Cab, CabCategory
from apps.houseboats.models import HouseBoat
from apps.bookings.models import Booking, BookingItem
from api.bookings.services import BookingPricingService
from api.bookings.serializers import BookingDetailSerializer

User = get_user_model()

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError ("Type %s not serializable" % type(obj))

def print_section(title):
    print(f"\n\n{'='*50}\n{title}\n{'='*50}")

def make_json_serializable(data):
    if isinstance(data, dict):
        return {k: make_json_serializable(v) for k, v in data.items()}
    if isinstance(data, list):
        return [make_json_serializable(v) for v in data]
    if isinstance(data, Decimal):
        return str(data)
    if isinstance(data, (date, datetime)):
        return data.isoformat()
    return data

def run_samples():
    # Setup User
    try:
        user = User.objects.get(email="frontend_dev@example.com")
    except User.DoesNotExist:
        try:
            user = User.objects.create(
                email="frontend_dev@example.com",
                first_name="Frontend",
                last_name="Dev",
                phone="9876543219" 
            )
        except Exception:
             user = User.objects.first()
             if not user:
                 user = User.objects.create(
                    email=f"frontend_dev_{random.randint(1000,9999)}@example.com",
                    first_name="Frontend",
                    last_name="Dev",
                    phone=str(random.randint(1000000000, 9999999999))
                )

    # ---------------------------------------------------------
    # 1. HOTEL BOOKING (Room Options)
    # ---------------------------------------------------------
    print_section("HOTEL BOOKING (Stay)")
    
    # Setup Data
    hotel = Property.objects.create(
        name="Grand Hyatt Kochi",
        property_type="hotel",
        city="Kochi",
        state="Kerala",
        check_in_time="14:00:00",
        check_out_time="11:00:00",
        gst_percent=12.00
    )
    room_type = RoomType.objects.create(
        property=hotel,
        name="Grand King Room",
        max_guests=3,
        base_price=5000,
        total_units=10,
        refund_policy="No Refund",
        booking_policy="Instant"
    )
    room_option = RoomOption.objects.create(
        room_type=room_type,
        name="Breakfast Included",
        base_price=5500, # Absolute price override
        has_breakfast=True
    )
    
    # Simulate Review Request Data
    check_in = date.today() + timedelta(days=10)
    check_out = date.today() + timedelta(days=12)
    
    items_data = [{
        "room_type_id": room_type.id,
        "room_option_id": room_option.id,
        "quantity": 1,
        "adults": 2,
        "children": 0
    }]
    
    # Calculate Pricing (Review Step)
    pricing = BookingPricingService.calculate_pricing(
        booking_type="stay",
        items_data=items_data,
        check_in=check_in,
        check_out=check_out
    )
    
    print("### API: GET /api/bookings/review/?booking_id={id}")
    print("### Response:")
    print(json.dumps(pricing, default=json_serial, indent=4))
    
    # Create Booking for Detail View
    booking = Booking.objects.create(
        user=user,
        booking_type="stay",
        status="confirmed",
        total_amount=pricing["final_total"],
        pricing_breakdown=make_json_serializable(pricing),
        title="Mr.",
        full_name="John Doe",
        email="john@example.com",
        phone="9876543210"
    )
    BookingItem.objects.create(
        booking=booking,
        property=hotel,
        room_type=room_type,
        room_option=room_option,
        check_in=check_in,
        check_out=check_out,
        adults=2,
        children=0
    )
    
    detail_serializer = BookingDetailSerializer(booking)
    print("\n### API: GET /api/bookings/{id}/")
    print("### Response:")
    print(json.dumps(detail_serializer.data, default=json_serial, indent=4))

    # ---------------------------------------------------------
    # 2. HOMESTAY (Entire Place)
    # ---------------------------------------------------------
    print_section("HOMESTAY BOOKING (Entire Place)")
    
    homestay = Property.objects.create(
        name="Munnar Tea Villa",
        property_type="homestay",
        city="Munnar",
        state="Kerala",
        check_in_time="12:00:00",
        check_out_time="11:00:00",
        allow_entire_place_booking=True,
        entire_place_price=15000,
        entire_place_max_guests=10,
        gst_percent=12.00
    )
    entire_room = RoomType.objects.create(
        property=homestay,
        name="Entire Villa",
        max_guests=10,
        base_price=15000,
        total_units=1,
        is_entire_place=True,
        refund_policy="Partial",
        booking_policy="Request"
    )
    
    items_data = [{
        "room_type_id": entire_room.id,
        "quantity": 1,
        "adults": 6,
        "children": 2
    }]
    
    pricing = BookingPricingService.calculate_pricing(
        booking_type="stay",
        items_data=items_data,
        check_in=check_in,
        check_out=check_out
    )
    
    print("### API: GET /api/bookings/review/?booking_id={id}")
    print("### Response:")
    print(json.dumps(pricing, default=json_serial, indent=4))

    # ---------------------------------------------------------
    # 3. HOLIDAY PACKAGE
    # ---------------------------------------------------------
    print_section("HOLIDAY PACKAGE BOOKING")
    
    # Create Holiday Package
    try:
        package = HolidayPackage.objects.get(slug="kerala-backwaters-3n-4d")
    except HolidayPackage.DoesNotExist:
        package = HolidayPackage.objects.create(
            title="Kerala Backwaters Special",
            slug="kerala-backwaters-3n-4d",
            primary_location="Alleppey",
            short_description="Experience the serene backwaters",
            terms_and_conditions="No refund on cancellation.",
            duration_nights=3,
            duration_days=4,
            base_price=15000
        )
    
    items_data = [{
        "package_id": package.id,
        "quantity": 1, 
        "adults": 2,
        "children": 1
    }]
    
    pricing = BookingPricingService.calculate_pricing(
        booking_type="package",
        items_data=items_data,
        check_in=check_in,
        check_out=check_out
    )
    
    print("### API: GET /api/bookings/review/?booking_id={id}")
    print("### Response:")
    print(json.dumps(pricing, default=json_serial, indent=4))

    # ---------------------------------------------------------
    # 4. ACTIVITY
    # ---------------------------------------------------------
    print_section("ACTIVITY BOOKING")
    
    # Create Activity
    try:
        activity = Activity.objects.get(slug="scuba-diving-kochi")
    except Activity.DoesNotExist:
        activity = Activity.objects.create(
            title="Scuba Diving",
            slug="scuba-diving-kochi",
            location="Kochi",
            short_description="Fun diving",
            description="Explore underwater life.",
            duration_days=1,
            base_price=3000,
            difficulty="moderate"
        )
    
    items_data = [{
        "activity_id": activity.id,
        "quantity": 1,
        "adults": 2,
        "children": 0
    }]
    
    pricing = BookingPricingService.calculate_pricing(
        booking_type="activity",
        items_data=items_data,
        check_in=check_in, 
        check_out=check_in
    )
    
    print("### API: GET /api/bookings/review/?booking_id={id}")
    print("### Response:")
    print(json.dumps(pricing, default=json_serial, indent=4))

    # ---------------------------------------------------------
    # 5. CAB
    # ---------------------------------------------------------
    print_section("CAB BOOKING")
    
    # Create Cab
    try:
        cab = Cab.objects.get(title="Sedan - Dzire or Similar")
    except Cab.DoesNotExist:
        cab = Cab.objects.create(
            title="Sedan - Dzire or Similar",
            location="Kochi",
            capacity=4,
            base_price=2500,
            fuel_type="diesel",
            price_per_km=15,
            included_kms=80,
            extra_km_fare=18,
            is_active=True
        )
    
    items_data = [{
        "cab_id": cab.id,
        "quantity": 1,
        "adults": 4,
        "children": 0
    }]
    
    pricing = BookingPricingService.calculate_pricing(
        booking_type="cab",
        items_data=items_data,
        check_in=check_in,
        check_out=check_out # 2 days
    )
    
    print("### API: GET /api/bookings/review/?booking_id={id}")
    print("### Response:")
    print(json.dumps(pricing, default=json_serial, indent=4))

    # ---------------------------------------------------------
    # 6. HOUSEBOAT
    # ---------------------------------------------------------
    print_section("HOUSEBOAT BOOKING")
    
    # Create Houseboat
    try:
        houseboat = HouseBoat.objects.get(slug="luxury-houseboat-alleppey")
    except HouseBoat.DoesNotExist:
        houseboat = HouseBoat.objects.create(
            name="Luxury Houseboat",
            slug="luxury-houseboat-alleppey",
            location="Alleppey",
            description="Floating paradise",
            base_price_per_night=12000
        )
    
    items_data = [{
        "houseboat_id": houseboat.id,
        "quantity": 1,
        "adults": 4,
        "children": 0
    }]
    
    pricing = BookingPricingService.calculate_pricing(
        booking_type="houseboat",
        items_data=items_data,
        check_in=check_in,
        check_out=check_out
    )
    
    print("### API: GET /api/bookings/review/?booking_id={id}")
    print("### Response:")
    print(json.dumps(pricing, default=json_serial, indent=4))

    # Cleanup
    # (Optional in dev env, but good practice)
    Booking.objects.all().delete()
    hotel.delete()
    homestay.delete()
    package.delete()
    activity.delete()
    cab.delete()
    houseboat.delete()

if __name__ == "__main__":
    from datetime import datetime
    run_samples()
