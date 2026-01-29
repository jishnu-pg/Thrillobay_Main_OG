from django.urls import path
from .views import HolidayPackageDetailAPIView, PackagePricingAPIView

urlpatterns = [
    path("<int:pk>/", HolidayPackageDetailAPIView.as_view(), name="package-detail"),
    path("<int:pk>/price/", PackagePricingAPIView.as_view(), name="package-price"),
]
