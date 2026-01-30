from rest_framework import serializers
from apps.activities.models import (
    Activity, ActivityImage, ActivityHighlight, 
    ActivityItinerary, ActivityPolicy, ActivityInclusion
)

class ActivityImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ActivityImage
        fields = ["url", "is_primary"]

    def get_url(self, obj):
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class ActivityItinerarySerializer(serializers.ModelSerializer):
    day = serializers.IntegerField(source="day_number")
    image = serializers.SerializerMethodField()

    class Meta:
        model = ActivityItinerary
        fields = ["day", "title", "description", "image"]

    def get_image(self, obj):
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class SimilarActivitySerializer(serializers.ModelSerializer):
    price_from = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = ["id", "title", "location", "price_from", "image"]

    def get_price_from(self, obj):
        return float(obj.base_price)

    def get_image(self, obj):
        # Use prefetched images
        images = list(obj.images.all())
        primary = next((img for img in images if img.is_primary), images[0] if images else None)
        if primary and primary.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(primary.image.url)
            return primary.image.url
        return None

class ActivityDetailSerializer(serializers.ModelSerializer):
    activity = serializers.SerializerMethodField()
    pricing = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()
    highlights = serializers.SerializerMethodField()
    itinerary = ActivityItinerarySerializer(many=True, read_only=True)
    inclusions = serializers.SerializerMethodField()
    exclusions = serializers.SerializerMethodField()
    policies = serializers.SerializerMethodField()
    similar_activities = serializers.SerializerMethodField()
    faqs = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            "activity", "pricing", "gallery", "highlights", 
            "itinerary", "inclusions", "exclusions", 
            "policies", "similar_activities", "faqs"
        ]

    def get_activity(self, obj):
        return {
            "id": obj.id,
            "title": obj.title,
            "location": obj.location,
            "duration_days": obj.duration_days,
            "difficulty": obj.get_difficulty_display(),
            "min_age": obj.min_age,
            "group_size": obj.group_size,
            "rating": float(obj.rating) if obj.rating else 0.0
        }

    def get_pricing(self, obj):
        return obj.calculate_pricing()

    def get_gallery(self, obj):
        images = list(obj.images.all())
        primary = next((img for img in images if img.is_primary), images[0] if images else None)
        
        request = self.context.get("request")
        def get_abs_url(img_obj):
            if img_obj and img_obj.image:
                if request:
                    return request.build_absolute_uri(img_obj.image.url)
                return img_obj.image.url
            return None

        return {
            "primary_image": get_abs_url(primary),
            "images": [get_abs_url(img) for img in images if not img.is_primary]
        }

    def get_highlights(self, obj):
        return [h.text for h in obj.highlights.all()]

    def get_inclusions(self, obj):
        return [inc.text for inc in obj.inclusions.all() if inc.is_included]

    def get_exclusions(self, obj):
        return [inc.text for inc in obj.inclusions.all() if not inc.is_included]

    def get_policies(self, obj):
        if hasattr(obj, "policy"):
            return {
                "terms_and_conditions": obj.policy.terms_and_conditions,
                "safety_guidelines": obj.policy.safety_guidelines
            }
        return {"terms_and_conditions": "", "safety_guidelines": ""}

    def get_similar_activities(self, obj):
        similar = self.context.get("similar_activities", [])
        return SimilarActivitySerializer(similar, many=True, context=self.context).data

    def get_faqs(self, obj):
        return self.context.get("faqs", [])
