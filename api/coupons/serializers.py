from rest_framework import serializers
from apps.coupons.models import Coupon

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ["id", "code", "discount_amount", "valid_from", "valid_to"]
