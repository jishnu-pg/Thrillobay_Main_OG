from rest_framework import generics, permissions
from django.db.models import Count
from apps.cabs.models import Cab, CabCategory
from ..serializers import CabListingSerializer
from ..filters import ListingPagination, get_price_range, unique_list, unique_by_id

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

        # Multi-select Fuel Type
        fuel_types = self.request.query_params.getlist("fuel_type") or self.request.query_params.getlist("fuel_type[]")
        if fuel_types:
            queryset = queryset.filter(fuel_type__in=fuel_types)

        # Multi-select Cab Category (Cab Type)
        categories = self.request.query_params.getlist("category") or self.request.query_params.getlist("category[]")
        if categories:
            # Filter by Category Name (case-insensitive if needed, but ID or Name match is better)
            # Assuming frontend sends names like "Sedan", "Hatchback"
            queryset = queryset.filter(category__name__in=categories)

        # Multi-select Cab Model (Title)
        models_list = self.request.query_params.getlist("cab_model") or self.request.query_params.getlist("cab_model[]")
        if models_list:
            queryset = queryset.filter(title__in=models_list)

        # Multi-select Seating Capacity
        capacities = self.request.query_params.getlist("seating_capacity") or self.request.query_params.getlist("seating_capacity[]")
        if capacities:
            # Check if values are integers like "4", "6" or strings like "4 seater"
            # We strip " seater" just in case, but ideally frontend sends raw numbers
            cleaned_capacities = []
            for c in capacities:
                try:
                    cleaned_capacities.append(int(str(c).lower().replace("seater", "").replace("seat", "").strip()))
                except ValueError:
                    pass
            if cleaned_capacities:
                queryset = queryset.filter(capacity__in=cleaned_capacities)

        # Multi-select Transfer Type
        transfer_types = self.request.query_params.getlist("transfer_type") or self.request.query_params.getlist("transfer_type[]")
        if transfer_types:
            queryset = queryset.filter(transfer_types__name__in=transfer_types).distinct()

        sort_by = self.request.query_params.get("sort_by", "price_asc")
        if sort_by == "price_asc":
            queryset = queryset.order_by("base_price")
        elif sort_by == "price_desc":
            queryset = queryset.order_by("-base_price")
        else:
            queryset = queryset.order_by("base_price") # Default for cabs is price_asc

        return queryset.prefetch_related("images", "category", "transfer_types")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        price_range = get_price_range(queryset, "base_price")
        
        # Faceted Counts
        # 1. Cab Type (Category)
        categories_data = queryset.values("category__name").annotate(count=Count("id")).order_by("category__name")
        categories_data = [c for c in categories_data if c["category__name"]]

        # 2. Fuel Type
        fuel_data = queryset.values("fuel_type").annotate(count=Count("id")).order_by("fuel_type")
        
        # 3. Cab Model (Title)
        models_data = queryset.values("title").annotate(count=Count("id")).order_by("title")
        
        # 4. Seating Capacity
        capacity_data = queryset.values("capacity").annotate(count=Count("id")).order_by("capacity")
        
        # 5. Transfer Type
        transfer_data = queryset.values("transfer_types__name").annotate(count=Count("id")).order_by("transfer_types__name")
        transfer_data = [t for t in transfer_data if t["transfer_types__name"]]

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.paginator.get_paginated_response(serializer.data, extra_data={
                "filters": {
                    "price_range": price_range,
                    "available_filters": {
                        "categories": categories_data,
                        "fuel_types": fuel_data,
                        "cab_models": models_data,
                        "seating_capacities": capacity_data,
                        "transfer_types": transfer_data
                    }
                }
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
