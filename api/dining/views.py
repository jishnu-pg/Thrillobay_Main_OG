from rest_framework import generics
from rest_framework.permissions import AllowAny
from apps.dining.models import FoodDestination
from .serializers import FoodDestinationSerializer

class FoodDestinationListView(generics.ListAPIView):
    serializer_class = FoodDestinationSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = FoodDestination.objects.filter(is_active=True)
        location = self.request.query_params.get("location")
        
        # Filter by location if provided and not "All"
        if location and location.strip().lower() not in ["", "all", "null", "undefined"]:
            queryset = queryset.filter(location__icontains=location)
            
        return queryset.order_by("-rating")

class FoodDestinationDetailView(generics.RetrieveAPIView):
    queryset = FoodDestination.objects.filter(is_active=True)
    serializer_class = FoodDestinationSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
