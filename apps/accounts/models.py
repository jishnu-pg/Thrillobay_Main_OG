from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone = models.CharField(max_length=15, unique=True, help_text="User's unique phone number")

    otp_token = models.CharField(max_length=10, null=True, blank=True, help_text="One Time Password token for verification")
    otp_created_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when the OTP was created")
    is_phone_verified = models.BooleanField(default=False, help_text="Designates whether the user's phone number is verified")
