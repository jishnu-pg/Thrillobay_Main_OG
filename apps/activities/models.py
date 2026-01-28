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

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    location = models.CharField(max_length=255)
    short_description = models.TextField()
    description = models.TextField()
    
    duration_days = models.PositiveSmallIntegerField()
    duration_nights = models.PositiveSmallIntegerField(default=0)
    
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.ForeignKey(
        Discount, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities"
    )
    
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    review_count = models.PositiveIntegerField(default=0)
    
    min_age = models.PositiveSmallIntegerField(null=True, blank=True)
    max_age = models.PositiveSmallIntegerField(null=True, blank=True)
    group_size = models.PositiveSmallIntegerField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Activities"

    def __str__(self):
        return self.title

class ActivityImage(TimeStampedModel):
    """
    Gallery for Activity images.
    """
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="activities/gallery/%Y/%m/")
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

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
    
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="features")
    feature_type = models.CharField(max_length=20, choices=FEATURE_TYPE_CHOICES)
    is_included = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_feature_type_display()} - {self.activity.title}"

class ActivityHighlight(TimeStampedModel):
    """
    Top highlight bullet points for the activity.
    """
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="highlights")
    text = models.TextField()

    def __str__(self):
        return f"Highlight for {self.activity.title}"

class ActivityItinerary(TimeStampedModel):
    """
    Day-by-day plan for activities.
    """
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="itinerary")
    day_number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to="activities/itinerary/%Y/%m/", null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

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
    activity = models.OneToOneField(Activity, on_delete=models.CASCADE, related_name="policy")
    terms_and_conditions = models.TextField()
    cancellation_policy = models.TextField()
    safety_guidelines = models.TextField()

    class Meta:
        verbose_name_plural = "Activity Policies"

    def __str__(self):
        return f"Policies for {self.activity.title}"

class ActivityInclusion(TimeStampedModel):
    """
    Items included or excluded from the activity package.
    """
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="inclusions")
    text = models.TextField()
    is_included = models.BooleanField(default=True)

    def __str__(self):
        status = "Inclusion" if self.is_included else "Exclusion"
        return f"{status}: {self.text[:50]}..."
