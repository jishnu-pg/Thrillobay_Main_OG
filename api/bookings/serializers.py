from rest_framework import serializers
from django.db import transaction
from django.db.models import Q
from apps.bookings.models import Booking, BookingItem, BookingTraveller
from apps.travellers.models import Traveller
from apps.properties.models import Property, RoomType
from apps.packages.models import HolidayPackage
from apps.activities.models import Activity
from apps.cabs.models import Cab
from apps.houseboats.models import HouseBoat

class BookingItemInputSerializer(serializers.Serializer):
    room_type_id = serializers.IntegerField(required=False)
    package_id = serializers.IntegerField(required=False)
    activity_id = serializers.IntegerField(required=False)
    cab_id = serializers.IntegerField(required=False)
    houseboat_id = serializers.IntegerField(required=False)
    
    quantity = serializers.IntegerField(min_value=1, default=1)
    adults = serializers.IntegerField(min_value=1)
    children = serializers.IntegerField(min_value=0, default=0)

class BookingCreateSerializer(serializers.ModelSerializer):
    booking_type = serializers.ChoiceField(choices=Booking.BOOKING_TYPE, default="stay")
    property_id = serializers.IntegerField(write_only=True, required=False)
    items = BookingItemInputSerializer(many=True, write_only=True)
    check_in = serializers.DateField(write_only=True)
    check_out = serializers.DateField(write_only=True)
    
    class Meta:
        model = Booking
        fields = [
            "id", 
            "booking_type", 
            "total_amount", 
            "amount_paid", 
            "status", 
            "created_at",
            "property_id",
            "items",
            "check_in",
            "check_out"
        ]
        read_only_fields = ["id", "total_amount", "amount_paid", "status", "created_at"]

    def validate(self, attrs):
        check_in = attrs.get("check_in")
        check_out = attrs.get("check_out")
        booking_type = attrs.get("booking_type", "stay")
        items_data = attrs.get("items")
        
        # Validation for dates based on booking type
        if booking_type == "stay":
            if check_in >= check_out:
                raise serializers.ValidationError("Check-out date must be after check-in date for stays.")
        else:
            if check_in > check_out:
                raise serializers.ValidationError("Check-out date cannot be before check-in date.")

        total_price = 0
        nights = (check_out - check_in).days
        if nights < 1:
            nights = 1 # Logic for day activities or cabs if same day

        # STAY BOOKING VALIDATION
        if booking_type == "stay":
            property_id = attrs.get("property_id")
            if not property_id:
                raise serializers.ValidationError({"property_id": "This field is required for stay bookings."})
            
            try:
                property_obj = Property.objects.get(id=property_id, is_active=True)
            except Property.DoesNotExist:
                raise serializers.ValidationError("Property not found or inactive.")
            
            attrs["property_obj"] = property_obj
            
            for item in items_data:
                room_type_id = item.get("room_type_id")
                if not room_type_id:
                    raise serializers.ValidationError("room_type_id is required for stay bookings.")
                
                quantity = item["quantity"]
                
                try:
                    room_type = RoomType.objects.get(id=room_type_id, property=property_obj)
                except RoomType.DoesNotExist:
                    raise serializers.ValidationError(f"RoomType {room_type_id} does not belong to this property.")
                
                item["room_type_obj"] = room_type

                # Validate Guest Capacity
                adults = item["adults"]
                children = item["children"]
                total_guests = adults + children
                
                if total_guests > room_type.max_guests:
                     raise serializers.ValidationError(f"Guest count ({total_guests}) exceeds maximum capacity ({room_type.max_guests}) for '{room_type.name}'.")

                # Check logic: Entire Place vs Single Room
                if room_type.is_entire_place:
                    if quantity > 1:
                        raise serializers.ValidationError(f"Cannot book more than 1 unit of Entire Place '{room_type.name}'.")
                    
                    # STRICT CHECK: If booking entire place, NO other bookings should exist for this property in this date range
                    overlapping_bookings = BookingItem.objects.filter(
                        property=property_obj,
                        check_in__lt=check_out,
                        check_out__gt=check_in
                    ).exclude(booking__status="cancelled")
                    
                    if overlapping_bookings.exists():
                        raise serializers.ValidationError(f"Property '{property_obj.name}' is already booked for these dates.")
                
                # Pricing: Room Rate * Nights * Quantity
                price_per_night = room_type.total_payable_amount
                item_total = price_per_night * nights * quantity
                total_price += item_total

        # PACKAGE BOOKING VALIDATION
        elif booking_type == "package":
            for item in items_data:
                package_id = item.get("package_id")
                if not package_id:
                    raise serializers.ValidationError("package_id is required for package bookings.")
                
                try:
                    package = HolidayPackage.objects.get(id=package_id, is_active=True)
                except HolidayPackage.DoesNotExist:
                    raise serializers.ValidationError(f"HolidayPackage {package_id} not found.")
                
                item["package_obj"] = package
                
                adults = item["adults"]
                children = item["children"]
                total_pax = adults + children
                
                # Pricing: (Base Price - Discount) * Pax
                price_per_person = package.base_price
                if package.discount and package.discount.is_active:
                     if package.discount.discount_type == "percentage":
                         price_per_person = price_per_person - (price_per_person * package.discount.value / 100)
                     else:
                         price_per_person = price_per_person - package.discount.value
                
                item_total = price_per_person * total_pax
                total_price += item_total

        # ACTIVITY BOOKING VALIDATION
        elif booking_type == "activity":
            for item in items_data:
                activity_id = item.get("activity_id")
                if not activity_id:
                    raise serializers.ValidationError("activity_id is required for activity bookings.")
                
                try:
                    activity = Activity.objects.get(id=activity_id, is_active=True)
                except Activity.DoesNotExist:
                    raise serializers.ValidationError(f"Activity {activity_id} not found.")
                
                item["activity_obj"] = activity
                
                adults = item["adults"]
                children = item["children"]
                total_pax = adults + children
                
                # Pricing logic from Activity model
                pricing = activity.calculate_pricing()
                price_per_person = pricing["discounted_price"]
                
                # Convert float price to Decimal
                price_decimal = serializers.DecimalField(max_digits=12, decimal_places=2).to_internal_value(str(price_per_person))
                
                item_total = price_decimal * total_pax
                total_price += item_total

        # CAB BOOKING VALIDATION
        elif booking_type == "cab":
            for item in items_data:
                cab_id = item.get("cab_id")
                if not cab_id:
                    raise serializers.ValidationError("cab_id is required for cab bookings.")
                
                try:
                    cab = Cab.objects.get(id=cab_id, is_active=True)
                except Cab.DoesNotExist:
                    raise serializers.ValidationError(f"Cab {cab_id} not found.")
                
                item["cab_obj"] = cab
                quantity = item["quantity"]
                
                # Pricing: Base Price * Quantity * Days (Nights)
                price_per_day = cab.base_price
                item_total = price_per_day * quantity * nights
                total_price += item_total
        
        # HOUSEBOAT BOOKING VALIDATION
        elif booking_type == "houseboat":
            for item in items_data:
                houseboat_id = item.get("houseboat_id")
                if not houseboat_id:
                    raise serializers.ValidationError("houseboat_id is required for houseboat bookings.")
                
                try:
                    houseboat = HouseBoat.objects.get(id=houseboat_id, is_active=True)
                except HouseBoat.DoesNotExist:
                    raise serializers.ValidationError(f"HouseBoat {houseboat_id} not found.")
                
                item["houseboat_obj"] = houseboat
                quantity = item["quantity"]
                
                # Pricing: (Discounted Price) * Quantity * Nights
                pricing = houseboat.calculate_pricing()
                price = pricing["discounted_price"]
                
                # Convert float price to Decimal
                price_decimal = serializers.DecimalField(max_digits=12, decimal_places=2).to_internal_value(str(price))
                
                item_total = price_decimal * quantity * nights
                total_price += item_total

        attrs["total_price"] = total_price
        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        booking_type = validated_data.get("booking_type", "stay")
        
        # Extract fields not belonging to Booking model
        check_in = validated_data.pop("check_in", None)
        check_out = validated_data.pop("check_out", None)
        property_id = validated_data.pop("property_id", None)
        
        # Remove helper objects from validated_data
        property_obj = validated_data.pop("property_obj", None)
        validated_data.pop("package_obj", None)
        validated_data.pop("activity_obj", None)
        validated_data.pop("cab_obj", None)
        validated_data.pop("houseboat_obj", None)
        
        total_amount = validated_data.pop("total_price", 0)

        with transaction.atomic():
            status = validated_data.pop("status", "pending")
            
            booking = Booking.objects.create(
                user=self.context["request"].user,
                total_amount=total_amount,
                amount_paid=0, # Initial booking is unpaid
                status=status,
                **validated_data
            )
            
            for item in items_data:
                common_data = {
                    "booking": booking,
                    "check_in": check_in,
                    "check_out": check_out,
                    "adults": item["adults"],
                    "children": item["children"]
                }
                
                if booking_type == "stay":
                    room_type = item["room_type_obj"]
                    for _ in range(item["quantity"]):
                        BookingItem.objects.create(
                            property=property_obj,
                            room_type=room_type,
                            **common_data
                        )
                
                elif booking_type == "package":
                    package = item["package_obj"]
                    for _ in range(item["quantity"]):
                        BookingItem.objects.create(
                            package=package,
                            **common_data
                        )
                        
                elif booking_type == "activity":
                    activity = item["activity_obj"]
                    for _ in range(item["quantity"]):
                        BookingItem.objects.create(
                            activity=activity,
                            **common_data
                        )
                        
                elif booking_type == "cab":
                    cab = item["cab_obj"]
                    for _ in range(item["quantity"]):
                        BookingItem.objects.create(
                            cab=cab,
                            **common_data
                        )

                elif booking_type == "houseboat":
                    houseboat = item["houseboat_obj"]
                    for _ in range(item["quantity"]):
                        BookingItem.objects.create(
                            houseboat=houseboat,
                            **common_data
                        )
        
        return booking

class BookingItemSerializer(serializers.ModelSerializer):
    # Stay fields
    room_type_name = serializers.CharField(source="room_type.name", read_only=True)
    property_name = serializers.CharField(source="property.name", read_only=True)
    property_location = serializers.SerializerMethodField()
    
    # Package fields
    package_title = serializers.CharField(source="package.title", read_only=True)
    package_location = serializers.CharField(source="package.primary_location", read_only=True)
    
    # Activity fields
    activity_title = serializers.CharField(source="activity.title", read_only=True)
    activity_location = serializers.CharField(source="activity.location", read_only=True)
    
    # Cab fields
    cab_title = serializers.CharField(source="cab.title", read_only=True)
    cab_category = serializers.CharField(source="cab.category.name", read_only=True)
    
    # Houseboat fields
    houseboat_name = serializers.CharField(source="houseboat.name", read_only=True)
    houseboat_location = serializers.CharField(source="houseboat.location", read_only=True)
    
    # Generic Image
    item_image = serializers.SerializerMethodField()
    # Deprecated: alias to item_image for backward compatibility
    property_image = serializers.SerializerMethodField()

    rating = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()
    amenities = serializers.SerializerMethodField()

    class Meta:
        model = BookingItem
        fields = [
            "id",
            # Stay
            "property_name", "property_location", "room_type_name",
            # Package
            "package_title", "package_location",
            # Activity
            "activity_title", "activity_location",
            # Cab
            "cab_title", "cab_category",
            # Houseboat
            "houseboat_name", "houseboat_location",
            
            "check_in", "check_out", "adults", "children",
            "item_image", "property_image",
            "rating", "category_display", "amenities"
        ]

    def get_amenities(self, obj):
        if obj.property:
            return [{"name": a.name, "icon": a.icon.url if a.icon else None} for a in obj.property.amenities.all()]
        # Can extend for other types if they have amenities
        return []

    def get_rating(self, obj):
        if obj.property:
            return obj.property.star_rating or obj.property.review_rating
        elif obj.package:
            return obj.package.rating
        elif obj.activity:
            return obj.activity.rating
        elif obj.houseboat:
            return obj.houseboat.rating
        return None

    def get_category_display(self, obj):
        if obj.property:
             return obj.property.get_property_type_display()
        elif obj.package:
             return "Holiday Package"
        elif obj.activity:
             return "Activity"
        elif obj.cab:
             return "Cab Service"
        elif obj.houseboat:
             return "Houseboat"
        return "Booking"

    def get_property_location(self, obj):
        if obj.property:
            return f"{obj.property.city}, {obj.property.state}"
        return ""

    def get_property_image(self, obj):
        return self.get_item_image(obj)

    def get_item_image(self, obj):
        image_obj = None
        
        if obj.property:
            # Property model has primary_image property
            image_obj = obj.property.primary_image
        elif obj.package:
            image_obj = obj.package.images.filter(is_primary=True).first() or obj.package.images.first()
        elif obj.activity:
            image_obj = obj.activity.images.filter(is_primary=True).first() or obj.activity.images.first()
        elif obj.cab:
            image_obj = obj.cab.images.filter(is_primary=True).first() or obj.cab.images.first()
        elif obj.houseboat:
            image_obj = obj.houseboat.images.filter(is_primary=True).first() or obj.houseboat.images.first()
            
        if image_obj and image_obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(image_obj.image.url)
            return image_obj.image.url
        return None

class BookingListSerializer(serializers.ModelSerializer):
    items = BookingItemSerializer(many=True, read_only=True)
    booking_date = serializers.DateTimeField(source="created_at", format="%Y-%m-%d")
    refund_status_display = serializers.CharField(source="get_refund_status_display", read_only=True)
    formatted_id = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "formatted_id",
            "booking_type",
            "status",
            "refund_status",
            "refund_status_display",
            "cancelled_at",
            "total_amount",
            "amount_paid",
            "booking_date",
            "items"
        ]

    def get_formatted_id(self, obj):
        return f"#{obj.id}"

class BookingDetailSerializer(serializers.ModelSerializer):
    items = BookingItemSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_phone = serializers.CharField(source="user.phone", read_only=True)
    booking_date = serializers.DateTimeField(source="created_at", format="%d %b %Y, %I:%M %p")
    formatted_id = serializers.SerializerMethodField()
    cancellation_policy = serializers.SerializerMethodField()
    rules = serializers.SerializerMethodField()
    refund_status_display = serializers.CharField(source="get_refund_status_display", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "formatted_id",
            "booking_type",
            "status",
            "refund_status",
            "refund_status_display",
            "cancelled_at",
            "total_amount",
            "amount_paid",
            "pricing_breakdown",
            "cancellation_policy",
            "rules",
            "booking_date",
            
            # Contact Info
            "title", "full_name", "email", "phone", "country_code",
            "special_requests",
            
            # User Account Info
            "user_name",
            "user_phone",
            "items"
        ]

    def get_formatted_id(self, obj):
        return f"#{obj.id}"

    def get_cancellation_policy(self, obj):
        # Attempt to get policy from the first item (primary service)
        first_item = obj.items.first()
        if first_item:
            if first_item.property:
                return first_item.property.cancellation_policy
            elif first_item.package:
                return getattr(first_item.package, "cancellation_policy", None)
            elif first_item.activity:
                return getattr(first_item.activity, "cancellation_policy", None)
            elif first_item.cab:
                return getattr(first_item.cab, "cancellation_policy", None)
            elif first_item.houseboat:
                return getattr(first_item.houseboat, "cancellation_policy", None)
        return None

    def get_rules(self, obj):
        # Attempt to get rules from the first item (primary service)
        first_item = obj.items.first()
        if first_item:
            if first_item.property:
                return first_item.property.rules
            # Can extend for other types if they have rules
        return None

class BookingTravellerInputSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    gender = serializers.CharField(max_length=10)
    is_primary = serializers.BooleanField(default=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)

class BookingConfirmSerializer(serializers.ModelSerializer):
    travellers = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Traveller.objects.all(),
        required=False
    )
    
    class Meta:
        model = Booking
        fields = [
            "title", "full_name", "email", "phone", "country_code",
            "special_requests", 
            "is_gst_required", "gst_number", "company_name", "company_address",
            "travellers", 
            "status"
        ]
        read_only_fields = ["status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, "user"):
            self.fields['travellers'].child_relation.queryset = Traveller.objects.filter(user=request.user)

    def update(self, instance, validated_data):
        travellers = validated_data.pop("travellers", [])
        
        # Update standard fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        with transaction.atomic():
            # Clear existing travellers if any (optional, but safer for updates)
            BookingTraveller.objects.filter(booking=instance).delete()

            # Link travellers
            for traveller in travellers:
                BookingTraveller.objects.create(
                    booking=instance,
                    traveller=traveller,
                    is_primary=False # We rely on Booking contact info for primary contact
                )
            
            instance.status = 'confirmed' 
            instance.save()
        return instance
