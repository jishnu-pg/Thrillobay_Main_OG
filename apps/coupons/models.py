from django.db import models
from apps.common.models import TimeStampedModel


class Coupon(TimeStampedModel):
    code = models.CharField(max_length=20, unique=True, help_text="Unique coupon code")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Discount amount for the coupon")
    valid_from = models.DateField(help_text="Start date for coupon validity")
    valid_to = models.DateField(help_text="End date for coupon validity")

    def __str__(self):
        return f"{self.code} - ₹{self.discount_amount}"


class CouponUsage(TimeStampedModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, help_text="Used coupon")
    booking = models.ForeignKey("bookings.Booking", on_delete=models.CASCADE, help_text="Related booking")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, help_text="User who used the coupon")
