from django.db import models
from apps.common.models import TimeStampedModel


class Booking(TimeStampedModel):
    BOOKING_TYPE = [
        ("stay", "Stay"),
        ("package", "Package"),
        ("activity", "Activity"),
        ("cab", "Cab"),
        ("houseboat", "Houseboat"),
    ]

    STATUS = [
        ("draft", "Draft"),
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    ]

    REFUND_STATUS = [
        ("none", "No Refund"),
        ("processing", "Processing"),
        ("processed", "Processed"),
        ("no_refund_due", "No Refund Due"),
    ]

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, help_text="User who made the booking")
    coupon = models.ForeignKey(
        "coupons.Coupon", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="bookings", 
        help_text="Applied coupon"
    )
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPE, help_text="Type of booking")
    status = models.CharField(max_length=20, choices=STATUS, help_text="Status of the booking")
    refund_status = models.CharField(max_length=20, choices=REFUND_STATUS, default="none", help_text="Status of the refund")
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total amount for the booking")
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Amount paid so far")
    
    cancelled_at = models.DateTimeField(null=True, blank=True, help_text="Date and time when the booking was cancelled")
    
    # Financial Breakdown
    pricing_breakdown = models.JSONField(default=dict, blank=True, help_text="JSON snapshot of pricing details (base, tax, discount, fees)")

    # Contact Details
    title = models.CharField(max_length=10, blank=True, help_text="Title of the contact person")
    full_name = models.CharField(max_length=255, blank=True, help_text="Full name of the contact person")
    email = models.EmailField(blank=True, help_text="Email address of the contact person")
    phone = models.CharField(max_length=20, blank=True, help_text="Phone number of the contact person")
    country_code = models.CharField(max_length=10, blank=True, help_text="Country code for the phone number")
    
    # Additional Info
    special_requests = models.TextField(blank=True, help_text="Any special requests from the user")
    
    # GST Details
    is_gst_required = models.BooleanField(default=False, help_text="Designates whether GST is required")
    gst_number = models.CharField(max_length=50, blank=True, help_text="GST number if applicable")
    company_name = models.CharField(max_length=255, blank=True, help_text="Company name for GST invoice")
    company_address = models.TextField(blank=True, help_text="Company address for GST invoice")

    def __str__(self):
        return f"Booking #{self.id} - {self.user.username} ({self.booking_type}) - {self.status}"


class BookingItem(TimeStampedModel):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="items", help_text="Related booking")
    property = models.ForeignKey("properties.Property", null=True, blank=True, on_delete=models.SET_NULL, help_text="Related property")
    room_type = models.ForeignKey("properties.RoomType", null=True, blank=True, on_delete=models.SET_NULL, help_text="Related room type")
    package = models.ForeignKey("packages.HolidayPackage", null=True, blank=True, on_delete=models.SET_NULL, help_text="Related holiday package")
    activity = models.ForeignKey("activities.Activity", null=True, blank=True, on_delete=models.SET_NULL, help_text="Related activity")
    cab = models.ForeignKey("cabs.Cab", null=True, blank=True, on_delete=models.SET_NULL, help_text="Related cab")
    
    # ADDED: Link to HouseBoat for houseboat bookings
    houseboat = models.ForeignKey(
        "houseboats.HouseBoat",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking_items",
        help_text="Related houseboat"
    )

    check_in = models.DateField(null=True, blank=True, help_text="Check-in date")
    check_out = models.DateField(null=True, blank=True, help_text="Check-out date")
    adults = models.PositiveIntegerField(default=1, help_text="Number of adults")
    children = models.PositiveIntegerField(default=0, help_text="Number of children")

    def __str__(self):
        item_name = ""
        if self.property:
            item_name = self.property.name
        elif self.package:
            item_name = self.package.title
        elif self.activity:
            item_name = self.activity.title
        elif self.cab:
            item_name = self.cab.title
        return f"Booking Item #{self.id} - {item_name}"


class BookingTraveller(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, help_text="Related booking")
    traveller = models.ForeignKey("travellers.Traveller", on_delete=models.CASCADE, help_text="Related traveller")
    is_primary = models.BooleanField(default=False, help_text="Designates whether this is the primary traveller")

    def __str__(self):
        primary_text = " (Primary)" if self.is_primary else ""
        return f"{self.traveller.first_name} {self.traveller.last_name} - Booking #{self.booking.id}{primary_text}"
