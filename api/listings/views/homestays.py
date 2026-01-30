from rest_framework import generics, permissions
from django.db.models import Min, Q, Count
from apps.properties.models import Property, Amenity
from ..serializers import HotelListingSerializer
from ..filters import ListingPagination, get_price_range, unique_by_id

class HomestayListingAPIView(generics.ListAPIView):
    serializer_class = HotelListingSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ListingPagination

    def get_queryset(self):
        # Base filter for Homestays/Villas/Apartments
        queryset = Property.objects.filter(property_type__in=["homestay", "villa", "apartment"], is_active=True)
        
        # Annotate min_price from RoomTypes for sorting and filtering
        queryset = queryset.annotate(min_price=Min("room_types__base_price"))

        # Filtering
        destination = self.request.query_params.get("destination")
        if destination:
            queryset = queryset.filter(Q(city__icontains=destination) | Q(state__icontains=destination))

        # Locations filter (city)
        locations = self.request.query_params.getlist("locations") or self.request.query_params.getlist("locations[]")
        if locations:
            queryset = queryset.filter(city__in=locations)

        # Property Type filter
        property_types = self.request.query_params.getlist("property_type") or self.request.query_params.getlist("property_type[]")
        if property_types:
            queryset = queryset.filter(property_type__in=property_types)

        # Star Rating filter (support multiple)
        star_ratings = self.request.query_params.getlist("star_rating") or self.request.query_params.getlist("star_rating[]")
        if star_ratings:
            queryset = queryset.filter(star_rating__in=star_ratings)

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

        user_rating = self.request.query_params.get("user_rating")
        if user_rating:
            queryset = queryset.filter(review_rating__gte=user_rating)

        # Bedrooms filter (support multiple)
        bedrooms = self.request.query_params.getlist("bedrooms") or self.request.query_params.getlist("bedrooms[]")
        if bedrooms:
            queryset = queryset.filter(room_types__bedroom_count__in=bedrooms).distinct()

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
        
        # Faceted counts for available filters
        locations_data = queryset.values('city').annotate(count=Count('id')).order_by('city')
        star_ratings_data = queryset.values('star_rating').annotate(count=Count('id')).order_by('star_rating')
        property_types_data = queryset.values('property_type').annotate(count=Count('id')).order_by('property_type')
        
        # User Review Ratings (Cumulative counts)
        review_rating_counts = [
            {"rating": 4.5, "count": queryset.filter(review_rating__gte=4.5).count()},
            {"rating": 4.0, "count": queryset.filter(review_rating__gte=4.0).count()},
            {"rating": 3.5, "count": queryset.filter(review_rating__gte=3.5).count()},
            {"rating": 3.0, "count": queryset.filter(review_rating__gte=3.0).count()},
        ]

        # Bedrooms data
        # Count unique properties for each bedroom count
        bedrooms_data = queryset.exclude(room_types__bedroom_count__isnull=True)\
            .values('room_types__bedroom_count')\
            .annotate(count=Count('id', distinct=True))\
            .order_by('room_types__bedroom_count')

        # Amenities
        available_amenities = Amenity.objects.filter(properties__in=queryset).values("id", "name").annotate(count=Count('properties')).order_by('-count')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.paginator.get_paginated_response(serializer.data, extra_data={
                "filters": {
                    "price_range": price_range,
                    "available_filters": {
                        "locations": locations_data,
                        "star_ratings": star_ratings_data,
                        "property_types": property_types_data,
                        "user_ratings": review_rating_counts,
                        "bedrooms": bedrooms_data,
                        "amenities": unique_by_id(available_amenities),
                    }
                }
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
