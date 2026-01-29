from django.urls import path
from .views import ActivityDetailAPIView

urlpatterns = [
    path("<int:pk>/", ActivityDetailAPIView.as_view(), name="activity-detail"),
]
