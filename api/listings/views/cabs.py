from rest_framework import generics, permissions
from apps.cabs.models import Cab, CabCategory
from ..serializers import CabListingSerializer
from ..filters import ListingPagination, get_price_range

class CabListingAPIView(generics.ListAPIView):
    serializer_class = CabListingSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ListingPagination

    def get_queryset(self):
        queryset = Cab.objects.filter(is_active=True)

        price_min = self.request.query_params.get("price_min")
        if price_min:
            queryset = queryset.filter(base_price__gte=price_min)

        price_max = self.request.query_params.get("price_max")
        if price_max:
            queryset = queryset.filter(base_price__lte=price_max)

        fuel_type = self.request.query_params.get("fuel_type")
        if fuel_type:
            queryset = queryset.filter(fuel_type=fuel_type)

        capacity = self.request.query_params.get("seating_capacity") or self.request.query_params.get("capacity")
        if capacity:
            queryset = queryset.filter(capacity__gte=capacity)

        sort_by = self.request.query_params.get("sort_by", "price_asc")
        if sort_by == "price_asc":
            queryset = queryset.order_by("base_price")
        elif sort_by == "price_desc":
            queryset = queryset.order_by("-base_price")
        else:
            queryset = queryset.order_by("base_price") # Default for cabs is price_asc

        return queryset.prefetch_related("images", "category")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        price_range = get_price_range(queryset, "base_price")
        
        available_categories = CabCategory.objects.filter(cabs__in=queryset).distinct().values("id", "name")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.paginator.get_paginated_response(serializer.data, extra_data={
                "filters": {
                    "price_range": price_range,
                    "available_filters": {
                        "categories": available_categories,
                        "fuel_types": queryset.values_list("fuel_type", flat=True).distinct()
                    }
                }
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
