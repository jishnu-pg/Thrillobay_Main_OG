from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from apps.coupons.models import Coupon
from .serializers import CouponSerializer

class CouponListAPIView(ListAPIView):
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        today = timezone.now().date()
        return Coupon.objects.filter(valid_from__lte=today, valid_to__gte=today)
