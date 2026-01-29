from django.urls import path
from .views import (
    HomestayDetailAPIView,
    HomestayRoomAvailabilityAPIView,
)

urlpatterns = [
    path("<int:pk>/", HomestayDetailAPIView.as_view(), name="homestay-detail"),
    path("<int:pk>/rooms/", HomestayRoomAvailabilityAPIView.as_view(), name="homestay-rooms"),
]
