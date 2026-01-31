from rest_framework import serializers
from apps.properties.models import Property, Discount, Amenity
from apps.packages.models import HolidayPackage
from apps.houseboats.models import HouseBoat
from apps.activities.models import Activity
from apps.cabs.models import Cab
from decimal import Decimal

# --- SHARED UTILS ---

def get_absolute_image_url(request, image_obj):
    if image_obj and image_obj.image:
        if request:
            return request.build_absolute_uri(image_obj.image.url)
        return image_obj.image.url
    return None

# --- SERIALIZERS ---

class HotelListingSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()
    price_from = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    cta_label = serializers.SerializerMethodField()
    rating = serializers.DecimalField(source="review_rating", max_digits=3, decimal_places=1, read_only=True)

    class Meta:
        model = Property
        fields = [
            "id", "name", "location", "rating", "price_from", 
            "primary_image", "property_type", "cta_label"
        ]

    def get_location(self, obj):
        return f"{obj.city}, {obj.state}"

    def get_price_from(self, obj):
        # annotated 'min_price' will be available from View
        return getattr(obj, "min_price", None)

    def get_primary_image(self, obj):
        return get_absolute_image_url(self.context.get("request"), obj.primary_image)

    def get_cta_label(self, obj):
        return "Book Now"

class PackageListingSerializer(serializers.ModelSerializer):
    location = serializers.CharField(source="primary_location")
    price_from = serializers.DecimalField(source="base_price", max_digits=12, decimal_places=2)
    primary_image = serializers.SerializerMethodField()
    cta_label = serializers.SerializerMethodField()

    class Meta:
        model = HolidayPackage
        fields = [
            "id", "title", "location", "duration_days", "duration_nights", 
            "rating", "price_from", "primary_image", "cta_label"
        ]

    def get_primary_image(self, obj):
        img = obj.images.filter(is_primary=True).first() or obj.images.first()
        return get_absolute_image_url(self.context.get("request"), img)

    def get_cta_label(self, obj):
        return "View Details"

class HouseboatListingSerializer(serializers.ModelSerializer):
    price_from = serializers.DecimalField(source="base_price_per_night", max_digits=12, decimal_places=2)
    primary_image = serializers.SerializerMethodField()
    cta_label = serializers.SerializerMethodField()
    bedrooms = serializers.IntegerField(source="specification.bedrooms")

    class Meta:
        model = HouseBoat
        fields = [
            "id", "name", "location", "rating", "price_from", 
            "primary_image", "cta_label", "bedrooms"
        ]

    def get_primary_image(self, obj):
        img = obj.images.filter(is_primary=True).first() or obj.images.first()
        return get_absolute_image_url(self.context.get("request"), img)

    def get_cta_label(self, obj):
        return "Book Now"

class ActivityListingSerializer(serializers.ModelSerializer):
    price_from = serializers.DecimalField(source="base_price", max_digits=12, decimal_places=2)
    primary_image = serializers.SerializerMethodField()
    cta_label = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            "id", "title", "location", "rating", "price_from", 
            "primary_image", "cta_label", "duration_days"
        ]

    def get_primary_image(self, obj):
        img = obj.images.filter(is_primary=True).first() or obj.images.first()
        return get_absolute_image_url(self.context.get("request"), img)

    def get_cta_label(self, obj):
        return "Book Now"

class CabListingSerializer(serializers.ModelSerializer):
    price_from = serializers.DecimalField(source="base_price", max_digits=12, decimal_places=2)
    discounted_price = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    cta_label = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    specs = serializers.SerializerMethodField()
    policies = serializers.SerializerMethodField()
    extra_km_fare = serializers.SerializerMethodField()

    class Meta:
        model = Cab
        fields = [
            "id", "title", "location", "rating", "review_count", 
            "price_from", "discounted_price", "specs", "policies",
            "extra_km_fare", "primary_image", "cta_label"
        ]

    def get_discounted_price(self, obj):
        if obj.discount and obj.discount.is_active:
            discount = obj.discount
            if discount.discount_type == "percentage":
                discount_amount = (obj.base_price * discount.value) / Decimal("100.00")
                return (obj.base_price - discount_amount).quantize(Decimal("0.01"))
            else:
                return max(Decimal("0.00"), obj.base_price - discount.value)
        return None

    def get_primary_image(self, obj):
        img = obj.images.filter(is_primary=True).first() or obj.images.first()
        return get_absolute_image_url(self.context.get("request"), img)

    def get_cta_label(self, obj):
        return "Book Now"
        
    def get_rating(self, obj):
        # Placeholder or if Cab model has reviews later
        return "5.0"

    def get_review_count(self, obj):
        # Placeholder or if Cab model has reviews later
        return 100

    def get_specs(self, obj):
        return {
            "is_ac": "AC" if obj.is_ac else "Non-AC",
            "seats": f"{obj.capacity} Seats",
            "fuel_type": obj.get_fuel_type_display(),
            "luggage": f"{obj.luggage_capacity} Bags"
        }

    def get_policies(self, obj):
        return {
            "cancellation": obj.cancellation_policy or "Free till departure time"
        }

    def get_extra_km_fare(self, obj):
        return f"₹{obj.extra_km_fare}/km after {obj.included_kms} kms"
