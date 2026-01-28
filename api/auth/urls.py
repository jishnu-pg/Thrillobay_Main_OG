from django.urls import path
from .views import RegisterAPIView, LoginAPIView, OTPVerificationAPIView

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("verify-otp/", OTPVerificationAPIView.as_view(), name="verify-otp"),
]
