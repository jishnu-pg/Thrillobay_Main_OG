"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.contrib.auth import get_user_model

def home(request):
    return JsonResponse({
        "message": "Welcome to Thrillobay API",
        "status": "Running",
        "documentation": "/api/",
        "admin": "/admin/"
    })

def create_admin_view(request):
    """
    Temporary view to create a superuser for Render deployment.
    Usage: Visit /create-superuser-secure-x9z/
    """
    User = get_user_model()
    username = "admin"
    email = "admin@thrillobay.com"
    password = "adminpassword123"  # Change this immediately after login!

    if not User.objects.filter(username=username).exists():
        try:
            User.objects.create_superuser(username, email, password)
            return JsonResponse({"status": "success", "message": f"Superuser '{username}' created successfully."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    else:
        return JsonResponse({"status": "warning", "message": f"Superuser '{username}' already exists."})

urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),
    path('create-superuser-secure-x9z/', create_admin_view), # Temporary secret URL
    path("api/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

