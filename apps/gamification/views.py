from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.donors.models import DonorProfile
from apps.hospitals.models import HospitalProfile, HospitalStaff
from .models import DonationRecord, CreditLedger, DonorBadge
from .serializers import (
    DonationRecordSerializer,
    DonationRecordCreateSerializer,
    CreditLedgerSerializer,
    DonorBadgeSerializer,
    RedeemCreditsSerializer,
)
from .services import record_donation, get_credit_balance, redeem_credits


def get_hospital(user):
    try:
        if user.role == User.Role.HOSPITAL_ADMIN:
            return user.hospital_profile
        elif user.role == User.Role.HOSPITAL_STAFF:
            return user.hospital_staff.hospital
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Donation records
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_donation(request):
    """Hospital staff records a confirmed donation."""
    hospital = get_hospital(request.user)
    if not hospital:
        return Response(
            {"error": True, "message": "Only hospital staff can record donations."},
            status=status.HTTP_403_FORBIDDEN,
        )

    donor_id      = request.data.get("donor_id")
    donation_type = request.data.get("donation_type")
    donation_date = request.data.get("donation_date")

    if not all([donor_id, donation_type, donation_date]):
        return Response(
            {"error": True, "message": "donor_id, donation_type, and donation_date are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        donor = DonorProfile.objects.get(id=donor_id)
    except DonorProfile.DoesNotExist:
        return Response({"error": True, "message": "Donor not found."}, status=404)

    valid_types = [c[0] for c in DonationRecord.DonationType.choices]
    if donation_type not in valid_types:
        return Response(
            {"error": True, "message": f"Invalid donation_type. Choose from: {valid_types}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    record = record_donation(
        donor_profile=donor,
        hospital_profile=hospital,
        donation_type=donation_type,
        donation_date=donation_date,
        confirmed_by=request.user,
    )

    return Response(
        {
            "message": "Donation recorded successfully",
            "donation_id":     record.id,
            "credits_awarded": record.credits_awarded,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def donation_history(request):
    """Donor views their own donation history."""
    if request.user.role != User.Role.DONOR:
        return Response({"error": True, "message": "Only donors can view this."}, status=403)

    try:
        donor = request.user.donor_profile
    except DonorProfile.DoesNotExist:
        return Response({"error": True, "message": "Donor profile not found."}, status=404)

    donations = DonationRecord.objects.filter(donor=donor).select_related("hospital")
    serializer = DonationRecordSerializer(donations, many=True)
    return Response({"count": donations.count(), "results": serializer.data})


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def manage_donation(request, donation_id):
    """Hospital staff updates or removes a donation record."""
    hospital = get_hospital(request.user)
    if not hospital:
        return Response({"error": True, "message": "Only hospital staff can manage donations."}, status=403)

    try:
        record = DonationRecord.objects.get(id=donation_id, hospital=hospital)
    except DonationRecord.DoesNotExist:
        return Response({"error": True, "message": "Donation record not found."}, status=404)

    if request.method == "DELETE":
        record.delete()
        return Response({"message": "Donation record removed."})

    serializer = DonationRecordSerializer(record, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Donation record updated."})
    return Response({"error": True, "details": serializer.errors}, status=400)


# ---------------------------------------------------------------------------
# Credits
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def credit_balance(request):
    if request.user.role != User.Role.DONOR:
        return Response({"error": True, "message": "Only donors have credits."}, status=403)

    try:
        donor = request.user.donor_profile
    except DonorProfile.DoesNotExist:
        return Response({"error": True, "message": "Donor profile not found."}, status=404)

    balance = get_credit_balance(donor)
    return Response({"credits": balance, "cash_equivalent": balance})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def credit_ledger(request):
    if request.user.role != User.Role.DONOR:
        return Response({"error": True, "message": "Only donors can view their ledger."}, status=403)

    try:
        donor = request.user.donor_profile
    except DonorProfile.DoesNotExist:
        return Response({"error": True, "message": "Donor profile not found."}, status=404)

    ledger = CreditLedger.objects.filter(donor=donor)
    serializer = CreditLedgerSerializer(ledger, many=True)
    return Response({"count": ledger.count(), "results": serializer.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def redeem_credits_view(request):
    if request.user.role != User.Role.DONOR:
        return Response({"error": True, "message": "Only donors can redeem credits."}, status=403)

    try:
        donor = request.user.donor_profile
    except DonorProfile.DoesNotExist:
        return Response({"error": True, "message": "Donor profile not found."}, status=404)

    serializer = RedeemCreditsSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": True, "details": serializer.errors}, status=400)

    success, message, new_balance = redeem_credits(
        donor,
        serializer.validated_data["amount"],
        serializer.validated_data["reason"],
    )

    if not success:
        return Response({"error": True, "message": message}, status=400)

    return Response({"message": message, "new_balance": new_balance})


# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def donor_badges(request):
    if request.user.role != User.Role.DONOR:
        return Response({"error": True, "message": "Only donors have badges."}, status=403)

    try:
        donor = request.user.donor_profile
    except DonorProfile.DoesNotExist:
        return Response({"error": True, "message": "Donor profile not found."}, status=404)

    badges = DonorBadge.objects.filter(donor=donor).select_related("badge")
    serializer = DonorBadgeSerializer(badges, many=True)
    return Response({"count": badges.count(), "results": serializer.data})