import random
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("User with this phone number already exists.")
        return value

    def create(self, validated_data):
        otp = str(random.randint(100000, 999999))
        phone = validated_data["phone"]
        
        # Generate a unique username from phone number
        username = f"user_{phone}"
        
        # Create user with random password (we don't use passwords, but Django requires one)
        random_password = User.objects.make_random_password(length=50)
        user = User.objects.create_user(
            username=username,
            phone=phone,
            password=random_password,
        )
        # Set unusable password so it can't be used for login
        user.set_unusable_password()
        user.otp_token = otp
        user.otp_created_at = timezone.now()
        user.is_phone_verified = False
        user.save()
        
        return user


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)

    def validate_phone(self, value):
        if not User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("User with this phone number does not exist.")
        return value

    def create(self, validated_data):
        phone = validated_data["phone"]
        user = User.objects.get(phone=phone)
        
        # Generate new OTP
        otp = str(random.randint(100000, 999999))
        user.otp_token = otp
        user.otp_created_at = timezone.now()
        user.save()
        
        return user


class OTPVerificationSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=10)

    def validate(self, attrs):
        phone = attrs.get("phone")
        otp = attrs.get("otp")
        
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError({"phone": "User with this phone number does not exist."})
        
        if not user.otp_token:
            raise serializers.ValidationError({"otp": "No OTP found. Please request a new OTP."})
        
        if user.otp_token != otp:
            raise serializers.ValidationError({"otp": "Invalid OTP."})
        
        # Check if OTP is expired (15 minutes)
        from django.utils import timezone
        if user.otp_created_at:
            time_diff = timezone.now() - user.otp_created_at
            if time_diff.total_seconds() > 900:  # 15 minutes
                raise serializers.ValidationError({"otp": "OTP has expired. Please request a new one."})
        
        attrs["user"] = user
        return attrs
