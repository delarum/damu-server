from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DonorProfile
from .serializers import DonorProfileSerializer, DonorProfileCreateSerializer
from apps.accounts.models import User


def donor_required(view_func):
    """Decorator: ensures the user is a donor."""
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.DONOR:
            return Response(
                {"error": True, "message": "Only donors can access this endpoint."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@donor_required
def create_profile(request):
    # Prevent duplicate profiles
    if hasattr(request.user, "donor_profile"):
        return Response(
            {"error": True, "message": "Donor profile already exists. Use PATCH to update."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = DonorProfileCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(
            {"message": "Donor profile created successfully", "profile_id": serializer.instance.id},
            status=status.HTTP_201_CREATED,
        )
    return Response(
        {"error": True, "message": "Validation failed", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@donor_required
def get_profile(request):
    try:
        profile = request.user.donor_profile
    except DonorProfile.DoesNotExist:
        return Response(
            {"error": True, "message": "Donor profile not found. Please create one first."},
            status=status.HTTP_404_NOT_FOUND,
        )
    serializer = DonorProfileSerializer(profile)
    return Response(serializer.data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@donor_required
def update_profile(request):
    try:
        profile = request.user.donor_profile
    except DonorProfile.DoesNotExist:
        return Response(
            {"error": True, "message": "Donor profile not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = DonorProfileSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Profile updated successfully"})
    return Response(
        {"error": True, "message": "Validation failed", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@donor_required
def delete_profile(request):
    # Soft delete — deactivate the user account
    request.user.is_active = False
    request.user.save(update_fields=["is_active"])
    return Response(
        {"message": "Donor account scheduled for deletion"},
        status=status.HTTP_200_OK,
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@donor_required
def toggle_availability(request):
    try:
        profile = request.user.donor_profile
    except DonorProfile.DoesNotExist:
        return Response(
            {"error": True, "message": "Donor profile not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    profile.availability_status = not profile.availability_status
    profile.save(update_fields=["availability_status"])
    state = "available" if profile.availability_status else "unavailable"
    return Response({"message": f"You are now marked as {state}.", "availability_status": profile.availability_status})