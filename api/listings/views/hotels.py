from rest_framework import generics, permissions
from django.db.models import Min, Q
from apps.properties.models import Property, Amenity
from ..serializers import HotelListingSerializer
from ..filters import ListingPagination, get_price_range

class HotelListingAPIView(generics.ListAPIView):
    serializer_class = HotelListingSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ListingPagination

    def get_queryset(self):
        # Base filter for Hotels/Resorts
        queryset = Property.objects.filter(property_type__in=["hotel", "resort"], is_active=True)
        
        # Annotate min_price from RoomTypes for sorting and filtering
        queryset = queryset.annotate(min_price=Min("room_types__base_price"))

        # Filtering
        destination = self.request.query_params.get("destination")
        if destination:
            queryset = queryset.filter(Q(city__icontains=destination) | Q(state__icontains=destination))

        guests = self.request.query_params.get("guests")
        adults = self.request.query_params.get("adults")
        children = self.request.query_params.get("children")
        
        if not guests and adults:
            guests = int(adults) + int(children or 0)
            
        if guests:
            queryset = queryset.filter(room_types__max_guests__gte=guests).distinct()

        price_min = self.request.query_params.get("price_min")
        if price_min:
            queryset = queryset.filter(min_price__gte=price_min)

        price_max = self.request.query_params.get("price_max")
        if price_max:
            queryset = queryset.filter(min_price__lte=price_max)

        star_rating = self.request.query_params.get("star_rating")
        if star_rating:
            queryset = queryset.filter(star_rating=star_rating)

        user_rating = self.request.query_params.get("user_rating")
        if user_rating:
            queryset = queryset.filter(review_rating__gte=user_rating)

        amenities = self.request.query_params.getlist("amenities") or self.request.query_params.getlist("amenities[]")
        if amenities:
            queryset = queryset.filter(amenities__id__in=amenities).distinct()

        # Sorting
        sort_by = self.request.query_params.get("sort_by", "rating")
        if sort_by == "price_asc":
            queryset = queryset.order_by("min_price")
        elif sort_by == "price_desc":
            queryset = queryset.order_by("-min_price")
        else:
            queryset = queryset.order_by("-review_rating")

        return queryset.prefetch_related("room_types", "images", "amenities")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Calculate filter metadata
        price_range = get_price_range(queryset, "room_types__base_price")
        
        # Get distinct amenities for the filter sidebar
        available_amenities = Amenity.objects.filter(properties__in=queryset).distinct().values("id", "name")

        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.paginator.get_paginated_response(serializer.data, extra_data={
                "filters": {
                    "price_range": price_range,
                    "available_filters": {
                        "amenities": available_amenities,
                    }
                }
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
