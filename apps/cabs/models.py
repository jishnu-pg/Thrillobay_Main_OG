from django.db import models
from apps.common.models import TimeStampedModel


class CabCategory(TimeStampedModel):
    """
    Normalized model for Cab Categories (e.g., Sedan, SUV, Hatchback).
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Cab Categories"

    def __str__(self):
        return self.name


class Cab(TimeStampedModel):
    """
    Core Cab model updated to match UI requirements.
    """
    FUEL_TYPE_CHOICES = [
        ("petrol", "Petrol"),
        ("diesel", "Diesel"),
        ("cng", "CNG"),
    ]

    # REFACTORED: category replaces the old 'cab_type' CharField
    category = models.ForeignKey(
        CabCategory, 
        on_delete=models.CASCADE, 
        related_name="cabs",
        null=True,
        blank=True
    )
    
    title = models.CharField(
        max_length=255, 
        help_text="e.g. Sedan | Dzire, Etios or Similar"
    )
    
    # Kept from original model
    capacity = models.PositiveIntegerField(help_text="Seating capacity")
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # New fields based on UI requirements
    luggage_capacity = models.PositiveIntegerField(default=2)
    fuel_type = models.CharField(max_length=10, choices=FUEL_TYPE_CHOICES)
    is_ac = models.BooleanField(default=True)
    
    # Pricing logic fields
    price_per_km = models.DecimalField(max_digits=10, decimal_places=2)
    included_kms = models.PositiveIntegerField(help_text="Distance included in base price")
    extra_km_fare = models.DecimalField(max_digits=10, decimal_places=2)
    driver_allowance = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    free_waiting_time_minutes = models.PositiveIntegerField(default=45)
    
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.category.name})"


class CabImage(TimeStampedModel):
    cab = models.ForeignKey(Cab, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="cabs/gallery/%Y/%m/")
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Image for {self.cab.title}"


class CabInclusion(TimeStampedModel):
    """
    Stores inclusions/exclusions and specific metrics (e.g. 'Parking Charges: Included').
    """
    cab = models.ForeignKey(Cab, on_delete=models.CASCADE, related_name="inclusions")
    label = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    is_included = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.label}: {self.value}"


class CabPolicy(TimeStampedModel):
    cab = models.ForeignKey(Cab, on_delete=models.CASCADE, related_name="policies")
    title = models.CharField(max_length=255)
    description = models.TextField()

    class Meta:
        verbose_name_plural = "Cab Policies"

    def __str__(self):
        return f"{self.title} - {self.cab.title}"


class CabPricingOption(TimeStampedModel):
    """
    Pricing options like 'Pay Now' vs 'Pay Later'.
    """
    OPTION_TYPE_CHOICES = [
        ("pay_now", "Pay Now"),
        ("pay_later", "Pay Later"),
    ]
    
    cab = models.ForeignKey(Cab, on_delete=models.CASCADE, related_name="pricing_options")
    option_type = models.CharField(max_length=20, choices=OPTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_option_type_display()} - {self.amount}"


class CabBooking(TimeStampedModel):
    """
    Booking record for Cab rentals.
    """
    TRIP_TYPE_CHOICES = [
        ("oneway", "One Way"),
        ("roundtrip", "Round Trip"),
    ]
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    ]

    cab = models.ForeignKey(Cab, on_delete=models.PROTECT, related_name="bookings")
    
    pickup_location = models.CharField(max_length=255)
    drop_location = models.CharField(max_length=255)
    pickup_datetime = models.DateTimeField()
    
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE_CHOICES)
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="pending"
    )

    def __str__(self):
        return f"Booking #{self.id} - {self.cab.title}"
