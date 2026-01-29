from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TravellerViewSet

router = DefaultRouter()
router.register(r'', TravellerViewSet, basename='traveller')

urlpatterns = [
    path('', include(router.urls)),
]
