from django.db import models
from apps.common.models import TimeStampedModel
from apps.properties.models import Property, RoomType, Discount

class HolidayPackage(TimeStampedModel):
    """
    Main model for Holiday Packages storing core information.
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    primary_location = models.CharField(max_length=255)
    secondary_locations = models.JSONField(default=list, blank=True, null=True)
    
    duration_days = models.PositiveSmallIntegerField()
    duration_nights = models.PositiveSmallIntegerField()
    
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.ForeignKey(
        Discount, on_delete=models.SET_NULL, null=True, blank=True, related_name="holiday_packages"
    )
    
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    review_count = models.PositiveIntegerField(default=0)
    
    short_description = models.TextField()
    highlights = models.JSONField(default=list, blank=True, null=True)
    terms_and_conditions = models.TextField()
    
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Holiday Package"
        verbose_name_plural = "Holiday Packages"

    def __str__(self):
        return self.title

class PackageImage(TimeStampedModel):
    """
    Gallery for Holiday Packages.
    """
    package = models.ForeignKey(HolidayPackage, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="packages/gallery/%Y/%m/")
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

class PackageFeature(TimeStampedModel):
    """
    Represents features like Sightseeing, Stay, Transport, Meals.
    """
    FEATURE_TYPE_CHOICES = [
        ("sightseeing", "Sightseeing"),
        ("stay", "Stay"),
        ("transport", "Transport"),
        ("meals", "Meals"),
    ]
    
    package = models.ForeignKey(HolidayPackage, on_delete=models.CASCADE, related_name="features")
    feature_type = models.CharField(max_length=20, choices=FEATURE_TYPE_CHOICES)
    is_included = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_feature_type_display()} - {self.package.title}"

class PackageItinerary(TimeStampedModel):
    """
    Day-by-day itinerary plan for the package.
    """
    TRANSPORT_CHOICES = [
        ("cab", "Cab"),
        ("boat", "Boat"),
        ("train", "Train"),
        ("flight", "Flight"),
        ("self", "Self Drive"),
    ]

    package = models.ForeignKey(HolidayPackage, on_delete=models.CASCADE, related_name="itinerary")
    day_number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    from_location = models.CharField(max_length=255, blank=True)
    to_location = models.CharField(max_length=255, blank=True)
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_CHOICES, blank=True, null=True)
    
    # Optional stay association per day
    stay_property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True)
    
    # ADDED: Link to Houseboat for days involving houseboat stays
    stay_houseboat = models.ForeignKey(
        "houseboats.HouseBoat",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="package_itineraries"
    )
    
    stay_nights = models.PositiveSmallIntegerField(default=0)
    
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["day_number", "order"]
        verbose_name_plural = "Package Itineraries"

    def __str__(self):
        return f"Day {self.day_number}: {self.title} ({self.package.title})"

class PackageAccommodation(TimeStampedModel):
    """
    Detailed accommodation information for the package.
    """
    package = models.ForeignKey(HolidayPackage, on_delete=models.CASCADE, related_name="accommodations")
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL, null=True, blank=True)
    nights = models.PositiveSmallIntegerField()
    meals_included = models.JSONField(default=list, blank=True, null=True)

    def __str__(self):
        return f"{self.property.name} - {self.package.title}"

class PackageActivity(TimeStampedModel):
    """
    Activities associated with a package or specific itinerary day.
    """
    package = models.ForeignKey(HolidayPackage, on_delete=models.CASCADE, related_name="activities")
    itinerary_day = models.ForeignKey(PackageItinerary, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities")
    
    # ADDED: Link to core Activity model for pricing and reusability
    activity = models.ForeignKey(
        "activities.Activity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="package_activities"
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to="packages/activities/%Y/%m/", null=True, blank=True)

    class Meta:
        verbose_name_plural = "Package Activities"

    def __str__(self):
        return self.name

class PackageTransfer(TimeStampedModel):
    """
    Transfer information (Cab/Boat/etc) per package or specific day.
    """
    TRANSPORT_CHOICES = [
        ("cab", "Cab"),
        ("boat", "Boat"),
        ("train", "Train"),
        ("flight", "Flight"),
    ]

    package = models.ForeignKey(HolidayPackage, on_delete=models.CASCADE, related_name="transfers")
    itinerary_day = models.ForeignKey(PackageItinerary, on_delete=models.SET_NULL, null=True, blank=True, related_name="transfers")
    
    # ADDED: Link to CabCategory for structured transport info
    cab_category = models.ForeignKey(
        "cabs.CabCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="package_transfers"
    )
    
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_CHOICES)
    description = models.TextField()

    def __str__(self):
        return f"{self.get_transport_type_display()} Transfer - {self.package.title}"

class PackageInclusion(TimeStampedModel):
    """
    Inclusions and exclusions for the holiday package.
    """
    package = models.ForeignKey(HolidayPackage, on_delete=models.CASCADE, related_name="inclusions")
    text = models.TextField()
    is_included = models.BooleanField(default=True)

    def __str__(self):
        status = "Inclusion" if self.is_included else "Exclusion"
        return f"{status}: {self.text[:50]}..."
