from django.db import models
from apps.common.models import TimeStampedModel


class CabCategory(TimeStampedModel):
    """
    Normalized model for Cab Categories (e.g., Sedan, SUV, Hatchback).
    """
    name = models.CharField(max_length=100, help_text="Name of the cab category")
    description = models.TextField(blank=True, null=True, help_text="Description of the cab category")
    is_active = models.BooleanField(default=True, help_text="Designates whether the category is active")

    class Meta:
        verbose_name_plural = "Cab Categories"

    def __str__(self):
        return self.name


class CabTransferType(TimeStampedModel):
    """
    Types of transfers/services (e.g., Airport Transfer, Outstation, Hourly).
    """
    name = models.CharField(max_length=100, unique=True, help_text="Name of the transfer type")

    class Meta:
        verbose_name = "Cab Transfer Type"
        verbose_name_plural = "Cab Transfer Types"

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
        blank=True,
        help_text="Category of the cab"
    )
    
    transfer_types = models.ManyToManyField(
        CabTransferType, 
        blank=True, 
        related_name="cabs", 
        help_text="Supported transfer types (e.g., Airport, Outstation)"
    )

    title = models.CharField(
        max_length=255, 
        help_text="e.g. Sedan | Dzire, Etios or Similar"
    )
    
    # Kept from original model
    location = models.CharField(max_length=255, null=True, blank=True, help_text="Location where the cab is based (e.g. Sulthan Bathery)")
    capacity = models.PositiveIntegerField(help_text="Seating capacity")
    base_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Base price for the cab")
    discount = models.ForeignKey(
        "properties.Discount", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="cabs", 
        help_text="Applicable discount for the cab"
    )
    cancellation_policy = models.TextField(
        blank=True, 
        null=True, 
        help_text="Cancellation policy summary (e.g. Free till 1 hour of departure)"
    )
    
    # New fields based on UI requirements
    luggage_capacity = models.PositiveIntegerField(default=2, help_text="Luggage capacity (number of bags)")
    fuel_type = models.CharField(max_length=10, choices=FUEL_TYPE_CHOICES, help_text="Type of fuel used")
    is_ac = models.BooleanField(default=True, help_text="Designates whether the cab has AC")
    
    # Pricing logic fields
    price_per_km = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per kilometer")
    included_kms = models.PositiveIntegerField(help_text="Distance included in base price")
    extra_km_fare = models.DecimalField(max_digits=10, decimal_places=2, help_text="Fare per extra kilometer")
    driver_allowance = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, help_text="Driver allowance per day"
    )
    free_waiting_time_minutes = models.PositiveIntegerField(default=45, help_text="Free waiting time in minutes")
    
    is_active = models.BooleanField(default=True, help_text="Designates whether the cab is active")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        category_name = self.category.name if self.category else "No Category"
        return f"{self.title} ({category_name})"


class CabImage(TimeStampedModel):
    cab = models.ForeignKey(Cab, on_delete=models.CASCADE, related_name="images", help_text="Related cab")
    image = models.ImageField(upload_to="cabs/gallery/%Y/%m/", help_text="Image file for the cab")
    is_primary = models.BooleanField(default=False, help_text="Designates whether this is the primary image")
    order = models.PositiveIntegerField(default=0, help_text="Ordering of the image")

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Image for {self.cab.title}"


class CabInclusion(TimeStampedModel):
    """
    Stores inclusions/exclusions and specific metrics (e.g. 'Parking Charges: Included').
    """
    cab = models.ForeignKey(Cab, on_delete=models.CASCADE, related_name="inclusions", help_text="Related cab")
    label = models.CharField(max_length=255, help_text="Label of the inclusion (e.g., 'Parking Charges')")
    value = models.CharField(max_length=255, help_text="Value of the inclusion (e.g., 'Included')")
    is_included = models.BooleanField(default=True, help_text="Designates whether this is an inclusion")

    def __str__(self):
        return f"{self.label}: {self.value}"


class CabPolicy(TimeStampedModel):
    cab = models.ForeignKey(Cab, on_delete=models.CASCADE, related_name="policies", help_text="Related cab")
    title = models.CharField(max_length=255, help_text="Title of the policy")
    description = models.TextField(help_text="Description of the policy")

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
    
    cab = models.ForeignKey(Cab, on_delete=models.CASCADE, related_name="pricing_options", help_text="Related cab")
    option_type = models.CharField(max_length=20, choices=OPTION_TYPE_CHOICES, help_text="Type of pricing option")
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount for the option")
    description = models.TextField(blank=True, null=True, help_text="Description of the option")
    is_default = models.BooleanField(default=False, help_text="Designates whether this is the default option")

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

    cab = models.ForeignKey(Cab, on_delete=models.PROTECT, related_name="bookings", help_text="Related cab")
    
    pickup_location = models.CharField(max_length=255, help_text="Pickup location")
    drop_location = models.CharField(max_length=255, help_text="Drop location")
    pickup_datetime = models.DateTimeField(help_text="Date and time of pickup")
    
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE_CHOICES, help_text="Type of trip")
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total distance in km")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total amount for the booking")
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="pending",
        help_text="Status of the booking"
    )

    def __str__(self):
        return f"Booking #{self.id} - {self.cab.title}"
