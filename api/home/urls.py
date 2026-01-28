from django.urls import path
from .views import (
    PopularHotelsAPIView, 
    PopularHomestaysAPIView, 
    PopularHolidayPackagesAPIView,
    PopularHouseboatsAPIView,
    PopularActivitiesAPIView,
    GlobalSearchAPIView
)

urlpatterns = [
    path("search/", GlobalSearchAPIView.as_view(), name="global-search"),
    path("popular-hotels/", PopularHotelsAPIView.as_view(), name="popular-hotels"),
    path("popular-homestays/", PopularHomestaysAPIView.as_view(), name="popular-homestays"),
    path("popular-holiday-packages/", PopularHolidayPackagesAPIView.as_view(), name="popular-holiday-packages"),
    path("popular-houseboats/", PopularHouseboatsAPIView.as_view(), name="popular-houseboats"),
    path("popular-activities/", PopularActivitiesAPIView.as_view(), name="popular-activities"),
]
