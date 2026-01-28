from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, LoginSerializer, OTPVerificationSerializer


class RegisterAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "OTP sent to your phone number",
                "otp": user.otp_token,  # In production, remove this and send via SMS
                "phone": user.phone,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "OTP sent to your phone number",
                "otp": user.otp_token,  # In production, remove this and send via SMS
                "phone": user.phone,
            },
            status=status.HTTP_200_OK,
        )


class OTPVerificationAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Mark phone as verified
        user.is_phone_verified = True
        user.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "OTP verified successfully",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "phone": user.phone,
                    "is_phone_verified": user.is_phone_verified,
                },
            },
            status=status.HTTP_200_OK,
        )
