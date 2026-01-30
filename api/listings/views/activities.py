from rest_framework import generics, permissions
from django.db.models import Count
from apps.activities.models import Activity
from ..serializers import ActivityListingSerializer
from ..filters import ListingPagination, get_price_range, unique_list

class ActivityListingAPIView(generics.ListAPIView):
    serializer_class = ActivityListingSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ListingPagination

    def get_queryset(self):
        queryset = Activity.objects.filter(is_active=True)

        destination = self.request.query_params.get("destination")
        if destination:
            queryset = queryset.filter(location__icontains=destination)

        price_min = self.request.query_params.get("price_min")
        if price_min:
            queryset = queryset.filter(base_price__gte=price_min)

        price_max = self.request.query_params.get("price_max")
        if price_max:
            queryset = queryset.filter(base_price__lte=price_max)

        difficulty = self.request.query_params.get("difficulty")
        if difficulty:
            queryset = queryset.filter(difficulty__iexact=difficulty)

        duration = self.request.query_params.get("duration")
        if duration:
            queryset = queryset.filter(duration_days=duration)

        activity_type = self.request.query_params.getlist("activity_type") or self.request.query_params.getlist("activity_type[]")
        if activity_type:
            # Filter by ActivityType name (case-insensitive)
            queryset = queryset.filter(types__name__in=activity_type).distinct()
        
        # Fallback for legacy single value fuzzy search if needed, but let's stick to strict type filtering for now based on UI requirements.
        # If no types found, check if it was a fuzzy search query? 
        # For now, we assume the frontend sends exact type names from the filter list.

        sort_by = self.request.query_params.get("sort_by", "rating")
        if sort_by == "price_asc":
            queryset = queryset.order_by("base_price")
        elif sort_by == "price_desc":
            queryset = queryset.order_by("-base_price")
        else:
            queryset = queryset.order_by("-rating")

        return queryset.prefetch_related("images", "discount", "types")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Metadata
        price_range = get_price_range(queryset, "base_price")
        
        # Faceted Counts for Activity Types
        types_data = queryset.values("types__name").annotate(count=Count("id")).order_by("types__name")
        # Filter out None/Empty types
        types_data = [t for t in types_data if t["types__name"]]

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.paginator.get_paginated_response(serializer.data, extra_data={
                "filters": {
                    "price_range": price_range,
                    "available_filters": {
                        "activity_types": types_data,
                        "difficulties": unique_list(queryset.values_list("difficulty", flat=True).distinct())
                    }
                }
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
