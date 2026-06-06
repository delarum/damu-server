import random
from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, OTPVerification


class RegisterDonorSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["full_name", "phone", "email", "password", "national_id", "date_of_birth"]

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data, role=User.Role.DONOR)
        user.set_password(password)
        user.save()
        self._send_otp(user)
        return user

    def _send_otp(self, user):
        code = str(random.randint(100000, 999999))
        OTPVerification.objects.create(
            user=user,
            code=code,
            purpose=OTPVerification.Purpose.REGISTRATION,
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        # TODO: send via Africa's Talking SMS
        print(f"[DEV] OTP for {user.phone}: {code}")


class RegisterHospitalSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["full_name", "phone", "email", "password"]

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data, role=User.Role.HOSPITAL_ADMIN)
        user.set_password(password)
        user.save()
        return user


class VerifyOTPSerializer(serializers.Serializer):
    phone   = serializers.CharField()
    code    = serializers.CharField(max_length=6)
    purpose = serializers.ChoiceField(choices=OTPVerification.Purpose.choices)

    def validate(self, data):
        try:
            user = User.objects.get(phone=data["phone"])
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        otp = OTPVerification.objects.filter(
            user=user,
            code=data["code"],
            purpose=data["purpose"],
            is_used=False,
        ).last()

        if not otp or not otp.is_valid():
            raise serializers.ValidationError("Invalid or expired OTP.")

        data["user"] = user
        data["otp"]  = otp
        return data


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds user role and verification status to the JWT response."""
    username_field = "phone"

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"]        = user.role
        token["is_verified"] = user.is_verified
        token["full_name"]   = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id":          self.user.id,
            "role":        self.user.role,
            "is_verified": self.user.is_verified,
            "full_name":   self.user.full_name,
        }
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value