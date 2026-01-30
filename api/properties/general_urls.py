from django.urls import path
from .views import FamousPlaceListAPIView

urlpatterns = [
    path("famous-places/", FamousPlaceListAPIView.as_view(), name="famous-places-list"),
]
