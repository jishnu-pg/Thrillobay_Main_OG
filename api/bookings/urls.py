from django.urls import path
from .views import BookingCreateAPIView, BookingListAPIView, BookingDetailAPIView, BookingReviewAPIView, BookingConfirmAPIView

urlpatterns = [
    path("review/", BookingReviewAPIView.as_view(), name="booking-review"),
    path("confirm/<int:id>/", BookingConfirmAPIView.as_view(), name="booking-confirm"),
    path("create/", BookingCreateAPIView.as_view(), name="booking-create"),
    path("", BookingListAPIView.as_view(), name="booking-list"),
    path("<int:id>/", BookingDetailAPIView.as_view(), name="booking-detail"),
]
