from django.urls import path
from .views.hotels import HotelListingAPIView
from .views.homestays import HomestayListingAPIView
from .views.packages import PackageListingAPIView
from .views.houseboats import HouseboatListingAPIView
from .views.activities import ActivityListingAPIView
from .views.cabs import CabListingAPIView

urlpatterns = [
    path("hotels/", HotelListingAPIView.as_view(), name="listing-hotels"),
    path("homestays/", HomestayListingAPIView.as_view(), name="listing-homestays"),
    path("packages/", PackageListingAPIView.as_view(), name="listing-packages"),
    path("houseboats/", HouseboatListingAPIView.as_view(), name="listing-houseboats"),
    path("activities/", ActivityListingAPIView.as_view(), name="listing-activities"),
    path("cabs/", CabListingAPIView.as_view(), name="listing-cabs"),
]
