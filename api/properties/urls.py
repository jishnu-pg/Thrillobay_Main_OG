from django.urls import path
from .views import (
    HotelDetailAPIView,
    HotelRoomAvailabilityAPIView,
)

urlpatterns = [
    path("<int:pk>/", HotelDetailAPIView.as_view(), name="hotel-detail"),
    path("<int:pk>/rooms/", HotelRoomAvailabilityAPIView.as_view(), name="hotel-rooms"),
]
