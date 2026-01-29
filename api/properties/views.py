from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils.dateparse import parse_date

from django.db.models import Min, Prefetch, Q
from apps.properties.models import Property, RoomType, PropertyImage
from .serializers import (
    HotelDetailSerializer,
    RoomAvailabilitySerializer,
    HomestayDetailSerializer,
    HomestayRoomAvailabilitySerializer,
)


class HotelDetailAPIView(RetrieveAPIView):
    """
    Returns full details for a hotel including images, amenities, pricing summary, and similar hotels.
    """
    queryset = (
        Property.objects.filter(is_active=True, property_type__in=["hotel", "resort"])
        .select_related("discount")
        .annotate(min_price=Min("room_types__base_price"))
        .prefetch_related(
            Prefetch("images", queryset=PropertyImage.objects.all().order_by("-is_primary", "order")),
            "amenities",
        )
    )
    serializer_class = HotelDetailSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        obj = self.get_object()
        
        # Move similar hotels logic here to avoid serializer-level DB calls
        similar = (
            Property.objects.filter(
                city=obj.city, property_type=obj.property_type, is_active=True
            )
            .exclude(id=obj.id)
            .annotate(min_price=Min("room_types__base_price"))
            .prefetch_related(
                Prefetch("images", queryset=PropertyImage.objects.filter(is_primary=True))
            )[:4]
        )
        context["similar_hotels"] = list(similar)
        return context


class HotelRoomAvailabilityAPIView(ListAPIView):
    """
    Returns available rooms for a hotel based on dates and number of guests.
    """
    serializer_class = RoomAvailabilitySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        hotel_id = self.kwargs.get("pk")
        
        # Ensure the property is actually a hotel or resort
        if not Property.objects.filter(id=hotel_id, property_type__in=["hotel", "resort"], is_active=True).exists():
            return RoomType.objects.none()
            
        check_in = self.request.query_params.get("check_in")
        check_out = self.request.query_params.get("check_out")
        guests = self.request.query_params.get("guests")

        # Basic validation
        if not all([check_in, check_out, guests]):
            return RoomType.objects.none()

        try:
            guests = int(guests)
            d_in = parse_date(check_in)
            d_out = parse_date(check_out)
            
            if not d_in or not d_out or d_out <= d_in:
                return RoomType.objects.none()
        except (ValueError, TypeError):
            return RoomType.objects.none()

        return RoomType.objects.filter(
            property_id=hotel_id,
            max_guests__gte=guests
        )

    def list(self, request, *args, **kwargs):
        check_in = self.request.query_params.get("check_in")
        check_out = self.request.query_params.get("check_out")
        guests = self.request.query_params.get("guests")

        if not all([check_in, check_out, guests]):
            return Response(
                {"error": "check_in, check_out, and guests are required parameters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            guests = int(guests)
            d_in = parse_date(check_in)
            d_out = parse_date(check_out)
            
            if not d_in or not d_out:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            
            if d_out <= d_in:
                return Response({"error": "check_out must be after check_in."}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({"error": "Invalid guests or date parameters."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
class HomestayDetailAPIView(RetrieveAPIView):
    """
    Returns full details for a homestay/villa including images, amenities, pricing summary, and similar properties.
    """
    queryset = (
        Property.objects.filter(is_active=True, property_type__in=["homestay", "villa"])
        .select_related("discount")
        .annotate(min_price=Min("room_types__base_price"))
        .prefetch_related(
            Prefetch("images", queryset=PropertyImage.objects.all().order_by("-is_primary", "order")),
            "amenities",
            "room_types",
        )
    )
    serializer_class = HomestayDetailSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        obj = self.get_object()
        
        # Move similar properties logic here to avoid serializer-level DB calls
        similar = (
            Property.objects.filter(
                city=obj.city, property_type=obj.property_type, is_active=True
            )
            .exclude(id=obj.id)
            .annotate(min_price=Min("room_types__base_price"))
            .prefetch_related(
                Prefetch("images", queryset=PropertyImage.objects.filter(is_primary=True))
            )[:4]
        )
        context["similar_properties"] = list(similar)
        return context


class HomestayRoomAvailabilityAPIView(ListAPIView):
    """
    Returns available rooms for a homestay/villa based on dates and number of guests.
    """
    serializer_class = HomestayRoomAvailabilitySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        property_id = self.kwargs.get("pk")
        
        # Ensure the property is actually a homestay/villa
        if not Property.objects.filter(id=property_id, property_type__in=["homestay", "villa"], is_active=True).exists():
            return RoomType.objects.none()
            
        check_in = self.request.query_params.get("check_in")
        check_out = self.request.query_params.get("check_out")
        guests = self.request.query_params.get("guests")

        # Basic validation
        if not all([check_in, check_out, guests]):
            return RoomType.objects.none()

        try:
            guests = int(guests)
            d_in = parse_date(check_in)
            d_out = parse_date(check_out)
            
            if not d_in or not d_out or d_out <= d_in:
                return RoomType.objects.none()
        except (ValueError, TypeError):
            return RoomType.objects.none()

        return RoomType.objects.filter(
            property_id=property_id
        ).filter(
            Q(is_entire_place=True, max_guests__gte=guests) | 
            Q(is_entire_place=False)
        ).select_related("property", "property__discount")

    def list(self, request, *args, **kwargs):
        check_in = request.query_params.get("check_in")
        check_out = request.query_params.get("check_out")
        guests = request.query_params.get("guests")

        if not all([check_in, check_out, guests]):
            return Response(
                {"error": "check_in, check_out, and guests are required parameters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            guests_count = int(guests)
            d_in = parse_date(check_in)
            d_out = parse_date(check_out)
            
            if not d_in or not d_out:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            
            if d_out <= d_in:
                return Response({"error": "check_out must be after check_in."}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({"error": "Invalid guests or date parameters."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset()
        serializer = self.get_serializer(
            queryset, 
            many=True, 
            context={
                "request": request,
                "check_in": d_in,
                "check_out": d_out,
                "guests": guests_count
            }
        )
        return Response(serializer.data)
