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

    name = models.CharField(max_length=255, help_text="Name of the discount")
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, help_text="Type of discount (Percentage or Flat Amount)")
    value = models.DecimalField(max_digits=12, decimal_places=2, help_text="Value of the discount")
    is_active = models.BooleanField(default=True, help_text="Designates whether this discount is active")

    def __str__(self):
        suffix = "%" if self.discount_type == "percentage" else ""
        return f"{self.name} ({self.value}{suffix})"


class Amenity(TimeStampedModel):
    """
    Reusable Amenity model for multi-select association with Properties.
    """
    name = models.CharField(max_length=255, help_text="Name of the amenity")
    icon = models.ImageField(upload_to="amenities/icons/", blank=True, null=True, help_text="Icon for the amenity")

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

    name = models.CharField(max_length=255, help_text="Name of the property")
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, help_text="Type of property")
    city = models.CharField(max_length=100, help_text="City where the property is located")
    area = models.CharField(max_length=100, blank=True, null=True, help_text="Area or locality")
    state = models.CharField(max_length=100, help_text="State where the property is located")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Longitude coordinate")
    
    # Rating and reviews
    star_rating = models.PositiveSmallIntegerField(blank=True, null=True, help_text="Star rating of the property")
    review_rating = models.DecimalField(
        max_digits=3, decimal_places=1, blank=True, null=True, help_text="Average review rating"
    )
    review_count = models.PositiveIntegerField(default=0, help_text="Total number of reviews")
    
    # Availability and policies
    check_in_time = models.TimeField(help_text="Check-in time")
    check_out_time = models.TimeField(help_text="Check-out time")
    description = models.TextField(help_text="Detailed description of the property")
    
    # Rule-based Behavior & Relations
    amenities = models.ManyToManyField(Amenity, blank=True, related_name="properties", help_text="Amenities available at the property")
    discount = models.ForeignKey(
        Discount, on_delete=models.SET_NULL, null=True, blank=True, related_name="properties", help_text="Applicable discount"
    )
    rules = models.TextField(blank=True, null=True, help_text="House rules for guests")
    cancellation_policy = models.TextField(blank=True, null=True, help_text="Cancellation policy for the property")
    
    # Financials (Property Level)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=12.00, help_text="GST percentage applicable")
    
    # Entire Place Booking Configuration
    allow_entire_place_booking = models.BooleanField(default=False, help_text="Allow booking the entire place")
    entire_place_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Price for booking the entire place")
    entire_place_max_guests = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum guests for entire place booking")
    
    is_active = models.BooleanField(default=True, help_text="Designates whether this property is active")

    class Meta:
        verbose_name_plural = "Properties"

    def __str__(self):
        return f"{self.name} ({self.get_property_type_display()})"

    @builtins.property
    def primary_image(self):
        """
        Returns the first primary image or the first available image.
        Optimized to use prefetched data if available.
        """
        if hasattr(self, "_prefetched_objects_cache") and "images" in self._prefetched_objects_cache:
            images = list(self.images.all())
            primary = next((img for img in images if img.is_primary), None)
            return primary or (images[0] if images else None)
        return self.images.filter(is_primary=True).first() or self.images.first()

    @builtins.property
    def discount_label(self):
        """Returns a formatted discount label if a discount is active."""
        if not self.discount or not self.discount.is_active:
            return ""
        
        if self.discount.discount_type == "percentage":
            return f"{int(self.discount.value)}% OFF"
        return f"₹{int(self.discount.value)} OFF"

    def calculate_pricing(self, base_price):
        """
        Calculates a full pricing dictionary for a given base price based on property settings.
        Maintains consistent logic across all APIs.
        """
        if not base_price:
            return {
                "price_from": "0.00",
                "discounted_price_from": "0.00",
                "discount_label": "",
            }

        # Calculate discount
        discounted_price = Decimal(base_price)
        discount_label = self.discount_label

        if self.discount and self.discount.is_active:
            if self.discount.discount_type == "percentage":
                discount_amount = (Decimal(base_price) * self.discount.value) / Decimal("100")
                discounted_price = Decimal(base_price) - discount_amount
            else:
                discounted_price = max(Decimal("0.00"), Decimal(base_price) - self.discount.value)

        # Calculate GST based on the discounted price
        gst_factor = Decimal(str(self.gst_percent)) / Decimal("100")
        gst_amount = (discounted_price * gst_factor).quantize(Decimal("0.01"))
        total_payable = (discounted_price + gst_amount).quantize(Decimal("0.01"))

        return {
            "price_from": f"{Decimal(base_price):.2f}",
            "discounted_price_from": f"{discounted_price:.2f}",
            "discount_label": discount_label,
            "gst_percent": self.gst_percent,
            "gst_amount": f"{gst_amount:.2f}",
            "total_payable": f"{total_payable:.2f}",
        }


class RoomType(TimeStampedModel):
    """
    Bookable units within a Property. Pricing inherits from the Property.
    """
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="room_types", help_text="Related property"
    )
    name = models.CharField(max_length=255, help_text="Name of the room type")
    max_guests = models.PositiveIntegerField(help_text="Maximum number of guests")
    bedroom_count = models.PositiveIntegerField(blank=True, null=True, help_text="Number of bedrooms")
    has_breakfast = models.BooleanField(default=False, help_text="Breakfast included")
    description = models.TextField(blank=True, null=True, help_text="Detailed description of the room type")
    
    refund_policy = models.TextField(help_text="Policy for refunds")
    booking_policy = models.TextField(help_text="Policy for booking")
    
    # Core price without tax or discounts
    base_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Base price per night")
    total_units = models.PositiveIntegerField(help_text="Total number of units available")
    is_entire_place = models.BooleanField(default=False, help_text="Is this an entire place booking?")

    def __str__(self):
        return f"{self.name} at {self.property.name}"

    @builtins.property
    def primary_image(self):
        """
        Returns the first primary image or the first available image for this room type.
        Optimized to use prefetched data if available.
        """
        if hasattr(self, "_prefetched_objects_cache") and "images" in self._prefetched_objects_cache:
            images = list(self.images.all())
            primary = next((img for img in images if img.is_primary), None)
            return primary or (images[0] if images else None)
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
        Property, on_delete=models.CASCADE, related_name="images", help_text="Related property"
    )
    image = models.ImageField(upload_to="properties/gallery/%Y/%m/", help_text="Image file")
    is_primary = models.BooleanField(default=False, help_text="Is this the primary image?")
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    alt_text = models.CharField(max_length=255, blank=True, null=True, help_text="Alternative text for accessibility")

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Image for {self.property.name}"


class RoomTypeImage(TimeStampedModel):
    room_type = models.ForeignKey(
        RoomType, on_delete=models.CASCADE, related_name="images", help_text="Related room type"
    )
    image = models.ImageField(upload_to="room_types/gallery/%Y/%m/", help_text="Image file")
    is_primary = models.BooleanField(default=False, help_text="Is this the primary image?")
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    alt_text = models.CharField(max_length=255, blank=True, null=True, help_text="Alternative text for accessibility")

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Image for {self.room_type.property.name} - {self.room_type.name}"


class RoomOption(TimeStampedModel):
    """
    Different pricing options/packages for a RoomType (e.g., Breakfast Included, Full Board).
    """
    room_type = models.ForeignKey(
        RoomType, on_delete=models.CASCADE, related_name="options", help_text="Related room type"
    )
    name = models.CharField(max_length=255, help_text="Option name (e.g. Breakfast Included)")
    description = models.TextField(blank=True, null=True, help_text="Short description of this option")
    
    # Pricing overrides
    base_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Price for this option")
    
    # Meal Plan
    has_breakfast = models.BooleanField(default=False, help_text="Breakfast included")
    has_lunch = models.BooleanField(default=False, help_text="Lunch included")
    has_dinner = models.BooleanField(default=False, help_text="Dinner included")
    
    # Policies
    is_refundable = models.BooleanField(default=False, help_text="Is this option refundable?")
    cancellation_policy = models.TextField(blank=True, null=True, help_text="Specific cancellation policy")

    def __str__(self):
        return f"{self.name} - {self.room_type.name}"

    @builtins.property
    def discount_amount(self):
        """Calculates discount amount based on property-level discount."""
        discount_obj = self.room_type.property.discount
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
        gst_factor = self.room_type.property.gst_percent / Decimal("100.00")
        return (self.discounted_price * gst_factor).quantize(Decimal("0.01"))

    @builtins.property
    def total_payable_amount(self):
        """Final amount including discount and GST."""
        return self.discounted_price + self.gst_amount


class FamousPlace(TimeStampedModel):
    name = models.CharField(max_length=255, help_text="Name of the famous place")
    description = models.TextField(help_text="Detailed description of the place")
    city = models.CharField(max_length=100, db_index=True, help_text="City where the place is located")
    location = models.CharField(max_length=255, help_text="Specific location/address")
    entry_fee = models.CharField(max_length=255, blank=True, null=True, help_text="Entry fee information (e.g., 'INR 15 per person')")
    timings = models.CharField(max_length=255, blank=True, null=True, help_text="Opening and closing timings")
    is_active = models.BooleanField(default=True, help_text="Designates whether this place is active")

    def __str__(self):
        return f"{self.name} ({self.city})"
