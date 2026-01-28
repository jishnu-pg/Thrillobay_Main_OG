import builtins
from decimal import Decimal
from django.db import models
from apps.common.models import TimeStampedModel


class Discount(TimeStampedModel):
    """
    Independent Discount model that can be applied to Properties.
    """
    DISCOUNT_TYPE_CHOICES = [
        ("percentage", "Percentage"),
        ("flat", "Flat Amount"),
    ]

    name = models.CharField(max_length=255)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        suffix = "%" if self.discount_type == "percentage" else ""
        return f"{self.name} ({self.value}{suffix})"


class Amenity(TimeStampedModel):
    """
    Reusable Amenity model for multi-select association with Properties.
    """
    name = models.CharField(max_length=255)
    icon = models.ImageField(upload_to="amenities/icons/", blank=True, null=True)

    class Meta:
        verbose_name_plural = "Amenities"

    def __str__(self):
        return self.name


class Property(TimeStampedModel):
    """
    Unified Property model representing Hotels, Resorts, Homestays, etc.
    """
    PROPERTY_TYPE_CHOICES = [
        ("hotel", "Hotel"),
        ("resort", "Resort"),
        ("homestay", "Homestay"),
        ("villa", "Villa"),
        ("apartment", "Apartment"),
    ]

    name = models.CharField(max_length=255)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100)
    
    # Rating and reviews
    star_rating = models.PositiveSmallIntegerField(blank=True, null=True)
    review_rating = models.DecimalField(
        max_digits=3, decimal_places=1, blank=True, null=True
    )
    review_count = models.PositiveIntegerField(default=0)
    
    # Availability and policies
    check_in_time = models.TimeField()
    check_out_time = models.TimeField()
    description = models.TextField()
    
    # Rule-based Behavior & Relations
    amenities = models.ManyToManyField(Amenity, blank=True, related_name="properties")
    discount = models.ForeignKey(
        Discount, on_delete=models.SET_NULL, null=True, blank=True, related_name="properties"
    )
    rules = models.TextField(blank=True, null=True)
    
    # Financials (Property Level)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=12.00)
    
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Properties"

    def __str__(self):
        return f"{self.name} ({self.get_property_type_display()})"

    @builtins.property
    def primary_image(self):
        """Returns the first primary image or the first available image."""
        return self.images.filter(is_primary=True).first() or self.images.first()


class RoomType(TimeStampedModel):
    """
    Bookable units within a Property. Pricing inherits from the Property.
    """
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="room_types"
    )
    name = models.CharField(max_length=255)
    max_guests = models.PositiveIntegerField()
    bedroom_count = models.PositiveIntegerField(blank=True, null=True)
    has_breakfast = models.BooleanField(default=False)
    
    refund_policy = models.TextField()
    booking_policy = models.TextField()
    
    # Core price without tax or discounts
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_units = models.PositiveIntegerField()
    is_entire_place = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} at {self.property.name}"

    @builtins.property
    def primary_image(self):
        """Returns the first primary image or the first available image for this room type."""
        return self.images.filter(is_primary=True).first() or self.images.first()

    # Dynamic Pricing Logic (Inherited from Property)
    
    @builtins.property
    def discount_amount(self):
        """Calculates discount amount based on property-level discount."""
        discount_obj = self.property.discount
        if not discount_obj or not discount_obj.is_active:
            return Decimal("0.00")
        
        if discount_obj.discount_type == "percentage":
            return (self.base_price * discount_obj.value / Decimal("100.00")).quantize(Decimal("0.01"))
        return discount_obj.value

    @builtins.property
    def discounted_price(self):
        """Base price minus any active property discount."""
        return max(Decimal("0.00"), self.base_price - self.discount_amount)

    @builtins.property
    def gst_amount(self):
        """Calculates GST based on discounted price."""
        gst_factor = self.property.gst_percent / Decimal("100.00")
        return (self.discounted_price * gst_factor).quantize(Decimal("0.01"))

    @builtins.property
    def total_payable_amount(self):
        """Final amount including discount and GST."""
        return self.discounted_price + self.gst_amount


class PropertyImage(TimeStampedModel):
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="properties/gallery/%Y/%m/")
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    alt_text = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Image for {self.property.name}"


class RoomTypeImage(TimeStampedModel):
    room_type = models.ForeignKey(
        RoomType, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="room_types/gallery/%Y/%m/")
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    alt_text = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Image for {self.room_type.property.name} - {self.room_type.name}"
