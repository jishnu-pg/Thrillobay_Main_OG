from django.urls import path
from .views import (
    PropertyListAPIView,
    PropertyDetailAPIView,
    PropertyRoomTypeListAPIView,
)

urlpatterns = [
    path("", PropertyListAPIView.as_view(), name="property-list"),
    path("<int:pk>/", PropertyDetailAPIView.as_view(), name="property-detail"),
    path(
        "<int:pk>/room-types/",
        PropertyRoomTypeListAPIView.as_view(),
        name="property-room-types",
    ),
]

