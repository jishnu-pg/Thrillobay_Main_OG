from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from apps.properties.models import Property
from apps.packages.models import HolidayPackage
from apps.houseboats.models import HouseBoat
from apps.activities.models import Activity
from apps.cabs.models import Cab
from .serializers import (
    HomePropertyCardSerializer, 
    HomeHolidayPackageSerializer,
    HomePageHouseboatSerializer,
    HomePageActivitySerializer,
    SearchHotelSerializer,
    SearchPackageSerializer,
    SearchHouseboatSerializer,
    SearchActivitySerializer,
    SearchCabSerializer
)

class GlobalSearchAPIView(APIView):
    """
    Unified Search API that routes internally based on search 'type'.
    Supports: hotel, homestay, package, houseboat, activity, cab.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        search_type = request.query_params.get("type")
        
        if not search_type:
            return Response(
                {"error": "Query parameter 'type' is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Common Validation: Date check for stay-based searches
        if search_type in ["hotel", "homestay", "houseboat"]:
            check_in = request.query_params.get("check_in")
            check_out = request.query_params.get("check_out")
            if check_in and check_out and check_in >= check_out:
                return Response(
                    {"error": "Check-out date must be after check-in date."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        if search_type == "hotel":
            return self.search_hotels(request)
        elif search_type == "homestay":
            return self.search_homestays(request)
        elif search_type == "package":
            return self.search_packages(request)
        elif search_type == "houseboat":
            return self.search_houseboats(request)
        elif search_type == "activity":
            return self.search_activities(request)
        elif search_type == "cab":
            return self.search_cabs(request)
        
        return Response(
            {"error": f"Invalid search type: {search_type}"}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    def search_hotels(self, request):
        destination = request.query_params.get("destination")
        guests = request.query_params.get("guests")
        
        queryset = Property.objects.filter(property_type__in=["hotel", "resort"], is_active=True)
        if destination:
            queryset = queryset.filter(Q(city__icontains=destination) | Q(state__icontains=destination))
        if guests:
            # Filter properties that have at least one room type accommodating the required guests
            queryset = queryset.filter(room_types__max_guests__gte=guests).distinct()
        
        queryset = queryset.prefetch_related("room_types", "images").order_by("-review_rating")
        serializer = SearchHotelSerializer(queryset, many=True, context={"request": request})
        return Response({
            "type": "hotel",
            "results": serializer.data,
            "meta": {"total": queryset.count()}
        })

    def search_homestays(self, request):
        destination = request.query_params.get("destination")
        guests = request.query_params.get("guests")
        
        queryset = Property.objects.filter(property_type__in=["homestay", "villa"], is_active=True)
        if destination:
            queryset = queryset.filter(Q(city__icontains=destination) | Q(state__icontains=destination))
        if guests:
            queryset = queryset.filter(room_types__max_guests__gte=guests).distinct()
        
        queryset = queryset.prefetch_related("room_types", "images").order_by("-review_rating")
        serializer = SearchHotelSerializer(queryset, many=True, context={"request": request})
        return Response({
            "type": "homestay",
            "results": serializer.data,
            "meta": {"total": queryset.count()}
        })

    def search_packages(self, request):
        destination = request.query_params.get("destination")
        price_min = request.query_params.get("price_min")
        price_max = request.query_params.get("price_max")
        duration = request.query_params.get("duration_days")
        
        queryset = HolidayPackage.objects.filter(is_active=True)
        if destination:
            queryset = queryset.filter(primary_location__icontains=destination)
        if price_min:
            queryset = queryset.filter(base_price__gte=price_min)
        if price_max:
            queryset = queryset.filter(base_price__lte=price_max)
        if duration:
            queryset = queryset.filter(duration_days=duration)
            
        queryset = queryset.select_related("discount").prefetch_related("images").order_by("-rating")
        serializer = SearchPackageSerializer(queryset, many=True, context={"request": request})
        return Response({
            "type": "package",
            "results": serializer.data,
            "meta": {"total": queryset.count()}
        })

    def search_houseboats(self, request):
        destination = request.query_params.get("destination")
        bedrooms = request.query_params.get("bedrooms")
        guests = request.query_params.get("guests")
        
        queryset = HouseBoat.objects.filter(is_active=True)
        if destination:
            queryset = queryset.filter(location__icontains=destination)
        if bedrooms:
            queryset = queryset.filter(specification__bedrooms=bedrooms)
        if guests:
            queryset = queryset.filter(specification__max_guests__gte=guests)
            
        queryset = queryset.select_related("specification", "discount").prefetch_related("images").order_by("-rating")
        serializer = SearchHouseboatSerializer(queryset, many=True, context={"request": request})
        return Response({
            "type": "houseboat",
            "results": serializer.data,
            "meta": {"total": queryset.count()}
        })

    def search_activities(self, request):
        location = request.query_params.get("location") or request.query_params.get("destination")
        difficulty = request.query_params.get("difficulty")
        duration = request.query_params.get("duration") # days
        
        queryset = Activity.objects.filter(is_active=True)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        if duration:
             queryset = queryset.filter(duration_days=duration)
            
        queryset = queryset.select_related("discount").prefetch_related("images").order_by("-rating")
        serializer = SearchActivitySerializer(queryset, many=True, context={"request": request})
        return Response({
            "type": "activity",
            "results": serializer.data,
            "meta": {"total": queryset.count()}
        })

    def search_cabs(self, request):
        pickup = request.query_params.get("pickup_location")
        drop = request.query_params.get("drop_location")
        capacity = request.query_params.get("capacity")
        
        if pickup and drop and pickup.lower() == drop.lower():
            return Response(
                {"error": "Pickup and drop locations cannot be the same."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        queryset = Cab.objects.filter(is_active=True)
        if capacity:
            queryset = queryset.filter(capacity__gte=capacity)
            
        queryset = queryset.select_related("category").prefetch_related("images").order_by("base_price")
        serializer = SearchCabSerializer(queryset, many=True, context={"request": request})
        return Response({
            "type": "cab",
            "results": serializer.data,
            "meta": {"total": queryset.count()}
        })

class PopularHotelsAPIView(generics.ListAPIView):
    """
    API view to return the top 8 popular Hotels & Resorts for the home page.
    Optimized with prefetch_related to prevent N+1 queries.
    """
    serializer_class = HomePropertyCardSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Property.objects.filter(
            property_type__in=["hotel", "resort"],
            is_active=True
        ).prefetch_related(
            "room_types", 
            "images"
        ).order_by("-review_rating")[:8]

class PopularHomestaysAPIView(generics.ListAPIView):
    """
    API view to return the top 8 popular Homestays & Villas for the home page.
    Unauthenticated and optimized for performance.
    """
    serializer_class = HomePropertyCardSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Property.objects.filter(
            property_type__in=["homestay", "villa"],
            is_active=True
        ).prefetch_related(
            "room_types", 
            "images"
        ).order_by("-review_rating")[:8]

class PopularHolidayPackagesAPIView(generics.ListAPIView):
    """
    API view to return the top 8 popular Holiday Packages for the home page.
    Optimized with prefetch_related for images and discount linkage.
    """
    serializer_class = HomeHolidayPackageSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return HolidayPackage.objects.filter(
            is_active=True
        ).select_related(
            "discount"
        ).prefetch_related(
            "images"
        ).order_by("-rating")[:8]

class PopularHouseboatsAPIView(generics.ListAPIView):
    """
    API view to return the top 8 popular Houseboats for the home page.
    Optimized with select_related for specifications and prefetch_related for images.
    """
    serializer_class = HomePageHouseboatSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return HouseBoat.objects.filter(
            is_active=True
        ).select_related(
            "specification",
            "discount"
        ).prefetch_related(
            "images"
        ).order_by("-rating", "-created_at")[:8]

class PopularActivitiesAPIView(generics.ListAPIView):
    """
    API view to return the top 8 popular Activities for the home page.
    Unauthenticated and optimized for performance.
    """
    serializer_class = HomePageActivitySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Activity.objects.filter(
            is_active=True
        ).select_related(
            "discount"
        ).prefetch_related(
            "images"
        ).order_by("-rating", "-created_at")[:8]
