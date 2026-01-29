from rest_framework import serializers
from apps.dining.models import FoodDestination, FoodDestinationImage

class FoodDestinationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodDestinationImage
        fields = ["id", "image", "is_primary"]

class FoodDestinationSerializer(serializers.ModelSerializer):
    images = FoodDestinationImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = FoodDestination
        fields = [
            "id",
            "name",
            "slug",
            "location",
            "description",
            "price_per_person",
            "rating",
            "reviews_count",
            "images",
        ]
