from rest_framework import serializers
from apps.properties.models import Property, RoomType, PropertyImage, RoomTypeImage


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["id", "image", "is_primary", "order"]


class RoomTypeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomTypeImage
        fields = ["id", "image", "is_primary", "order"]


class RoomTypeSerializer(serializers.ModelSerializer):
    gst_percent = serializers.SerializerMethodField()
    gst_amount = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    images = RoomTypeImageSerializer(many=True, read_only=True)

    class Meta:
        model = RoomType
        fields = [
            "id",
            "name",
            "max_guests",
            "base_price",
            "gst_percent",
            "gst_amount",
            "final_price",
            "has_breakfast",
            "primary_image",
            "images",
        ]

    def get_gst_percent(self, obj):
        return obj.property.gst_percent

    def get_gst_amount(self, obj):
        gst_percent = obj.property.gst_percent
        gst_amount = (obj.base_price * gst_percent) / 100
        return gst_amount.quantize(obj.base_price)

    def get_final_price(self, obj):
        gst_percent = obj.property.gst_percent
        gst_amount = (obj.base_price * gst_percent) / 100
        final_price = obj.base_price + gst_amount
        return final_price.quantize(obj.base_price)

    def get_primary_image(self, obj):
        image_obj = obj.primary_image
        if image_obj and image_obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(image_obj.image.url)
            return image_obj.image.url
        return None


class PropertyListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "name",
            "city",
            "state",
            "rating",
            "property_type",
            "primary_image",
        ]

    def get_primary_image(self, obj):
        image_obj = obj.primary_image
        if image_obj and image_obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(image_obj.image.url)
            return image_obj.image.url
        return None


class PropertyDetailSerializer(serializers.ModelSerializer):
    room_types = RoomTypeSerializer(many=True, read_only=True)
    primary_image = serializers.SerializerMethodField()
    images = PropertyImageSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "name",
            "city",
            "state",
            "rating",
            "property_type",
            "description",
            "primary_image",
            "images",
            "room_types",
        ]

    def get_primary_image(self, obj):
        image_obj = obj.primary_image
        if image_obj and image_obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(image_obj.image.url)
            return image_obj.image.url
        return None

