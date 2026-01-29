from django.db import models
from apps.common.models import TimeStampedModel


class Traveller(TimeStampedModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="travellers", help_text="Related user")
    first_name = models.CharField(max_length=100, help_text="First name")
    last_name = models.CharField(max_length=100, help_text="Last name")
    gender = models.CharField(max_length=10, help_text="Gender")
    dob = models.DateField(null=True, blank=True, help_text="Date of birth")
    
    # Address Details
    country = models.CharField(max_length=100, blank=True, help_text="Country")
    state = models.CharField(max_length=100, blank=True, help_text="State")
    city = models.CharField(max_length=100, blank=True, help_text="City")
    pincode = models.CharField(max_length=20, blank=True, help_text="Pin Code")

    # Passport Details
    passport_number = models.CharField(max_length=50, blank=True, help_text="Passport number")
    passport_expiry = models.DateField(null=True, blank=True, help_text="Passport expiry date")
    passport_issuing_country = models.CharField(max_length=100, blank=True, help_text="Passport issuing country")
    passport_copy = models.ImageField(upload_to="travellers/passports/", blank=True, null=True, help_text="Passport copy image")

    # Contact Details
    email = models.EmailField(blank=True, help_text="Email address")
    phone = models.CharField(max_length=15, blank=True, help_text="Phone number")

    # Frequent Flyer Details
    frequent_flyer_airline = models.CharField(max_length=100, blank=True, help_text="Frequent flyer airline")
    frequent_flyer_number = models.CharField(max_length=50, blank=True, help_text="Frequent flyer number")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.username})"
