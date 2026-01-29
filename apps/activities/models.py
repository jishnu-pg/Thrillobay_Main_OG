from django.db import models
from apps.common.models import TimeStampedModel
from apps.properties.models import Discount

class Activity(TimeStampedModel):
    """
    Main model for Activities / experiences (treks, sightseeing, adventure).
    """
    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("moderate", "Moderate"),
        ("hard", "Hard"),
    ]

    title = models.CharField(max_length=255, help_text="The name of the activity")
    slug = models.SlugField(max_length=255, unique=True, help_text="Unique slug for the activity URL")
    location = models.CharField(max_length=255, help_text="Location where the activity takes place")
    short_description = models.TextField(help_text="Brief summary of the activity")
    description = models.TextField(help_text="Detailed description of the activity")
    
    duration_days = models.PositiveSmallIntegerField(help_text="Duration of the activity in days")
    duration_nights = models.PositiveSmallIntegerField(default=0, help_text="Duration of the activity in nights")
    
    base_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Base price for the activity")
    discount = models.ForeignKey(
        Discount, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities", help_text="Applicable discount for the activity"
    )
    
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, help_text="Difficulty level of the activity")
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, help_text="Average rating of the activity")
    review_count = models.PositiveIntegerField(default=0, help_text="Total number of reviews")
    
    min_age = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Minimum age requirement for the activity")
    max_age = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Maximum age limit for the activity")
    group_size = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Maximum group size for the activity")
    
    is_active = models.BooleanField(default=True, help_text="Designates whether the activity is active and visible")

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Activities"

    def __str__(self):
        return self.title

    def calculate_pricing(self):
        """
        Calculates pricing dictionary including discounts.
        """
        base = self.base_price
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
            "base_price": float(base),
            "discount": discount_data,
            "discounted_price": float(discounted),
            "tax_included": True,
            "price_note": "Per person"
        }

class ActivityImage(TimeStampedModel):
    """
    Gallery for Activity images.
    """
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="images", help_text="Related activity")
    image = models.ImageField(upload_to="activities/gallery/%Y/%m/", help_text="Image file for the activity")
    is_primary = models.BooleanField(default=False, help_text="Designates whether this is the primary image")
    order = models.PositiveIntegerField(default=0, help_text="Ordering of the image")

    class Meta:
        ordering = ["order", "created_at"]

class ActivityFeature(TimeStampedModel):
    """
    Included icons section (Sightseeing, Stay, Transport, Meals).
    """
    FEATURE_TYPE_CHOICES = [
        ("sightseeing", "Sightseeing"),
        ("stay", "Stay"),
        ("transport", "Transport"),
        ("meals", "Meals"),
    ]
    
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="features", help_text="Related activity")
    feature_type = models.CharField(max_length=20, choices=FEATURE_TYPE_CHOICES, help_text="Type of the feature")
    is_included = models.BooleanField(default=True, help_text="Designates whether the feature is included")

    def __str__(self):
        return f"{self.get_feature_type_display()} - {self.activity.title}"

class ActivityHighlight(TimeStampedModel):
    """
    Top highlight bullet points for the activity.
    """
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="highlights", help_text="Related activity")
    text = models.TextField(help_text="Highlight text")

    def __str__(self):
        return f"Highlight for {self.activity.title}"

class ActivityItinerary(TimeStampedModel):
    """
    Day-by-day plan for activities.
    """
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="itinerary", help_text="Related activity")
    day_number = models.PositiveSmallIntegerField(help_text="Day number of the itinerary")
    title = models.CharField(max_length=255, help_text="Title of the itinerary day")
    description = models.TextField(help_text="Description of the itinerary day")
    image = models.ImageField(upload_to="activities/itinerary/%Y/%m/", null=True, blank=True, help_text="Image for the itinerary day")
    order = models.PositiveSmallIntegerField(default=0, help_text="Ordering of the itinerary day")

    class Meta:
        ordering = ["day_number", "order"]
        verbose_name_plural = "Activity Itineraries"

    def __str__(self):
        return f"Day {self.day_number}: {self.title} ({self.activity.title})"

class ActivityPolicy(TimeStampedModel):
    """
    Rules, safety guidelines, and terms.
    OneToOne relationship ensures one policy set per activity.
    """
    activity = models.OneToOneField(Activity, on_delete=models.CASCADE, related_name="policy", help_text="Related activity")
    terms_and_conditions = models.TextField(help_text="Terms and conditions for the activity")
    cancellation_policy = models.TextField(help_text="Cancellation policy for the activity")
    safety_guidelines = models.TextField(help_text="Safety guidelines for the activity")

    class Meta:
        verbose_name_plural = "Activity Policies"

    def __str__(self):
        return f"Policies for {self.activity.title}"

class ActivityInclusion(TimeStampedModel):
    """
    Items included or excluded from the activity package.
    """
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="inclusions", help_text="Related activity")
    text = models.TextField(help_text="Inclusion/Exclusion text")
    is_included = models.BooleanField(default=True, help_text="Designates whether this is an inclusion")

    def __str__(self):
        status = "Inclusion" if self.is_included else "Exclusion"
        return f"{status}: {self.text[:50]}..."
