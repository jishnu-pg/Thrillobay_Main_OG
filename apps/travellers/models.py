from django.db import models
from apps.common.models import TimeStampedModel


class Traveller(TimeStampedModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="travellers")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    dob = models.DateField(null=True, blank=True)

    passport_number = models.CharField(max_length=50, blank=True)
    passport_expiry = models.DateField(null=True, blank=True)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.username})"
