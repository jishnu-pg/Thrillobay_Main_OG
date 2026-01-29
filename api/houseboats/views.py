from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from django.db.models import Prefetch, Min
from apps.houseboats.models import HouseBoat, HouseBoatImage, HouseBoatInclusion
from .serializers import HouseBoatDetailSerializer

class HouseboatDetailAPIView(RetrieveAPIView):
    """
    Returns full details for a Houseboat detail page load.
    Lookup is performed using 'id'.
    """
    queryset = (
        HouseBoat.objects.filter(is_active=True)
        .select_related("specification", "timing", "meal_plan", "policy", "discount")
        .prefetch_related(
            Prefetch("images", queryset=HouseBoatImage.objects.all().order_by("-is_primary", "order")),
            Prefetch("inclusions", queryset=HouseBoatInclusion.objects.all()),
        )
    )
    serializer_class = HouseBoatDetailSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        obj = self.get_object()
        
        # Extract city from location "City, State"
        city = obj.location.split(",")[0].strip()

        # 1. Fetch Similar Houseboats (same city, exclude self)
        similar = (
            HouseBoat.objects.filter(location__icontains=city, is_active=True)
            .exclude(id=obj.id)
            .prefetch_related(
                Prefetch("images", queryset=HouseBoatImage.objects.filter(is_primary=True))
            )[:4]
        )
        context["similar_houseboats"] = list(similar)


        return context
