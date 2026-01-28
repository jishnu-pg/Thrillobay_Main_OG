from rest_framework import serializers
from decimal import Decimal
from apps.packages.models import (
    HolidayPackage, PackageImage, PackageFeature, PackageItinerary,
    PackageAccommodation, PackageActivity, PackageTransfer, PackageInclusion
)
from apps.properties.models import Discount

class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ["id", "name", "discount_type", "value"]

class PackageImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageImage
        fields = ["id", "image", "is_primary", "order"]

class PackageFeatureSerializer(serializers.ModelSerializer):
    feature_label = serializers.CharField(source="get_feature_type_display")

    class Meta:
        model = PackageFeature
        fields = ["id", "feature_type", "feature_label", "is_included"]

class PackageItinerarySerializer(serializers.ModelSerializer):
    stay_property_name = serializers.CharField(source="stay_property.name", read_only=True)
    transport_label = serializers.CharField(source="get_transport_type_display", read_only=True)

    class Meta:
        model = PackageItinerary
        fields = [
            "id", "day_number", "title", "description", 
            "from_location", "to_location", "transport_type", "transport_label",
            "stay_property", "stay_property_name", "stay_nights"
        ]

class PackageAccommodationSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source="property.name", read_only=True)
    room_type_name = serializers.CharField(source="room_type.name", read_only=True)

    class Meta:
        model = PackageAccommodation
        fields = ["id", "property", "property_name", "room_type", "room_type_name", "nights", "meals_included"]

class PackageActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageActivity
        fields = ["id", "itinerary_day", "name", "description", "image"]

class PackageTransferSerializer(serializers.ModelSerializer):
    transport_label = serializers.CharField(source="get_transport_type_display", read_only=True)

    class Meta:
        model = PackageTransfer
        fields = ["id", "itinerary_day", "transport_type", "transport_label", "description"]

class PackageInclusionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageInclusion
        fields = ["id", "text", "is_included"]

class HolidayPackageDetailSerializer(serializers.ModelSerializer):
    images = PackageImageSerializer(many=True, read_only=True)
    features = PackageFeatureSerializer(many=True, read_only=True)
    itinerary = PackageItinerarySerializer(many=True, read_only=True)
    accommodations = PackageAccommodationSerializer(many=True, read_only=True)
    activities = PackageActivitySerializer(many=True, read_only=True)
    transfers = PackageTransferSerializer(many=True, read_only=True)
    inclusions = serializers.SerializerMethodField()
    exclusions = serializers.SerializerMethodField()
    discount_details = DiscountSerializer(source="discount", read_only=True)
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = HolidayPackage
        fields = [
            "id", "title", "slug", "primary_location", "secondary_locations",
            "duration_days", "duration_nights", "base_price", "discount_details",
            "final_price", "rating", "review_count", "short_description",
            "highlights", "terms_and_conditions", "images", "features",
            "itinerary", "accommodations", "activities", "transfers",
            "inclusions", "exclusions"
        ]

    def get_final_price(self, obj):
        if not obj.discount or not obj.discount.is_active:
            return obj.base_price
        
        discount = obj.discount
        if discount.discount_type == "percentage":
            discount_amount = (obj.base_price * discount.value) / Decimal("100.00")
            return (obj.base_price - discount_amount).quantize(Decimal("0.01"))
        else:
            return max(Decimal("0.00"), obj.base_price - discount.value)

    def get_inclusions(self, obj):
        inclusions = obj.inclusions.filter(is_included=True)
        return PackageInclusionSerializer(inclusions, many=True).data

    def get_exclusions(self, obj):
        exclusions = obj.inclusions.filter(is_included=False)
        return PackageInclusionSerializer(exclusions, many=True).data
