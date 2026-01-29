from django.urls import include, path

urlpatterns = [
    path("auth/", include("api.auth.urls")),
    path("hotels/", include("api.properties.urls")),
    path("homestays/", include("api.properties.homestay_urls")),
    path("holiday-packages/", include("api.packages.urls")),
    path("houseboats/", include("api.houseboats.urls")),
    path("activities/", include("api.activities.urls")),
    path("cabs/", include("api.cabs.urls")),
    path("home/", include("api.home.urls")),
    path("listings/", include("api.listings.urls")),
    path("bookings/", include("api.bookings.urls")),
    path("coupons/", include("api.coupons.urls")),
    path("support/", include("api.support.urls")),
    path("dining/", include("api.dining.urls")),
]

