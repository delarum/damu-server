import random
from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.notifications.services import send_email
from .models import User, OTPVerification


class RegisterDonorSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["full_name", "email", "password", "phone", "national_id", "date_of_birth"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
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
        subject = "Verify your DamuLink account"
        message = f"Your verification code is: {code}\n\nThis code will expire in 10 minutes."
        send_email(user, subject, message)


class RegisterHospitalSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["full_name", "email", "password", "phone"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data, role=User.Role.HOSPITAL_ADMIN)
        user.set_password(password)
        user.save()
        return user


class VerifyOTPSerializer(serializers.Serializer):
    email   = serializers.EmailField()
    code    = serializers.CharField(max_length=6)
    purpose = serializers.ChoiceField(choices=OTPVerification.Purpose.choices)

    def validate(self, data):
      try:
        user = User.objects.get(email=data["email"])
      except User.DoesNotExist:
        raise serializers.ValidationError(f"No user found for email: {data['email']}")

      otp = OTPVerification.objects.filter(
        user=user,
        code=data["code"],
        purpose=data["purpose"],
        is_used=False,
      ).last()

      if not otp:
        raise serializers.ValidationError(
            f"No matching OTP found for purpose='{data['purpose']}', code='{data['code']}'"
        )
      if not otp.is_valid():
        raise serializers.ValidationError(
            f"OTP expired at {otp.expires_at} (now {timezone.now()})"
        )

      data["user"] = user
      data["otp"] = otp
      return data


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds user role and verification status to the JWT response."""
    username_field = "email"

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