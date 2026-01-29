from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from apps.cabs.models import Cab
from .serializers import CabDetailSerializer

class CabDetailAPIView(RetrieveAPIView):
    """
    Returns full details for a Cab detail page load.
    Lookup is performed using 'id'.
    """
    queryset = (
        Cab.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related(
            "pricing_options", 
            "images", 
            "inclusions", 
            "policies"
        )
    )
    serializer_class = CabDetailSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # In a real app, these would come from request.query_params or session
        # for the specific booking context. Here we pass them for the mock trip info.
        context.update({
            "pickup_location": self.request.query_params.get("pickup", "Wayanad, Kerala"),
            "drop_location": self.request.query_params.get("drop", "Bangalore"),
            "trip_type": self.request.query_params.get("trip_type", "One Way"),
            "pickup_datetime": self.request.query_params.get("pickup_at", "2023-03-23T10:00:00")
        })
        return context
