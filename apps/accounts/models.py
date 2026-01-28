from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone = models.CharField(max_length=15, unique=True)

    otp_token = models.CharField(max_length=10, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    is_phone_verified = models.BooleanField(default=False)
