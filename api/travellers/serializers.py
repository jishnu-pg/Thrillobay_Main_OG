from rest_framework import serializers
from apps.travellers.models import Traveller

class TravellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Traveller
        fields = [
            'id', 'first_name', 'last_name', 'gender', 'dob',
            'country', 'state', 'city', 'pincode',
            'passport_number', 'passport_expiry', 'passport_issuing_country', 'passport_copy',
            'email', 'phone',
            'frequent_flyer_airline', 'frequent_flyer_number',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        # Ensure the user is attached to the traveller
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)
