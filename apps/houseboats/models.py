from django.db import models
from apps.common.models import TimeStampedModel
from apps.properties.models import Discount

class HouseBoat(TimeStampedModel):
    """
    Main model for Houseboats representing core entity information.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    location = models.CharField(max_length=255)
    description = models.TextField()
    
    base_price_per_night = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.ForeignKey(
        Discount, on_delete=models.SET_NULL, null=True, blank=True, related_name="houseboats"
    )
    
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    review_count = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Houseboat"
        verbose_name_plural = "Houseboats"

    def __str__(self):
        return self.name

class HouseBoatImage(TimeStampedModel):
    """
    Gallery for Houseboat images.
    """
    houseboat = models.ForeignKey(HouseBoat, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="houseboats/gallery/%Y/%m/")
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

class HouseBoatSpecification(TimeStampedModel):
    """
    Structured specifications for houseboats.
    OneToOne relationship ensures one specification set per boat.
    """
    AC_TYPE_CHOICES = [
        ("full_time", "Full Time"),
        ("night_only", "Night Only"),
        ("none", "None"),
    ]
    CRUISE_TYPE_CHOICES = [
        ("day_cruise", "Day Cruise"),
        ("overnight_cruise", "Overnight Cruise"),
    ]

    houseboat = models.OneToOneField(HouseBoat, on_delete=models.CASCADE, related_name="specification")
    bedrooms = models.PositiveSmallIntegerField()
    bathrooms = models.PositiveSmallIntegerField()
    max_guests = models.PositiveSmallIntegerField()
    ac_type = models.CharField(max_length=20, choices=AC_TYPE_CHOICES)
    cruise_type = models.CharField(max_length=20, choices=CRUISE_TYPE_CHOICES)

    def __str__(self):
        return f"Specs for {self.houseboat.name}"

class HouseBoatTiming(TimeStampedModel):
    """
    Check-in, Check-out, and Cruise timing policies.
    """
    houseboat = models.OneToOneField(HouseBoat, on_delete=models.CASCADE, related_name="timing")
    check_in_time = models.TimeField()
    check_out_time = models.TimeField()
    cruise_start_time = models.TimeField()
    cruise_end_time = models.TimeField()

    def __str__(self):
        return f"Timings for {self.houseboat.name}"

class HouseBoatMealPlan(TimeStampedModel):
    """
    Specific meal and food policies for houseboats.
    """
    houseboat = models.OneToOneField(HouseBoat, on_delete=models.CASCADE, related_name="meal_plan")
    breakfast_included = models.BooleanField(default=True)
    lunch_included = models.BooleanField(default=True)
    dinner_included = models.BooleanField(default=True)
    welcome_drink = models.BooleanField(default=True)
    veg_only = models.BooleanField(default=False)
    menu_description = models.TextField(blank=True)

    def __str__(self):
        return f"Meal Plan for {self.houseboat.name}"

class HouseBoatRoute(TimeStampedModel):
    """
    Journey details for the houseboat.
    """
    houseboat = models.ForeignKey(HouseBoat, on_delete=models.CASCADE, related_name="routes")
    boarding_point = models.CharField(max_length=255)
    drop_point = models.CharField(max_length=255)
    route_description = models.TextField()

    def __str__(self):
        return f"Route for {self.houseboat.name}: {self.boarding_point} to {self.drop_point}"

class HouseBoatPolicy(TimeStampedModel):
    """
    Rules and internal policies for the houseboat.
    """
    houseboat = models.OneToOneField(HouseBoat, on_delete=models.CASCADE, related_name="policy")
    cancellation_policy = models.TextField()
    refund_policy = models.TextField()
    house_rules = models.TextField()

    class Meta:
        verbose_name_plural = "Houseboat Policies"

    def __str__(self):
        return f"Policies for {self.houseboat.name}"

class HouseBoatInclusion(TimeStampedModel):
    """
    Items included or excluded from the base fare.
    """
    houseboat = models.ForeignKey(HouseBoat, on_delete=models.CASCADE, related_name="inclusions")
    text = models.TextField()
    is_included = models.BooleanField(default=True)

    def __str__(self):
        status = "Inclusion" if self.is_included else "Exclusion"
        return f"{status}: {self.text[:50]}..."
