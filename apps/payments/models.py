from django.db import models
from apps.common.models import TimeStampedModel


class Payment(TimeStampedModel):
    booking = models.ForeignKey("bookings.Booking", on_delete=models.CASCADE, help_text="Related booking")
    payment_mode = models.CharField(max_length=50, help_text="Mode of payment (e.g., Credit Card, UPI)")
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Payment amount")
    status = models.CharField(max_length=30, help_text="Payment status")
    transaction_id = models.CharField(max_length=100, blank=True, help_text="Transaction ID from the payment gateway")

    def __str__(self):
        return f"Payment #{self.id} - Booking #{self.booking.id} - ₹{self.amount} ({self.status})"
