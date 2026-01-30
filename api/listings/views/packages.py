from rest_framework import generics, permissions
from django.db.models import Q, Min, Max, Count
from apps.packages.models import HolidayPackage
from ..serializers import PackageListingSerializer
from ..filters import ListingPagination, get_price_range, unique_list

class PackageListingAPIView(generics.ListAPIView):
    serializer_class = PackageListingSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ListingPagination

    def get_queryset(self):
        queryset = HolidayPackage.objects.filter(is_active=True)

        destination = self.request.query_params.get("destination")
        if destination:
            queryset = queryset.filter(primary_location__icontains=destination)

        price_min = self.request.query_params.get("price_min")
        if price_min:
            queryset = queryset.filter(base_price__gte=price_min)

        price_max = self.request.query_params.get("price_max")
        if price_max:
            queryset = queryset.filter(base_price__lte=price_max)

        # Duration Range (Nights)
        min_nights = self.request.query_params.get("min_nights")
        if min_nights:
            queryset = queryset.filter(duration_nights__gte=min_nights)
            
        max_nights = self.request.query_params.get("max_nights")
        if max_nights:
            queryset = queryset.filter(duration_nights__lte=max_nights)

        # Themes / Package Types
        themes = self.request.query_params.getlist("themes") or self.request.query_params.getlist("themes[]")
        if themes:
            queryset = queryset.filter(themes__name__in=themes).distinct()

        duration = self.request.query_params.get("duration") or self.request.query_params.get("duration_days")
        if duration:
            # Handle "1-2 Days" format or exact number
            if "-" in str(duration):
                try:
                    min_d, max_d = map(int, str(duration).lower().replace("days", "").replace("day", "").split("-"))
                    queryset = queryset.filter(duration_days__gte=min_d, duration_days__lte=max_d)
                except ValueError:
                    pass
            else:
                try:
                    d = int(str(duration).lower().replace("days", "").replace("day", "").strip())
                    queryset = queryset.filter(duration_days=d)
                except ValueError:
                    pass

        sort_by = self.request.query_params.get("sort_by", "rating")
        if sort_by == "price_asc":
            queryset = queryset.order_by("base_price")
        elif sort_by == "price_desc":
            queryset = queryset.order_by("-base_price")
        else:
            queryset = queryset.order_by("-rating")

        return queryset.prefetch_related("images", "discount", "themes")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Metadata
        price_range = get_price_range(queryset, "base_price")
        
        # Duration Range (Nights)
        min_duration = queryset.aggregate(min=Min("duration_nights"))["min"]
        max_duration = queryset.aggregate(max=Max("duration_nights"))["max"]
        duration_range = {"min": min_duration, "max": max_duration}
        
        # Faceted Counts for Themes
        themes_data = queryset.values("themes__name").annotate(count=Count("id")).order_by("themes__name")
        # Filter out None/Empty themes
        themes_data = [t for t in themes_data if t["themes__name"]]

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.paginator.get_paginated_response(serializer.data, extra_data={
                "filters": {
                    "price_range": price_range,
                    "duration_range": duration_range,
                    "available_filters": {
                        "themes": themes_data,
                        "durations": unique_list(queryset.values_list("duration_days", flat=True).distinct().order_by("duration_days"))
                    }
                }
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
