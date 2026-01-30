from rest_framework import generics, permissions
from apps.houseboats.models import HouseBoat
from ..serializers import HouseboatListingSerializer
from ..filters import ListingPagination, get_price_range

class HouseboatListingAPIView(generics.ListAPIView):
    serializer_class = HouseboatListingSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ListingPagination

    def get_queryset(self):
        queryset = HouseBoat.objects.filter(is_active=True)

        destination = self.request.query_params.get("destination")
        if destination:
            queryset = queryset.filter(location__icontains=destination)

        price_min = self.request.query_params.get("price_min")
        if price_min:
            queryset = queryset.filter(base_price_per_night__gte=price_min)

        price_max = self.request.query_params.get("price_max")
        if price_max:
            queryset = queryset.filter(base_price_per_night__lte=price_max)

        bedroom_count = self.request.query_params.get("bedroom_count") or self.request.query_params.get("bedrooms")
        if bedroom_count:
            queryset = queryset.filter(specification__bedrooms=bedroom_count)

        guests = self.request.query_params.get("guests")
        if guests:
            queryset = queryset.filter(specification__max_guests__gte=guests)
            
        houseboat_type = self.request.query_params.get("houseboat_type")
        if houseboat_type:
            queryset = queryset.filter(
                Q(specification__cruise_type__icontains=houseboat_type) | 
                Q(specification__ac_type__icontains=houseboat_type)
            )

        sort_by = self.request.query_params.get("sort_by", "rating")
        if sort_by == "price_asc":
            queryset = queryset.order_by("base_price_per_night")
        elif sort_by == "price_desc":
            queryset = queryset.order_by("-base_price_per_night")
        else:
            queryset = queryset.order_by("-rating")

        return queryset.prefetch_related("images", "specification", "discount")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        price_range = get_price_range(queryset, "base_price_per_night")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.paginator.get_paginated_response(serializer.data, extra_data={
                "filters": {
                    "price_range": price_range,
                    "available_filters": {
                        "bedrooms": queryset.values_list("specification__bedrooms", flat=True).distinct().order_by("specification__bedrooms")
                    }
                }
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
