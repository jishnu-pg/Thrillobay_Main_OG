from django.db import models
from apps.common.models import TimeStampedModel


class Payment(TimeStampedModel):
    booking = models.ForeignKey("bookings.Booking", on_delete=models.CASCADE)
    payment_mode = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=30)
    transaction_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Payment #{self.id} - Booking #{self.booking.id} - ₹{self.amount} ({self.status})"
