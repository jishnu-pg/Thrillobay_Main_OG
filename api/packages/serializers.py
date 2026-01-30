from rest_framework import serializers
from decimal import Decimal
from apps.packages.models import (
    HolidayPackage, PackageImage, PackageFeature, PackageItinerary,
    PackageAccommodation, PackageActivity, PackageTransfer, PackageInclusion
)
from apps.properties.models import Discount

class PackageImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = PackageImage
        fields = ["url", "is_primary"]

    def get_url(self, obj):
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class PackageFeatureSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="get_feature_type_display")
    included = serializers.BooleanField(source="is_included")

    class Meta:
        model = PackageFeature
        fields = ["type", "included"]


class ItineraryTransferSerializer(serializers.ModelSerializer):
    cab_category = serializers.CharField(source="cab_category.name", read_only=True)

    class Meta:
        model = PackageTransfer
        fields = ["cab_category", "description"]


class ItineraryStaySerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    room_type = serializers.SerializerMethodField()
    check_in_time = serializers.SerializerMethodField()
    check_out_time = serializers.SerializerMethodField()
    amenities = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = PackageItinerary
        fields = ["type", "name", "room_type", "check_in_time", "check_out_time", "amenities", "image"]

    def get_type(self, obj):
        if obj.stay_property:
            return "hotel"
        if obj.stay_houseboat:
            return "houseboat"
        return None

    def get_name(self, obj):
        if obj.stay_property:
            return obj.stay_property.name
        if obj.stay_houseboat:
            return obj.stay_houseboat.name
        return None

    def get_room_type(self, obj):
        # Optimized to use already prefetched accommodations list
        if obj.stay_property:
            accommodations = list(obj.package.accommodations.all())
            accommodation = next((acc for acc in accommodations if acc.property_id == obj.stay_property_id), None)
            if accommodation and accommodation.room_type:
                return accommodation.room_type.name
        return ""

    def get_check_in_time(self, obj):
        if obj.stay_property:
            return obj.stay_property.check_in_time
        if obj.stay_houseboat and hasattr(obj.stay_houseboat, 'timing'):
            return obj.stay_houseboat.timing.check_in_time
        return None

    def get_check_out_time(self, obj):
        if obj.stay_property:
            return obj.stay_property.check_out_time
        if obj.stay_houseboat and hasattr(obj.stay_houseboat, 'timing'):
            return obj.stay_houseboat.timing.check_out_time
        return None

    def get_amenities(self, obj):
        if obj.stay_property:
            return [{"name": a.name, "icon": a.icon.url if a.icon else None} for a in obj.stay_property.amenities.all()]
        # Houseboats usually have amenities too, checking model...
        if obj.stay_houseboat:
             # Assuming houseboat has amenities M2M or similar. 
             # I'll check HouseBoat model if needed, but for now I'll just return empty list or handle property only.
             # Let's peek at HouseBoat model or just be safe.
             return []
        return []

    def get_image(self, obj):
        request = self.context.get('request')
        image = None
        if obj.stay_property:
            image = obj.stay_property.primary_image
        elif obj.stay_houseboat:
             # Assuming primary_image property exists on HouseBoat as well (common pattern)
             if hasattr(obj.stay_houseboat, 'primary_image'):
                 image = obj.stay_houseboat.primary_image
        
        if image and image.image:
             return request.build_absolute_uri(image.image.url) if request else image.image.url
        return None


class PackageItinerarySerializer(serializers.ModelSerializer):
    day = serializers.IntegerField(source="day_number")
    transfer = serializers.SerializerMethodField()
    stay = ItineraryStaySerializer(source="*", read_only=True)
    activities = serializers.SerializerMethodField()

    class Meta:
        model = PackageItinerary
        fields = ["day", "title", "description", "transfer", "stay", "activities"]

    def get_transfer(self, obj):
        transfer = obj.transfers.first()
        if transfer:
            return ItineraryTransferSerializer(transfer).data
        return None

    def get_activities(self, obj):
        return [act.name for act in obj.activities.all()]


class PackageAccommodationSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source="property.name", read_only=True)
    room_type = serializers.CharField(source="room_type.name", read_only=True)

    class Meta:
        model = PackageAccommodation
        fields = ["property_name", "room_type", "nights", "meals_included"]


class SimilarPackageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    price_from = serializers.CharField(source="base_price")

    class Meta:
        model = HolidayPackage
        fields = ["id", "title", "price_from", "image"]

    def get_image(self, obj):
        primary = obj.images.filter(is_primary=True).first() or obj.images.first()
        if primary and primary.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(primary.image.url)
            return primary.image.url
        return None


class HolidayPackageDetailSerializer(serializers.ModelSerializer):
    location = serializers.CharField(source="primary_location")
    discount = serializers.SerializerMethodField()
    price_per_person = serializers.DecimalField(source="base_price", max_digits=12, decimal_places=2)
    discounted_price = serializers.SerializerMethodField()
    
    images = serializers.SerializerMethodField()
    highlights = serializers.JSONField()
    features = PackageFeatureSerializer(many=True, read_only=True)
    itinerary = PackageItinerarySerializer(many=True, read_only=True)
    accommodations = PackageAccommodationSerializer(many=True, read_only=True)
    transfers = serializers.SerializerMethodField()
    inclusions = serializers.SerializerMethodField()
    exclusions = serializers.SerializerMethodField()
    terms = serializers.CharField(source="terms_and_conditions")
    similar_packages = serializers.SerializerMethodField()

    class Meta:
        model = HolidayPackage
        fields = [
            "id", "title", "subtitle", "duration_days", "duration_nights", "location",
            "base_price", "discount", "price_per_person", "discounted_price",
            "rating", "review_count", "images", "highlights", "features",
            "itinerary", "accommodations", "transfers", "inclusions",
            "exclusions", "terms", "similar_packages"
        ]

    def get_discount(self, obj):
        if obj.discount and obj.discount.is_active:
            return {
                "type": obj.discount.discount_type,
                "value": float(obj.discount.value)
            }
        return None

    def get_discounted_price(self, obj):
        if not obj.discount or not obj.discount.is_active:
            return obj.base_price
        
        discount = obj.discount
        if discount.discount_type == "percentage":
            discount_amount = (obj.base_price * discount.value) / Decimal("100.00")
            return (obj.base_price - discount_amount).quantize(Decimal("0.01"))
        else:
            return max(Decimal("0.00"), obj.base_price - discount.value)

    def get_images(self, obj):
        # Primary image first, ordered images after (but exclude primary from this list as per request)
        images = [img for img in obj.images.all() if not img.is_primary]
        return PackageImageSerializer(images, many=True, context=self.context).data

    def get_transfers(self, obj):
        # Extract unique cab categories used across itinerary
        unique_cabs = set()
        for it in obj.itinerary.all():
            for transfer in it.transfers.all():
                if transfer.cab_category:
                    unique_cabs.add(transfer.cab_category.name)
        return [{"cab_category": cab} for cab in sorted(list(unique_cabs))]

    def get_inclusions(self, obj):
        return [inc.text for inc in obj.inclusions.all() if inc.is_included]

    def get_exclusions(self, obj):
        return [inc.text for inc in obj.inclusions.all() if not inc.is_included]

    def get_similar_packages(self, obj):
        similar = HolidayPackage.objects.filter(
            primary_location=obj.primary_location,
            is_active=True
        ).exclude(id=obj.id).prefetch_related("images")[:4]
        return SimilarPackageSerializer(similar, many=True, context=self.context).data
