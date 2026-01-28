from django.db.models import Min, Max, Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class ListingPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

    def get_paginated_response(self, data, extra_data=None):
        response_data = {
            "filters": extra_data.get("filters", {}),
            "results": data,
            "pagination": {
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "total": self.page.paginator.count
            }
        }
        return Response(response_data)

def get_price_range(queryset, price_field):
    aggregate = queryset.aggregate(min_price=Min(price_field), max_price=Max(price_field))
    return {
        "min": float(aggregate['min_price'] or 0),
        "max": float(aggregate['max_price'] or 0)
    }
