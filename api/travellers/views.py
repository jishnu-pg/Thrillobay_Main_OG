from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.travellers.models import Traveller
from .serializers import TravellerSerializer

class TravellerViewSet(viewsets.ModelViewSet):
    serializer_class = TravellerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only travellers belonging to the current user
        return Traveller.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
