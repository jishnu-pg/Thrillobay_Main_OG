from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from django.db.models import Prefetch
from apps.activities.models import Activity, ActivityImage, ActivityHighlight, ActivityItinerary, ActivityInclusion
from apps.support.models import FAQ
from .serializers import ActivityDetailSerializer

class ActivityDetailAPIView(RetrieveAPIView):
    """
    Returns full details for an Activity/Experience detail page.
    Lookup is performed using 'id'.
    """
    queryset = (
        Activity.objects.filter(is_active=True)
        .select_related("discount", "policy")
        .prefetch_related(
            Prefetch("images", queryset=ActivityImage.objects.all().order_by("-is_primary", "order")),
            Prefetch("highlights", queryset=ActivityHighlight.objects.all()),
            Prefetch("itinerary", queryset=ActivityItinerary.objects.all().order_by("day_number", "order")),
            Prefetch("inclusions", queryset=ActivityInclusion.objects.all()),
        )
    )
    serializer_class = ActivityDetailSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        obj = self.get_object()

        # 1. Fetch Similar Activities (same location, same difficulty, exclude self)
        similar = (
            Activity.objects.filter(
                location__icontains=obj.location,
                difficulty=obj.difficulty,
                is_active=True
            )
            .exclude(id=obj.id)
            .prefetch_related(
                Prefetch("images", queryset=ActivityImage.objects.filter(is_primary=True))
            )[:4]
        )
        context["similar_activities"] = list(similar)

        # 2. Fetch FAQs (Location-based from support app)
        faqs = (
            FAQ.objects.filter(location__icontains=obj.location, is_active=True)
            .prefetch_related("items")
        )
        faqs_data = []
        for f in faqs:
            answer = " ".join([item.description for item in f.items.all()])
            faqs_data.append({
                "question": f.question,
                "answer": answer
            })
        context["faqs"] = faqs_data

        return context
