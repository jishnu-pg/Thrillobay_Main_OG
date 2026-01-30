from rest_framework import serializers
from apps.houseboats.models import (
    HouseBoat, HouseBoatImage, HouseBoatSpecification,
    HouseBoatTiming, HouseBoatMealPlan, HouseBoatInclusion, HouseBoatPolicy
)

class HouseBoatImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = HouseBoatImage
        fields = ["url", "is_primary"]

    def get_url(self, obj):
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class HouseBoatSpecificationSerializer(serializers.ModelSerializer):
    ac_type = serializers.CharField(source="get_ac_type_display", read_only=True)
    cruise_type = serializers.CharField(source="get_cruise_type_display", read_only=True)
    
    class Meta:
        model = HouseBoatSpecification
        fields = ["bedrooms", "bathrooms", "max_guests", "ac_type", "cruise_type"]

class HouseBoatTimingSerializer(serializers.ModelSerializer):
    check_in_time = serializers.TimeField(format="%I:%M %p")
    check_out_time = serializers.TimeField(format="%I:%M %p")
    cruise_start_time = serializers.TimeField(format="%I:%M %p")
    cruise_end_time = serializers.TimeField(format="%I:%M %p")

    class Meta:
        model = HouseBoatTiming
        fields = ["check_in_time", "check_out_time", "cruise_start_time", "cruise_end_time"]

class HouseBoatMealPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = HouseBoatMealPlan
        fields = ["breakfast_included", "lunch_included", "dinner_included", "veg_only"]

class SimilarHouseBoatSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    price_from = serializers.CharField(source="base_price_per_night")

    class Meta:
        model = HouseBoat
        fields = ["id", "name", "price_from", "image"]

    def get_image(self, obj):
        primary = obj.images.filter(is_primary=True).first() or obj.images.first()
        if primary and primary.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(primary.image.url)
            return primary.image.url
        return None


class HouseBoatDetailSerializer(serializers.ModelSerializer):
    houseboat_type = serializers.SerializerMethodField()
    pricing = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    specification = HouseBoatSpecificationSerializer(read_only=True)
    timing = HouseBoatTimingSerializer(read_only=True)
    meals = HouseBoatMealPlanSerializer(source="meal_plan", read_only=True)
    inclusions = serializers.SerializerMethodField()
    policies = serializers.SerializerMethodField()
    similar_houseboats = serializers.SerializerMethodField()

    class Meta:
        model = HouseBoat
        fields = [
            "id", "name", "location", "rating", "review_count", "houseboat_type",
            "pricing", "images", "specification", "timing", "meals",
            "inclusions", "policies", "similar_houseboats"
        ]

    def get_houseboat_type(self, obj):
        if hasattr(obj, "specification"):
            display = obj.specification.get_cruise_type_display()
            if obj.specification.cruise_type == "overnight_cruise":
                return "Day & Night"
            return display
        return ""

    def get_pricing(self, obj):
        return obj.calculate_pricing()

    def get_images(self, obj):
        # Use prefetched and sorted images, excluding primary
        images = [img for img in obj.images.all() if not img.is_primary]
        return HouseBoatImageSerializer(images, many=True, context=self.context).data

    def get_inclusions(self, obj):
        # Using prefetched inclusions
        return [inc.text for inc in obj.inclusions.all() if inc.is_included]

    def get_policies(self, obj):
        if hasattr(obj, "policy"):
            return {
                "cancellation": obj.policy.cancellation_policy,
                "check_in_rules": obj.policy.house_rules
            }
        return {"cancellation": "", "check_in_rules": ""}

    def get_similar_houseboats(self, obj):
        similar = self.context.get("similar_houseboats", [])
        return SimilarHouseBoatSerializer(similar, many=True, context=self.context).data

