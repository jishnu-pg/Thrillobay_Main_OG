from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from apps.support.models import FAQ
from .serializers import FAQListSerializer


class FAQListAPIView(ListAPIView):
    """
    API to list FAQs filtered by location.
    Query Param: /api/support/faqs/?location=Wayanad
    """
    serializer_class = FAQListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = FAQ.objects.filter(is_active=True).prefetch_related("items")
        location = self.request.query_params.get("location")
        if location:
            queryset = queryset.filter(location__iexact=location)
        return queryset
