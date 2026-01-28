from django.db import models
from apps.common.models import TimeStampedModel


class Booking(TimeStampedModel):
    BOOKING_TYPE = [
        ("stay", "Stay"),
        ("package", "Package"),
        ("activity", "Activity"),
        ("cab", "Cab"),
    ]

    STATUS = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPE)
    status = models.CharField(max_length=20, choices=STATUS)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Booking #{self.id} - {self.user.username} ({self.booking_type}) - {self.status}"


class BookingItem(TimeStampedModel):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="items")

    property = models.ForeignKey("properties.Property", null=True, blank=True, on_delete=models.SET_NULL)
    room_type = models.ForeignKey("properties.RoomType", null=True, blank=True, on_delete=models.SET_NULL)

    package = models.ForeignKey("packages.HolidayPackage", null=True, blank=True, on_delete=models.SET_NULL)
    activity = models.ForeignKey("activities.Activity", null=True, blank=True, on_delete=models.SET_NULL)
    cab = models.ForeignKey("cabs.Cab", null=True, blank=True, on_delete=models.SET_NULL)
    
    # ADDED: Link to HouseBoat for houseboat bookings
    houseboat = models.ForeignKey(
        "houseboats.HouseBoat",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking_items"
    )

    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)

    def __str__(self):
        item_name = ""
        if self.property:
            item_name = self.property.name
        elif self.package:
            item_name = self.package.title
        elif self.activity:
            item_name = self.activity.title
        elif self.cab:
            item_name = self.cab.cab_type
        return f"Booking Item #{self.id} - {item_name}"


class BookingTraveller(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    traveller = models.ForeignKey("travellers.Traveller", on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        primary_text = " (Primary)" if self.is_primary else ""
        return f"{self.traveller.first_name} {self.traveller.last_name} - Booking #{self.booking.id}{primary_text}"
