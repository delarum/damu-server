import random
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import TokenError

from apps.notifications.services import send_email
from .models import User, OTPVerification
from .serializers import (
    RegisterDonorSerializer,
    RegisterHospitalSerializer,
    VerifyOTPSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
)


@api_view(["POST"])
@permission_classes([AllowAny])
def register_donor(request):
    serializer = RegisterDonorSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "message": "Donor account created successfully",
                "user_id": user.id,
                "otp_sent": True,
            },
            status=status.HTTP_201_CREATED,
        )
    return Response(
        {"error": True, "message": "Validation failed", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def register_hospital(request):
    serializer = RegisterHospitalSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "message": "Hospital registration submitted for review",
                "user_id": user.id,
                "status": "pending_review",
            },
            status=status.HTTP_201_CREATED,
        )
    return Response(
        {"error": True, "message": "Validation failed", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    serializer = VerifyOTPSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data["user"]
        otp  = serializer.validated_data["otp"]

        otp.is_used = True
        otp.save()

        if serializer.validated_data["purpose"] == OTPVerification.Purpose.REGISTRATION:
            user.is_verified = True
            user.save(update_fields=["is_verified"])

        return Response({"message": "OTP verified successfully"})
    return Response(
        {"error": True, "message": "Verification failed", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def resend_otp(request):
    email   = request.data.get("email")
    purpose = request.data.get("purpose", OTPVerification.Purpose.REGISTRATION)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"error": True, "message": "User not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    code = str(random.randint(100000, 999999))
    OTPVerification.objects.create(
        user=user,
        code=code,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    subject = "Your DamuLink verification code"
    message = f"Your verification code is: {code}\n\nThis code will expire in 10 minutes."
    send_email(user, subject, message)
    return Response({"message": "OTP resent successfully", "otp_sent": True})


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logged out successfully"})
    except TokenError:
        return Response(
            {"error": True, "message": "Invalid or already blacklisted token"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"message": "Password changed successfully"})
    return Response(
        {"error": True, "message": "Validation failed", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response(
        {
            "id":          user.id,
            "full_name":   user.full_name,
            "email":       user.email,
            "phone":       user.phone,
            "role":        user.role,
            "is_verified": user.is_verified,
            "created_at":  user.created_at,
        }
    )
