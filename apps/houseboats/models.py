from django.db import models
from apps.common.models import TimeStampedModel
from apps.properties.models import Discount

class HouseBoat(TimeStampedModel):
    """
    Main model for Houseboats representing core entity information.
    """
    name = models.CharField(max_length=255, help_text="Name of the houseboat")
    slug = models.SlugField(max_length=255, unique=True, help_text="Unique slug for the houseboat URL")
    location = models.CharField(max_length=255, help_text="Location of the houseboat")
    description = models.TextField(help_text="Detailed description of the houseboat")
    
    base_price_per_night = models.DecimalField(max_digits=12, decimal_places=2, help_text="Base price per night")
    discount = models.ForeignKey(
        Discount, on_delete=models.SET_NULL, null=True, blank=True, related_name="houseboats", help_text="Applicable discount for the houseboat"
    )
    
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, help_text="Average rating of the houseboat")
    review_count = models.PositiveIntegerField(default=0, help_text="Total number of reviews")
    
    is_active = models.BooleanField(default=True, help_text="Designates whether the houseboat is active")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Houseboat"
        verbose_name_plural = "Houseboats"

    def __str__(self):
        return self.name

    def calculate_pricing(self):
        """
        Calculates pricing dictionary including discounts.
        """
        base = self.base_price_per_night
        discounted = base
        discount_data = None

        if self.discount and self.discount.is_active:
            discount_data = {
                "type": self.discount.discount_type,
                "value": float(self.discount.value)
            }
            if self.discount.discount_type == "percentage":
                discount_amount = (base * self.discount.value) / 100
                discounted = base - discount_amount
            else:
                discounted = max(0, base - self.discount.value)

        return {
            "base_price_per_night": float(base),
            "discount": discount_data,
            "discounted_price": float(discounted),
            "price_display": f"₹ {int(discounted):,} / Night"
        }

class HouseBoatImage(TimeStampedModel):
    """
    Gallery for Houseboat images.
    """
    houseboat = models.ForeignKey(HouseBoat, on_delete=models.CASCADE, related_name="images", help_text="Related houseboat")
    image = models.ImageField(upload_to="houseboats/gallery/%Y/%m/", help_text="Image file for the houseboat")
    is_primary = models.BooleanField(default=False, help_text="Designates whether this is the primary image")
    order = models.PositiveIntegerField(default=0, help_text="Ordering of the image")

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

    houseboat = models.OneToOneField(HouseBoat, on_delete=models.CASCADE, related_name="specification", help_text="Related houseboat")
    bedrooms = models.PositiveSmallIntegerField(help_text="Number of bedrooms")
    bathrooms = models.PositiveSmallIntegerField(help_text="Number of bathrooms")
    max_guests = models.PositiveSmallIntegerField(help_text="Maximum number of guests")
    ac_type = models.CharField(max_length=20, choices=AC_TYPE_CHOICES, help_text="Type of air conditioning")
    cruise_type = models.CharField(max_length=20, choices=CRUISE_TYPE_CHOICES, help_text="Type of cruise")

    def __str__(self):
        return f"Specs for {self.houseboat.name}"

class HouseBoatTiming(TimeStampedModel):
    """
    Check-in, Check-out, and Cruise timing policies.
    """
    houseboat = models.OneToOneField(HouseBoat, on_delete=models.CASCADE, related_name="timing", help_text="Related houseboat")
    check_in_time = models.TimeField(help_text="Check-in time")
    check_out_time = models.TimeField(help_text="Check-out time")
    cruise_start_time = models.TimeField(help_text="Cruise start time")
    cruise_end_time = models.TimeField(help_text="Cruise end time")

    def __str__(self):
        return f"Timings for {self.houseboat.name}"

class HouseBoatMealPlan(TimeStampedModel):
    """
    Specific meal and food policies for houseboats.
    """
    houseboat = models.OneToOneField(HouseBoat, on_delete=models.CASCADE, related_name="meal_plan", help_text="Related houseboat")
    breakfast_included = models.BooleanField(default=True, help_text="Designates whether breakfast is included")
    lunch_included = models.BooleanField(default=True, help_text="Designates whether lunch is included")
    dinner_included = models.BooleanField(default=True, help_text="Designates whether dinner is included")
    welcome_drink = models.BooleanField(default=True, help_text="Designates whether welcome drink is included")
    veg_only = models.BooleanField(default=False, help_text="Designates whether only vegetarian food is served")
    menu_description = models.TextField(blank=True, help_text="Description of the menu")

    def __str__(self):
        return f"Meal Plan for {self.houseboat.name}"

class HouseBoatRoute(TimeStampedModel):
    """
    Journey details for the houseboat.
    """
    houseboat = models.ForeignKey(HouseBoat, on_delete=models.CASCADE, related_name="routes", help_text="Related houseboat")
    boarding_point = models.CharField(max_length=255, help_text="Boarding point for the houseboat")
    drop_point = models.CharField(max_length=255, help_text="Drop point for the houseboat")
    route_description = models.TextField(help_text="Description of the route")

    def __str__(self):
        return f"Route for {self.houseboat.name}: {self.boarding_point} to {self.drop_point}"

class HouseBoatPolicy(TimeStampedModel):
    """
    Rules and internal policies for the houseboat.
    """
    houseboat = models.OneToOneField(HouseBoat, on_delete=models.CASCADE, related_name="policy", help_text="Related houseboat")
    cancellation_policy = models.TextField(help_text="Cancellation policy")
    refund_policy = models.TextField(help_text="Refund policy")
    house_rules = models.TextField(help_text="House rules")

    class Meta:
        verbose_name_plural = "Houseboat Policies"

    def __str__(self):
        return f"Policies for {self.houseboat.name}"

class HouseBoatInclusion(TimeStampedModel):
    """
    Items included or excluded from the base fare.
    """
    houseboat = models.ForeignKey(HouseBoat, on_delete=models.CASCADE, related_name="inclusions", help_text="Related houseboat")
    text = models.TextField(help_text="Inclusion/Exclusion text")
    is_included = models.BooleanField(default=True, help_text="Designates whether this is an inclusion")

    def __str__(self):
        status = "Inclusion" if self.is_included else "Exclusion"
        return f"{status}: {self.text[:50]}..."
