from rest_framework import generics, permissions
from apps.activities.models import Activity
from ..serializers import ActivityListingSerializer
from ..filters import ListingPagination, get_price_range

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
            queryset = queryset.filter(difficulty=difficulty)

        sort_by = self.request.query_params.get("sort_by", "rating")
        if sort_by == "price_asc":
            queryset = queryset.order_by("base_price")
        elif sort_by == "price_desc":
            queryset = queryset.order_by("-base_price")
        else:
            queryset = queryset.order_by("-rating")

        return queryset.prefetch_related("images", "discount")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        price_range = get_price_range(queryset, "base_price")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.paginator.get_paginated_response(serializer.data, extra_data={
                "filters": {
                    "price_range": price_range,
                    "available_filters": {
                        "difficulties": queryset.values_list("difficulty", flat=True).distinct()
                    }
                }
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
