from django.db.models import Prefetch
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.packages.models import HolidayPackage, PackageImage, PackageItinerary
from .serializers import HolidayPackageDetailSerializer


class HolidayPackageDetailAPIView(RetrieveAPIView):
    """
    Returns full details for a Holiday Package detail page load.
    Lookup is performed using 'id'.
    """
    queryset = (
        HolidayPackage.objects.filter(is_active=True)
        .select_related("discount")
        .prefetch_related(
            Prefetch("images", queryset=PackageImage.objects.all().order_by("-is_primary", "order")),
            "features",
            Prefetch("itinerary", queryset=PackageItinerary.objects.all().order_by("day_number", "order")),
            "itinerary__transfers",
            "itinerary__transfers__cab_category",
            "itinerary__stay_property",
            "itinerary__stay_houseboat",
            "itinerary__activities",
            "accommodations",
            "accommodations__property",
            "accommodations__room_type",
            "inclusions"
        )
    )
    serializer_class = HolidayPackageDetailSerializer
    permission_classes = [AllowAny]


class PackagePricingAPIView(RetrieveAPIView):
    """
    Optional Pricing Breakdown API.
    """
    queryset = HolidayPackage.objects.filter(is_active=True).select_related("discount")
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = HolidayPackageDetailSerializer(obj, context={"request": request})
        data = serializer.data
        
        return Response({
            "id": obj.id,
            "title": obj.title,
            "base_price": data["base_price"],
            "discount": data["discount"],
            "discounted_price": data["discounted_price"],
            "price_per_person": data["price_per_person"],
        })
