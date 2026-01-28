from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from apps.properties.models import Property, RoomType
from .serializers import (
    PropertyListSerializer,
    PropertyDetailSerializer,
    RoomTypeSerializer,
)


class PropertyListAPIView(ListAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertyListSerializer
    permission_classes = [AllowAny]


class PropertyDetailAPIView(RetrieveAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertyDetailSerializer
    permission_classes = [AllowAny]


class PropertyRoomTypeListAPIView(ListAPIView):
    serializer_class = RoomTypeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        property_id = self.kwargs["pk"]
        return RoomType.objects.filter(property_id=property_id)

