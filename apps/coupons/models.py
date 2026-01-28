from django.db import models
from apps.common.models import TimeStampedModel


class Coupon(TimeStampedModel):
    code = models.CharField(max_length=20, unique=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateField()
    valid_to = models.DateField()

    def __str__(self):
        return f"{self.code} - ₹{self.discount_amount}"


class CouponUsage(TimeStampedModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    booking = models.ForeignKey("bookings.Booking", on_delete=models.CASCADE)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
