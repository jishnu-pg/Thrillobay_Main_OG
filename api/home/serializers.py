from rest_framework import serializers
from apps.properties.models import Property
from apps.packages.models import HolidayPackage
from apps.houseboats.models import HouseBoat
from apps.activities.models import Activity
from apps.cabs.models import Cab
from decimal import Decimal

class HomePropertyCardSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for home page property cards (Hotels, Resorts, Homestays, Villas).
    """
    rating = serializers.DecimalField(source="review_rating", max_digits=3, decimal_places=1)
    rating_count = serializers.IntegerField(source="review_count")
    price_from = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "name",
            "city",
            "state",
            "rating",
            "rating_count",
            "price_from",
            "primary_image",
            "property_type",
        ]

    def get_price_from(self, obj):
        """
        Returns the lowest base_price from related RoomTypes.
        Uses prefetch lookup to avoid additional queries.
        """
        room_types = obj.room_types.all()
        if room_types:
            return min(rt.base_price for rt in room_types)
        return None

    def get_primary_image(self, obj):
        image_obj = obj.primary_image
        if image_obj and image_obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(image_obj.image.url)
            return image_obj.image.url
        return None

class HomeHolidayPackageSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for holiday package cards on the home page.
    """
    price = serializers.DecimalField(source="base_price", max_digits=12, decimal_places=2)
    discounted_price = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = HolidayPackage
        fields = [
            "id",
            "title",
            "duration_days",
            "duration_nights",
            "primary_location",
            "price",
            "discounted_price",
            "rating",
            "review_count",
            "primary_image",
        ]

    def get_discounted_price(self, obj):
        """
        Calculates the discounted price based on the package's discount.
        """
        discount_obj = obj.discount
        if not discount_obj or not discount_obj.is_active:
            return obj.base_price
        
        if discount_obj.discount_type == "percentage":
            discount_amount = (obj.base_price * discount_obj.value / Decimal("100.00"))
            return (obj.base_price - discount_amount).quantize(Decimal("0.01"))
        
        # Flat amount discount
        return max(Decimal("0.00"), obj.base_price - discount_obj.value)

    def get_primary_image(self, obj):
        """
        Returns the absolute URL of the primary image or fallback to the first image.
        Uses manual lookup for simplicity and absolute URL requirement.
        """
        image_obj = obj.images.filter(is_primary=True).first() or obj.images.first()
        if image_obj and image_obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(image_obj.image.url)
            return image_obj.image.url
        return None

class HomePageHouseboatSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for houseboat cards on the home page.
    """
    bedrooms = serializers.IntegerField(source="specification.bedrooms", read_only=True)
    trip_type = serializers.SerializerMethodField()
    base_price = serializers.DecimalField(source="base_price_per_night", max_digits=12, decimal_places=2)
    discounted_price = serializers.SerializerMethodField()
    rating = serializers.DecimalField(max_digits=3, decimal_places=1)
    rating_count = serializers.IntegerField(source="review_count")
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = HouseBoat
        fields = [
            "id",
            "name",
            "bedrooms",
            "trip_type",
            "base_price",
            "discounted_price",
            "rating",
            "rating_count",
            "primary_image",
        ]

    def get_trip_type(self, obj):
        """
        Maps cruise_type to human-friendly display.
        """
        if hasattr(obj, "specification"):
            if obj.specification.cruise_type == "overnight_cruise":
                return "Day & Night"
            return "Day"
        return "N/A"

    def get_discounted_price(self, obj):
        """
        Calculates the discounted price based on the houseboat's discount.
        """
        discount_obj = obj.discount
        if not discount_obj or not discount_obj.is_active:
            return obj.base_price_per_night
        
        if discount_obj.discount_type == "percentage":
            discount_amount = (obj.base_price_per_night * discount_obj.value / Decimal("100.00"))
            return (obj.base_price_per_night - discount_amount).quantize(Decimal("0.01"))
        
        return max(Decimal("0.00"), obj.base_price_per_night - discount_obj.value)

    def get_primary_image(self, obj):
        """
        Returns the absolute URL of the primary image or fallback.
        """
        image_obj = obj.images.filter(is_primary=True).first() or obj.images.first()
        if image_obj and image_obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(image_obj.image.url)
            return image_obj.image.url
        return None

class HomePageActivitySerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for activity cards on the home page.
    """
    duration_label = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    rating_count = serializers.IntegerField(source="review_count")

    class Meta:
        model = Activity
        fields = [
            "id",
            "title",
            "location",
            "duration_label",
            "base_price",
            "discounted_price",
            "rating",
            "rating_count",
            "primary_image",
        ]

    def get_duration_label(self, obj):
        """
        Maps duration to a human-readable label.
        Since the model uses days/nights, we'll format accordingly.
        """
        days = obj.duration_days
        nights = obj.duration_nights
        
        if days > 0 and nights > 0:
            return f"{days}D / {nights}N"
        elif days > 0:
            # For 1-day activities, it's usually a few hours or a full day.
            # We use "Day" as a fallback since specific hours aren't stored in the schema.
            return f"{days} Day" if days == 1 else f"{days} Days"
        return "N/A"

    def get_discounted_price(self, obj):
        """
        Calculates price after applying the property/activity level discount.
        """
        discount_obj = obj.discount
        if not discount_obj or not discount_obj.is_active:
            return obj.base_price
        
        if discount_obj.discount_type == "percentage":
            discount_amount = (obj.base_price * discount_obj.value / Decimal("100.00"))
            return (obj.base_price - discount_amount).quantize(Decimal("0.01"))
        
        return max(Decimal("0.00"), obj.base_price - discount_obj.value)

    def get_primary_image(self, obj):
        """
        Absolute URL for the primary image.
        """
        image_obj = obj.images.filter(is_primary=True).first() or obj.images.first()
        if image_obj and image_obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(image_obj.image.url)
            return image_obj.image.url
        return None

# --- SEARCH SERIALIZERS (OPTIMIZED FOR LIST PAGES) ---

class SearchHotelSerializer(serializers.ModelSerializer):
    """
    Serializer for Hotel/Homestay search results.
    """
    location = serializers.SerializerMethodField()
    price_from = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    rating = serializers.DecimalField(source="review_rating", max_digits=3, decimal_places=1)

    class Meta:
        model = Property
        fields = ["id", "name", "location", "price_from", "rating", "primary_image", "property_type"]

    def get_location(self, obj):
        return f"{obj.city}, {obj.state}"

    def get_price_from(self, obj):
        room_types = obj.room_types.all()
        if room_types:
            return min(rt.base_price for rt in room_types)
        return None

    def get_primary_image(self, obj):
        image_obj = obj.primary_image
        if image_obj and image_obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(image_obj.image.url)
            return image_obj.image.url
        return None

class SearchPackageSerializer(serializers.ModelSerializer):
    """
    Serializer for Holiday Package search results.
    """
    location = serializers.CharField(source="primary_location")
    price = serializers.DecimalField(source="base_price", max_digits=12, decimal_places=2)
    discounted_price = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = HolidayPackage
        fields = [
            "id", "title", "location", "duration_days", "duration_nights", 
            "price", "discounted_price", "rating", "primary_image"
        ]

    def get_discounted_price(self, obj):
        discount_obj = obj.discount
        if not discount_obj or not discount_obj.is_active:
            return obj.base_price
        if discount_obj.discount_type == "percentage":
            return (obj.base_price * (1 - discount_obj.value / Decimal("100.00"))).quantize(Decimal("0.01"))
        return max(Decimal("0.00"), obj.base_price - discount_obj.value)

    def get_primary_image(self, obj):
        image_obj = obj.images.filter(is_primary=True).first() or obj.images.first()
        if image_obj and image_obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(image_obj.image.url)
            return image_obj.image.url
        return None

class SearchHouseboatSerializer(serializers.ModelSerializer):
    """
    Serializer for Houseboat search results.
    """
    bedrooms = serializers.IntegerField(source="specification.bedrooms", read_only=True)
    price_from = serializers.DecimalField(source="base_price_per_night", max_digits=12, decimal_places=2)
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = HouseBoat
        fields = ["id", "name", "location", "bedrooms", "price_from", "rating", "primary_image"]

    def get_primary_image(self, obj):
        image_obj = obj.images.filter(is_primary=True).first() or obj.images.first()
        if image_obj and image_obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(image_obj.image.url)
            return image_obj.image.url
        return None

class SearchActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for Activity search results.
    """
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = ["id", "title", "location", "base_price", "rating", "primary_image"]

    def get_primary_image(self, obj):
        image_obj = obj.images.filter(is_primary=True).first() or obj.images.first()
        if image_obj and image_obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(image_obj.image.url)
            return image_obj.image.url
        return None

class SearchCabSerializer(serializers.ModelSerializer):
    """
    Serializer for Cab search results.
    """
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Cab
        fields = ["id", "title", "capacity", "base_price", "fuel_type", "primary_image"]

    def get_primary_image(self, obj):
        image_obj = obj.images.filter(is_primary=True).first() or obj.images.first()
        if image_obj and image_obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(image_obj.image.url)
            return image_obj.image.url
        return None
