from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from .models import HospitalProfile, HospitalDocument, HospitalStaff
from .serializers import (
    HospitalProfileSerializer,
    HospitalProfileCreateSerializer,
    HospitalDocumentSerializer,
    HospitalStaffSerializer,
    SubscriptionSerializer,
)


# ---------------------------------------------------------------------------
# Permission helpers
# ---------------------------------------------------------------------------

def hospital_admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.HOSPITAL_ADMIN:
            return Response(
                {"error": True, "message": "Only hospital admins can perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def hospital_member_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_hospital_member:
            return Response(
                {"error": True, "message": "Only hospital staff can access this."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def get_hospital(user):
    """Get hospital profile for a hospital admin or staff member."""
    try:
        if user.role == User.Role.HOSPITAL_ADMIN:
            return user.hospital_profile
        elif user.role == User.Role.HOSPITAL_STAFF:
            return user.hospital_staff.hospital
    except (HospitalProfile.DoesNotExist, HospitalStaff.DoesNotExist):
        return None


# ---------------------------------------------------------------------------
# Profile endpoints
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@hospital_admin_required
def create_profile(request):
    if hasattr(request.user, "hospital_profile"):
        return Response(
            {"error": True, "message": "Hospital profile already exists."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    serializer = HospitalProfileCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(admin=request.user)
        return Response(
            {
                "message": "Hospital registration submitted for review",
                "hospital_id": serializer.instance.id,
                "status": "pending_review",
            },
            status=status.HTTP_201_CREATED,
        )
    return Response(
        {"error": True, "message": "Validation failed", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@hospital_member_required
def get_profile(request):
    hospital = get_hospital(request.user)
    if not hospital:
        return Response(
            {"error": True, "message": "Hospital profile not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    serializer = HospitalProfileSerializer(hospital)
    return Response(serializer.data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@hospital_admin_required
def update_profile(request):
    hospital = get_hospital(request.user)
    if not hospital:
        return Response(
            {"error": True, "message": "Hospital profile not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    serializer = HospitalProfileSerializer(hospital, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Hospital profile updated"})
    return Response(
        {"error": True, "message": "Validation failed", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@hospital_admin_required
def delete_profile(request):
    hospital = get_hospital(request.user)
    if not hospital:
        return Response(
            {"error": True, "message": "Hospital profile not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    hospital.approval_status = HospitalProfile.ApprovalStatus.SUSPENDED
    hospital.save(update_fields=["approval_status"])
    return Response({"message": "Hospital profile deactivated"})


# ---------------------------------------------------------------------------
# Document upload
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@hospital_admin_required
@parser_classes([MultiPartParser, FormParser])
def upload_document(request):
    hospital = get_hospital(request.user)
    if not hospital:
        return Response(
            {"error": True, "message": "Hospital profile not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    serializer = HospitalDocumentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(hospital=hospital)
        return Response(
            {"message": "Document uploaded successfully"},
            status=status.HTTP_201_CREATED,
        )
    return Response(
        {"error": True, "message": "Validation failed", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


# ---------------------------------------------------------------------------
# Staff management
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@hospital_admin_required
def list_staff(request):
    hospital = get_hospital(request.user)
    if not hospital:
        return Response({"error": True, "message": "Hospital profile not found."}, status=404)
    staff = hospital.staff.select_related("user").all()
    serializer = HospitalStaffSerializer(staff, many=True)
    return Response({"results": serializer.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@hospital_admin_required
def add_staff(request):
    hospital = get_hospital(request.user)
    if not hospital:
        return Response({"error": True, "message": "Hospital profile not found."}, status=404)

    phone = request.data.get("phone")
    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        return Response(
            {"error": True, "message": "No user found with that phone number."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if HospitalStaff.objects.filter(user=user).exists():
        return Response(
            {"error": True, "message": "This user is already linked to a hospital."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.role = User.Role.HOSPITAL_STAFF
    user.save(update_fields=["role"])
    HospitalStaff.objects.create(hospital=hospital, user=user)
    return Response(
        {"message": f"{user.full_name} added as hospital staff."},
        status=status.HTTP_201_CREATED,
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@hospital_admin_required
def remove_staff(request, staff_id):
    hospital = get_hospital(request.user)
    try:
        staff = HospitalStaff.objects.get(id=staff_id, hospital=hospital)
    except HospitalStaff.DoesNotExist:
        return Response(
            {"error": True, "message": "Staff member not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    staff.user.role = User.Role.DONOR
    staff.user.save(update_fields=["role"])
    staff.delete()
    return Response({"message": "Staff member removed."})


# ---------------------------------------------------------------------------
# Subscription
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@hospital_member_required
def get_subscription(request):
    hospital = get_hospital(request.user)
    if not hospital:
        return Response({"error": True, "message": "Hospital not found."}, status=404)
    return Response(
        {
            "tier":               hospital.subscription_tier,
            "status":             hospital.subscription_status,
            "expires_at":         hospital.subscription_expires,
            "searches_remaining": hospital.searches_remaining,
            "is_active":          hospital.is_active_subscriber,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@hospital_admin_required
def activate_subscription(request):
    """
    Dev/test endpoint to manually activate a subscription.
    In production this is triggered by M-Pesa/Stripe payment callbacks.
    """
    hospital = get_hospital(request.user)
    if not hospital:
        return Response({"error": True, "message": "Hospital not found."}, status=404)

    serializer = SubscriptionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": True, "message": "Validation failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tier = serializer.validated_data["tier"]
    hospital.subscription_tier    = tier
    hospital.subscription_status  = "active"
    hospital.subscription_expires = timezone.now() + timedelta(days=30)
    hospital.search_limit         = HospitalProfile.TIER_LIMITS.get(tier, 100)
    hospital.search_quota         = 0
    hospital.save()

    return Response(
        {
            "message":    f"Subscription activated: {tier}",
            "expires_at": hospital.subscription_expires,
            "search_limit": hospital.search_limit,
        }
    )