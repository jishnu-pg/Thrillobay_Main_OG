from django.urls import path
from .views import FoodDestinationListView, FoodDestinationDetailView

urlpatterns = [
    path("", FoodDestinationListView.as_view(), name="food-destination-list"),
    path("<slug:slug>/", FoodDestinationDetailView.as_view(), name="food-destination-detail"),
]
