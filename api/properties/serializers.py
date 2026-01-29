from rest_framework import serializers
from apps.properties.models import Property, RoomType, PropertyImage, Amenity, Discount
from django.db.models import Min


class HotelImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = PropertyImage
        fields = ["image", "is_primary"]

    def get_image(self, obj):
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class AmenitySerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    class Meta:
        model = Amenity
        fields = ["id", "name", "icon"]

    def get_icon(self, obj):
        if obj.icon:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.icon.url)
            return obj.icon.url
        return None


class SimilarHotelSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    price_from = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = ["id", "name", "primary_image", "price_from", "review_rating"]

    def get_primary_image(self, obj):
        image_obj = obj.primary_image
        if image_obj and image_obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(image_obj.image.url)
            return image_obj.image.url
        return None

    def get_price_from(self, obj):
        # Use pre-annotated value from the view
        min_price = getattr(obj, "min_price", "0.00")
        return f"{min_price:.2f}" if min_price else "0.00"


class HotelDetailSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()
    pricing = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    amenities = AmenitySerializer(many=True, read_only=True)
    policies = serializers.SerializerMethodField()
    reviews_summary = serializers.SerializerMethodField()
    similar_hotels = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "name",
            "location",
            "star_rating",
            "review_rating",
            "check_in_time",
            "check_out_time",
            "description",
            "pricing",
            "images",
            "amenities",
            "policies",
            "reviews_summary",
            "similar_hotels",
            "allow_entire_place_booking",
            "entire_place_price",
            "entire_place_max_guests",
        ]

    def get_location(self, obj):
        parts = [p for p in [obj.area, obj.city, obj.state] if p]
        return ", ".join(parts)

    def get_pricing(self, obj):
        # 1. Minimum Room Price (Start From)
        min_price = getattr(obj, "min_price", None)
        room_pricing = obj.calculate_pricing(min_price) if min_price else None

        # 2. Entire Place Price (if applicable)
        entire_place_pricing = None
        if obj.allow_entire_place_booking and obj.entire_place_price:
             entire_place_pricing = obj.calculate_pricing(obj.entire_place_price)

        return {
            "min_room_price": room_pricing,
            "entire_place_price": entire_place_pricing,
            # Backward compatibility / Quick access
            "price_from": room_pricing["price_from"] if room_pricing else "0.00",
            "discount_label": room_pricing["discount_label"] if room_pricing else ""
        }

    def get_images(self, obj):
        # Use already prefetched and sorted images
        return HotelImageSerializer(obj.images.all(), many=True, context=self.context).data

    def get_policies(self, obj):
        return {
            "cancellation_policy": obj.rules if obj.rules else "",
            "house_rules": "",  # Placeholder as requested
        }

    def get_reviews_summary(self, obj):
        return {
            "average_rating": float(obj.review_rating) if obj.review_rating else 0.0,
            "total_reviews": obj.review_count,
        }

    def get_similar_hotels(self, obj):
        # Read pre-fetched data from view context
        similar = self.context.get("similar_hotels", [])
        return SimilarHotelSerializer(similar, many=True, context=self.context).data


class RoomAvailabilitySerializer(serializers.ModelSerializer):
    discounted_price = serializers.ReadOnlyField()
    gst_percent = serializers.SerializerMethodField()
    gst_amount = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField(source="total_payable_amount")
    amenities = serializers.SerializerMethodField()

    class Meta:
        model = RoomType
        fields = [
            "name",
            "base_price",
            "discounted_price",
            "gst_percent",
            "gst_amount",
            "total_price",
            "has_breakfast",
            "max_guests",
            "total_units",
            "amenities",
        ]

    def get_gst_percent(self, obj):
        return obj.property.gst_percent

    def get_amenities(self, obj):
        # Fetch shared amenities from the parent property
        amenities = obj.property.amenities.all()
        return AmenitySerializer(amenities, many=True, context=self.context).data


class HomestayImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = PropertyImage
        fields = ["image", "is_primary"]

    def get_image(self, obj):
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class SimilarHomestaySerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    price_from = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = ["id", "name", "primary_image", "price_from", "review_rating"]

    def get_primary_image(self, obj):
        image_obj = obj.primary_image
        if image_obj and image_obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(image_obj.image.url)
            return image_obj.image.url
        return None

    def get_price_from(self, obj):
        min_price = getattr(obj, "min_price", "0.00")
        return f"{min_price:.2f}" if min_price else "0.00"


class HomestayDetailSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()
    pricing = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    amenities = AmenitySerializer(many=True, read_only=True)
    policies = serializers.SerializerMethodField()
    reviews_summary = serializers.SerializerMethodField()
    similar_properties = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "name",
            "property_type",
            "location",
            "review_rating",
            "check_in_time",
            "check_out_time",
            "description",
            "pricing",
            "images",
            "amenities",
            "policies",
            "reviews_summary",
            "similar_properties",
            "allow_entire_place_booking",
            "entire_place_price",
            "entire_place_max_guests",
        ]

    def get_location(self, obj):
        parts = [p for p in [obj.area, obj.city, obj.state] if p]
        return ", ".join(parts)

    def get_pricing(self, obj):
        # 1. Minimum Room Price (Start From)
        min_price = getattr(obj, "min_price", None)
        room_pricing = obj.calculate_pricing(min_price) if min_price else None

        # 2. Entire Place Price (if applicable)
        entire_place_pricing = None
        if obj.allow_entire_place_booking and obj.entire_place_price:
             entire_place_pricing = obj.calculate_pricing(obj.entire_place_price)

        return {
            "min_room_price": room_pricing,
            "entire_place_price": entire_place_pricing,
            # Backward compatibility / Quick access
            "price_from": room_pricing["price_from"] if room_pricing else "0.00",
            "discount_label": room_pricing["discount_label"] if room_pricing else ""
        }

    def get_images(self, obj):
        # Use already prefetched and sorted images
        return HomestayImageSerializer(obj.images.all(), many=True, context=self.context).data

    def get_policies(self, obj):
        return {
            "cancellation_policy": obj.rules if obj.rules else "",
            "house_rules": "",
        }

    def get_reviews_summary(self, obj):
        return {
            "average_rating": float(obj.review_rating) if obj.review_rating else 0.0,
            "total_reviews": obj.review_count,
        }

    def get_similar_properties(self, obj):
        similar = self.context.get("similar_properties", [])
        return SimilarHomestaySerializer(similar, many=True, context=self.context).data


class HomestayRoomAvailabilitySerializer(serializers.ModelSerializer):
    total_nights = serializers.SerializerMethodField()
    base_total = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    gst = serializers.SerializerMethodField()
    final_payable_amount = serializers.SerializerMethodField()

    class Meta:
        model = RoomType
        fields = [
            "id",
            "name",
            "max_guests",
            "base_price",
            "total_nights",
            "base_total",
            "discount",
            "gst",
            "final_payable_amount",
            "is_entire_place",
        ]

    def get_total_nights(self, obj):
        check_in = self.context.get("check_in")
        check_out = self.context.get("check_out")
        if check_in and check_out:
            delta = check_out - check_in
            return max(1, delta.days)
        return 1

    def get_base_total(self, obj):
        nights = self.get_total_nights(obj)
        return f"{(obj.base_price * nights):.2f}"

    def get_discount(self, obj):
        nights = self.get_total_nights(obj)
        return f"{(obj.discount_amount * nights):.2f}"

    def get_gst(self, obj):
        nights = self.get_total_nights(obj)
        return f"{(obj.gst_amount * nights):.2f}"

    def get_final_payable_amount(self, obj):
        nights = self.get_total_nights(obj)
        return f"{(obj.total_payable_amount * nights):.2f}"
