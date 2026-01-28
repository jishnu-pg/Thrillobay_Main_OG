from django.urls import include, path

urlpatterns = [
    path("auth/", include("api.auth.urls")),
    path("properties/", include("api.properties.urls")),
    path("holiday-packages/", include("api.packages.urls")),
    path("home/", include("api.home.urls")),
    path("listings/", include("api.listings.urls")),
]

