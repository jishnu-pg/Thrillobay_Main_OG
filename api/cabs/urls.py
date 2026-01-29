from django.urls import path
from .views import CabDetailAPIView

urlpatterns = [
    path("<int:pk>/", CabDetailAPIView.as_view(), name="cab-detail"),
]
