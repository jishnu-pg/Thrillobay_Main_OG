from rest_framework import serializers
from apps.cabs.models import Cab, CabCategory, CabPricingOption, CabImage, CabInclusion, CabPolicy

class CabCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CabCategory
        fields = ["id", "name", "description"]

class CabPricingOptionSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="get_option_type_display", read_only=True)
    
    class Meta:
        model = CabPricingOption
        fields = ["type", "amount", "description"]

class CabImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = CabImage
        fields = ["url", "is_primary"]

    def get_url(self, obj):
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class CabDetailSerializer(serializers.ModelSerializer):
    trip = serializers.SerializerMethodField()
    cab = serializers.SerializerMethodField()
    pricing = serializers.SerializerMethodField()
    payment_options = CabPricingOptionSerializer(source="pricing_options", many=True, read_only=True)
    driver_details = serializers.SerializerMethodField()
    inclusions = serializers.SerializerMethodField()
    policies = serializers.SerializerMethodField()

    class Meta:
        model = Cab
        fields = [
            "trip", "cab", "pricing", "payment_options", 
            "driver_details", "inclusions", "policies"
        ]

    def get_trip(self, obj):
        # Taking from context if available, else placeholders
        return {
            "pickup_location": self.context.get("pickup_location", "Wayanad, Kerala"),
            "drop_location": self.context.get("drop_location", "Bangalore"),
            "trip_type": self.context.get("trip_type", "One Way"),
            "pickup_datetime": self.context.get("pickup_datetime", "2023-03-23T10:00:00")
        }

    def get_cab(self, obj):
        return {
            "id": obj.id,
            "title": obj.title,
            "category": obj.category.name if obj.category else "",
            "capacity": obj.capacity,
            "fuel_type": obj.get_fuel_type_display(),
            "is_ac": obj.is_ac,
            "luggage_capacity": f"{obj.luggage_capacity} Bags"
        }

    def get_pricing(self, obj):
        return {
            "base_fare": float(obj.base_price),
            "included_kms": obj.included_kms,
            "extra_km_price": float(obj.extra_km_fare),
            "driver_allowance": float(obj.driver_allowance) if obj.driver_allowance else 0.0,
            "tax_included": True,
            "final_price": float(obj.base_price)
        }

    def get_driver_details(self, obj):
        return {
            "note": "Driver details will be shared 30 mins prior to departure."
        }

    def get_inclusions(self, obj):
        # Using prefetched inclusions
        return [f"{inc.label}: {inc.value}" if inc.value else inc.label for inc in obj.inclusions.all()]

    def get_policies(self, obj):
        # We'll map the policies from CabPolicy model
        policies_dict = {
            "cab_category": f"{obj.category.name if obj.category else ''} ({obj.title})",
            "hilly_regions": "AC may be switched off in hilly areas",
            "luggage_policy": f"{obj.luggage_capacity} luggage bags allowed",
            "delays": "Pickup may be delayed up to 30 mins",
            "receipts": "Extra charges paid directly to driver"
        }
        
        # Override with actual CabPolicy if they exist
        for policy in obj.policies.all():
            policies_dict[policy.title.lower().replace(" ", "_")] = policy.description
            
        return policies_dict
