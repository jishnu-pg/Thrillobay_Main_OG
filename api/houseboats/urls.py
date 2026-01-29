from django.urls import path
from .views import HouseboatDetailAPIView

urlpatterns = [
    path("<int:pk>/", HouseboatDetailAPIView.as_view(), name="houseboat-detail"),
]
