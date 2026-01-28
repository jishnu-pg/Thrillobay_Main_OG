from django.urls import path
from .views import HolidayPackageDetailView

urlpatterns = [
    path("<slug:slug>/", HolidayPackageDetailView.as_view(), name="package-detail"),
]
