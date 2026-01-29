from django.db import models
from django.utils.text import slugify
from apps.common.models import TimeStampedModel

class FoodDestination(TimeStampedModel):
    name = models.CharField(max_length=255, help_text="Name of the food destination")
    slug = models.SlugField(max_length=255, unique=True, blank=True, help_text="Unique slug for the URL")
    location = models.CharField(max_length=255, help_text="Location (e.g., Sulthan Bathery, Wayanad)")
    description = models.TextField(help_text="Detailed description of the food destination")
    
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per person")
    
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0, help_text="Average rating (0.0 to 5.0)")
    reviews_count = models.PositiveIntegerField(default=0, help_text="Total number of reviews")
    
    is_active = models.BooleanField(default=True, help_text="Designates whether this destination is active")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class FoodDestinationImage(TimeStampedModel):
    food_destination = models.ForeignKey(
        FoodDestination, on_delete=models.CASCADE, related_name="images", help_text="Related food destination"
    )
    image = models.ImageField(upload_to="dining/gallery/%Y/%m/", help_text="Image of the food destination")
    is_primary = models.BooleanField(default=False, help_text="Designates whether this is the primary image")
    
    class Meta:
        ordering = ["-is_primary", "-created_at"]

    def __str__(self):
        return f"Image for {self.food_destination.name}"
