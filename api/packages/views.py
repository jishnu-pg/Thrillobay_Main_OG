from rest_framework import generics
from rest_framework.permissions import AllowAny
from apps.packages.models import HolidayPackage
from .serializers import HolidayPackageDetailSerializer

class HolidayPackageDetailView(generics.RetrieveAPIView):
    """
    Returns full details of a single Holiday Package optimized for detail page rendering.
    Lookup is performed using the 'slug' field.
    """
    queryset = HolidayPackage.objects.filter(is_active=True).select_related(
        "discount"
    ).prefetch_related(
        "images",
        "features",
        "itinerary",
        "itinerary__stay_property",
        "accommodations",
        "accommodations__property",
        "accommodations__room_type",
        "activities",
        "transfers",
        "inclusions"
    )
    serializer_class = HolidayPackageDetailSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]
