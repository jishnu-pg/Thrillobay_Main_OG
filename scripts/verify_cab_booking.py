import os
import sys
import django
from decimal import Decimal
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.accounts.models import User
from apps.cabs.models import Cab, CabCategory, CabPricingOption, CabInclusion
from apps.bookings.models import Booking
from rest_framework.test import APIRequestFactory, force_authenticate
from api.bookings.views import BookingReviewAPIView

def verify_cab_booking():
    # 1. Setup Data
    try:
        user = User.objects.get(username="cab_tester")
    except User.DoesNotExist:
        # Create with random phone to avoid collision if possible, or just use a fixed one but handle collision
        import random
        phone = f"999{random.randint(1000000, 9999999)}"
        try:
            user = User.objects.create(username="cab_tester", email="cab@test.com", phone=phone)
        except Exception:
            # Fallback to any user
            user = User.objects.first()
    
    category = CabCategory.objects.filter(name="Sedan").first()
    if not category:
        category = CabCategory.objects.create(name="Sedan")
    cab, _ = Cab.objects.get_or_create(
        title="Dzire or Similar",
        defaults={
            "category": category,
            "base_price": Decimal("15000.00"),
            "price_per_km": Decimal("12.00"),
            "included_kms": 100,
            "extra_km_fare": Decimal("15.00"),
            "capacity": 4,
            "fuel_type": "petrol",
            "is_active": True
        }
    )
    
    # Setup Pricing Options
    CabPricingOption.objects.get_or_create(
        cab=cab,
        option_type="pay_now",
        defaults={"amount": Decimal("1000.00"), "description": "Pay small amount now"}
    )
    
    # Setup Inclusions
    CabInclusion.objects.get_or_create(cab=cab, label="Parking Charges", value="Included")
    CabInclusion.objects.get_or_create(cab=cab, label="Toll Charges", value="Included")

    print(f"Cab Setup: {cab.title} (Base: {cab.base_price})")

    # 2. Test Review API (POST)
    factory = APIRequestFactory()
    view = BookingReviewAPIView.as_view()
    
    payload = {
        "booking_type": "cab",
        "check_in": "2024-07-09", # Not used for cab but required by serializer validation
        "check_out": "2024-07-09",
        "payment_option": "part", # Select Part Payment
        "items": [
            {
                "cab_id": cab.id,
                "quantity": 1,
                "pickup_location": "Kempegowda International Airport",
                "drop_location": "Arekere, Bengaluru",
                "pickup_datetime": "2024-07-09T10:00:00",
                "trip_type": "Airport Transfer",
                "adults": 2,
                "children": 0
            }
        ]
    }
    
    request = factory.post("/api/bookings/review/", data=payload, format="json")
    force_authenticate(request, user=user)
    
    print("\n--- Testing Review API (POST) ---")
    response = view(request)
    
    if response.status_code == 200:
        data = response.data
        print(f"Booking ID: {data.get('booking_id')}")
        
        # 3. Test Review API (GET) to verify details and pricing
        print("\n--- Testing Review API (GET) ---")
        request_get = factory.get(f"/api/bookings/review/?booking_id={data.get('booking_id')}")
        force_authenticate(request_get, user=user)
        response_get = view(request_get)
        
        if response_get.status_code == 200:
            data_get = response_get.data
            print(f"Final Total: {data_get.get('final_total')}")
            print(f"Insurance Fee: {data_get.get('insurance_fee')}")
            
            # Check Items for Payment Options and Journey Details
            items = data_get.get("breakdown", [])
            if items:
                item = items[0]
                print(f"Item Total: {item.get('total')}")
                print(f"Journey: {item.get('pickup_location')} -> {item.get('drop_location')}")
                print(f"Pickup Time: {item.get('pickup_datetime')}")
                print(f"Trip Type: {item.get('trip_type')}")
                
                print("Payment Options:")
                for opt in item.get("payment_options", []):
                    print(f" - {opt['label']}: {opt['amount']} ({opt['value']})")
                
                print("Inclusions:")
                for inc in item.get("inclusions", []):
                    print(f" - {inc['name']}: {inc['value']} (Included: {inc['is_included']})")
        else:
            print(f"GET Failed: {response_get.status_code} {response_get.data}")
        
        # Verify Database
        booking_id = data.get("booking_id")
        booking = Booking.objects.get(id=booking_id)
        print(f"\nDB Verification (Booking #{booking.id}):")
        print(f"Status: {booking.status}")
        print(f"Payment Option: {booking.payment_option}")
        print(f"Part Payment Amount: {booking.part_payment_amount}")
        print(f"Amount Paid: {booking.amount_paid}")
        print(f"Total Amount: {booking.total_amount}")
        
        # Verify Booking Item
        b_item = booking.items.first()
        print(f"Pickup: {b_item.pickup_location}")
        print(f"Drop: {b_item.drop_location}")
        print(f"Trip Type: {b_item.trip_type}")

    else:
        print(f"Error: {response.status_code}")
        print(response.data)

if __name__ == "__main__":
    verify_cab_booking()
