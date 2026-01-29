from rest_framework import serializers
from apps.support.models import FAQ, FAQItem


class FAQItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQItem
        fields = ["id", "title", "description", "order"]


class FAQListSerializer(serializers.ModelSerializer):
    items = FAQItemSerializer(many=True, read_only=True)

    class Meta:
        model = FAQ
        fields = ["id", "location", "question", "items"]
