from django.db import models
from apps.common.models import TimeStampedModel
from apps.properties.models import Property, RoomType, Discount

class HolidayPackage(TimeStampedModel):
    """
    Main model for Holiday Packages storing core information.
    """
    title = models.CharField(max_length=255, help_text="Title of the holiday package")
    slug = models.SlugField(max_length=255, unique=True, help_text="Unique slug for the package URL")
    primary_location = models.CharField(max_length=255, help_text="Primary location of the package")
    secondary_locations = models.JSONField(default=list, blank=True, null=True, help_text="List of secondary locations")
    
    duration_days = models.PositiveSmallIntegerField(help_text="Duration of the package in days")
    duration_nights = models.PositiveSmallIntegerField(help_text="Duration of the package in nights")
    
    base_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Base price for the package")
    discount = models.ForeignKey(
        Discount, on_delete=models.SET_NULL, null=True, blank=True, related_name="holiday_packages", help_text="Applicable discount for the package"
    )
    
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, help_text="Average rating of the package")
    review_count = models.PositiveIntegerField(default=0, help_text="Total number of reviews")
    
    short_description = models.TextField(help_text="Brief summary of the package")
    highlights = models.JSONField(default=list, blank=True, null=True, help_text="List of package highlights")
    terms_and_conditions = models.TextField(help_text="Terms and conditions for the package")
    
    is_active = models.BooleanField(default=True, help_text="Designates whether the package is active")

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
    package = models.ForeignKey(HolidayPackage, on_delete=models.CASCADE, related_name="images", help_text="Related holiday package")
    image = models.ImageField(upload_to="packages/gallery/%Y/%m/", help_text="Image file for the package")
    is_primary = models.BooleanField(default=False, help_text="Designates whether this is the primary image")
    order = models.PositiveIntegerField(default=0, help_text="Ordering of the image")

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
    
    package = models.ForeignKey(HolidayPackage, on_delete=models.CASCADE, related_name="features", help_text="Related holiday package")
    feature_type = models.CharField(max_length=20, choices=FEATURE_TYPE_CHOICES, help_text="Type of feature")
    is_included = models.BooleanField(default=True, help_text="Designates whether the feature is included")

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

    package = models.ForeignKey(HolidayPackage, on_delete=models.CASCADE, related_name="itinerary", help_text="Related holiday package")
    day_number = models.PositiveSmallIntegerField(help_text="Day number of the itinerary")
    title = models.CharField(max_length=255, help_text="Title of the itinerary day")
    description = models.TextField(help_text="Description of the itinerary day")
    
    from_location = models.CharField(max_length=255, blank=True, help_text="Starting location")
    to_location = models.CharField(max_length=255, blank=True, help_text="Destination location")
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_CHOICES, blank=True, null=True, help_text="Type of transport")
    
    # Optional stay association per day
    stay_property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, help_text="Stay property for the day")
    
    # ADDED: Link to Houseboat for days involving houseboat stays
    stay_houseboat = models.ForeignKey(
        "houseboats.HouseBoat",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="package_itineraries",
        help_text="Stay houseboat for the day"
    )
    
    stay_nights = models.PositiveSmallIntegerField(default=0, help_text="Number of nights staying")
    
    order = models.PositiveSmallIntegerField(default=0, help_text="Ordering of the itinerary day")

    class Meta:
        ordering = ["day_number", "order"]
        verbose_name_plural = "Package Itineraries"

    def __str__(self):
        return f"Day {self.day_number}: {self.title} ({self.package.title})"

class PackageAccommodation(TimeStampedModel):
    """
    Detailed accommodation information for the package.
    """
    package = models.ForeignKey(HolidayPackage, on_delete=models.CASCADE, related_name="accommodations", help_text="Related holiday package")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, help_text="Accommodation property")
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL, null=True, blank=True, help_text="Type of room")
    nights = models.PositiveSmallIntegerField(help_text="Number of nights")
    meals_included = models.JSONField(default=list, blank=True, null=True, help_text="List of included meals")

    def __str__(self):
        return f"{self.property.name} - {self.package.title}"

class PackageActivity(TimeStampedModel):
    """
    Activities associated with a package or specific itinerary day.
    """
    package = models.ForeignKey(HolidayPackage, on_delete=models.CASCADE, related_name="activities", help_text="Related holiday package")
    itinerary_day = models.ForeignKey(PackageItinerary, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities", help_text="Related itinerary day")
    
    # ADDED: Link to core Activity model for pricing and reusability
    activity = models.ForeignKey(
        "activities.Activity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="package_activities",
        help_text="Related core activity"
    )
    
    name = models.CharField(max_length=255, help_text="Name of the activity")
    description = models.TextField(help_text="Description of the activity")
    image = models.ImageField(upload_to="packages/activities/%Y/%m/", null=True, blank=True, help_text="Image for the activity")

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

    package = models.ForeignKey(HolidayPackage, on_delete=models.CASCADE, related_name="transfers", help_text="Related holiday package")
    itinerary_day = models.ForeignKey(PackageItinerary, on_delete=models.SET_NULL, null=True, blank=True, related_name="transfers", help_text="Related itinerary day")
    
    # ADDED: Link to CabCategory for structured transport info
    cab_category = models.ForeignKey(
        "cabs.CabCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="package_transfers",
        help_text="Related cab category"
    )
    
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_CHOICES, help_text="Type of transport")
    description = models.TextField(help_text="Description of the transfer")

    def __str__(self):
        return f"{self.get_transport_type_display()} Transfer - {self.package.title}"

class PackageInclusion(TimeStampedModel):
    """
    Inclusions and exclusions for the holiday package.
    """
    package = models.ForeignKey(HolidayPackage, on_delete=models.CASCADE, related_name="inclusions", help_text="Related holiday package")
    text = models.TextField(help_text="Inclusion/Exclusion text")
    is_included = models.BooleanField(default=True, help_text="Designates whether this is an inclusion")

    def __str__(self):
        status = "Inclusion" if self.is_included else "Exclusion"
        return f"{status}: {self.text[:50]}..."
