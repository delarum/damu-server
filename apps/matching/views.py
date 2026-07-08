
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.donors.models import DonorProfile
from apps.hospitals.models import HospitalProfile, HospitalStaff
from utils.geo import donors_within_radius
from .models import ContactRequest
from .serializers import (
    ContactRequestCreateSerializer,
    ContactRequestSerializer,
    DonorSearchResultSerializer,
)


# ---------------------------------------------------------------------------
# Permission helpers
# ---------------------------------------------------------------------------

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
    try:
        if user.role == User.Role.HOSPITAL_ADMIN:
            return user.hospital_profile
        elif user.role == User.Role.HOSPITAL_STAFF:
            return user.hospital_staff.hospital
    except (HospitalProfile.DoesNotExist, HospitalStaff.DoesNotExist):
        return None


def check_subscription(hospital):
    if not hospital.is_active_subscriber:
        return Response(
            {"error": True, "message": "Active subscription required to search donors."},
            status=status.HTTP_403_FORBIDDEN,
        )
    if hospital.searches_remaining <= 0:
        return Response(
            {"error": True, "message": "Monthly search quota exceeded. Please upgrade your plan."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    return None


# ---------------------------------------------------------------------------
# Search endpoints
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@hospital_member_required
def search_blood_donors(request):
    hospital = get_hospital(request.user)
    if not hospital:
        return Response({"error": True, "message": "Hospital not found."}, status=404)

    quota_error = check_subscription(hospital)
    if quota_error:
        return quota_error

    # Query params
    blood_type = request.query_params.get("blood_type")
    radius_km  = float(request.query_params.get("radius", 10))

    if not blood_type:
        return Response(
            {"error": True, "message": "blood_type query parameter is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if hospital.lat is None or hospital.lng is None:
        return Response(
            {"error": True, "message": "Hospital location not set. Update your profile with lat/lng."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Base queryset — available blood donors matching blood type
    donors_qs = DonorProfile.objects.filter(
        blood_type=blood_type,
        donor_type__in=["blood", "both"],
        availability_status=True,
        verification_status="verified",
    ).select_related("user")

    # Filter by cooldown
    now = timezone.now()
    donors_qs = donors_qs.filter(
        cooldown_until__isnull=True
    ) | donors_qs.filter(cooldown_until__lt=now)

    # Distance filtering (server-side — donor coords never sent to client)
    nearby = donors_within_radius(donors_qs, hospital.lat, hospital.lng, radius_km)

    # Increment search quota
    hospital.search_quota += 1
    hospital.save(update_fields=["search_quota"])

    # Build results — attach distance to each donor object temporarily
    results = []
    for donor, distance in nearby:
        donor._distance_km = distance
        results.append(donor)

    # Serialize
    data = []
    for donor in results:
        serializer = DonorSearchResultSerializer(donor)
        row = serializer.data
        row["distance_km"] = donor._distance_km
        data.append(row)

    return Response({"count": len(data), "results": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@hospital_member_required
def search_organ_donors(request):
    hospital = get_hospital(request.user)
    if not hospital:
        return Response({"error": True, "message": "Hospital not found."}, status=404)

    quota_error = check_subscription(hospital)
    if quota_error:
        return quota_error

    organ     = request.query_params.get("organ")
    radius_km = float(request.query_params.get("radius", 50))

    if not organ:
        return Response(
            {"error": True, "message": "organ query parameter is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if hospital.lat is None or hospital.lng is None:
        return Response(
            {"error": True, "message": "Hospital location not set."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    donors_qs = DonorProfile.objects.filter(
        donor_type__in=["organ", "both"],
        availability_status=True,
        verification_status="verified",
    ).select_related("user")

    # Filter by organ in JSONField
    donors_qs = [d for d in donors_qs if organ in (d.organs_pledged or [])]

    nearby = donors_within_radius(donors_qs, hospital.lat, hospital.lng, radius_km)

    hospital.search_quota += 1
    hospital.save(update_fields=["search_quota"])

    data = []
    for donor, distance in nearby:
        data.append({
            "donor_id":   donor.id,
            "name":       _masked_name(donor),
            "organ":      organ,
            "distance_km": distance,
            "county":     donor.county,
            "town":       donor.town,
        })

    return Response({"count": len(data), "results": data})



# ---------------------------------------------------------------------------
# Donor map endpoint — full national network for hospitals
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@hospital_member_required
def donor_map(request):
    hospital = get_hospital(request.user)
    if not hospital:
        return Response({"error": True, "message": "Hospital not found."}, status=404)

    donors_qs = DonorProfile.objects.filter(
        lat__isnull=False,
        lng__isnull=False,
    ).select_related("user")

    # Optional filters
    blood_type = request.query_params.get("blood_type")
    if blood_type:
        donors_qs = donors_qs.filter(blood_type=blood_type)

    donor_type = request.query_params.get("donor_type")
    if donor_type in ["blood", "organ", "both"]:
        donors_qs = donors_qs.filter(donor_type=donor_type)

    results = []
    for donor in donors_qs:
        results.append({
            "id":                    donor.id,
            "full_name":             donor.user.full_name,
            "phone":                 donor.user.phone,
            "blood_type":            donor.blood_type,
            "donor_type":            donor.donor_type,
            "organs_pledged":        donor.organs_pledged,
            "county":                donor.county,
            "sub_county":            donor.sub_county,
            "town":                  donor.town,
            "lat":                   float(donor.lat),
            "lng":                   float(donor.lng),
            "availability_status":   donor.availability_status,
            "verification_status":   donor.verification_status,
            "preferred_contact_method": donor.preferred_contact_method,
            "last_donation_date":    donor.last_donation_date,
        })

    return Response({"count": len(results), "results": results})

def _masked_name(donor):
    parts = donor.user.full_name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[-1][0]}."
    return parts[0] if parts else "Donor"


# ---------------------------------------------------------------------------
# Contact requests
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@hospital_member_required
def initiate_contact_request(request):
    hospital = get_hospital(request.user)
    if not hospital:
        return Response({"error": True, "message": "Hospital not found."}, status=404)

    if not hospital.is_active_subscriber:
        return Response(
            {"error": True, "message": "Active subscription required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = ContactRequestCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": True, "message": "Validation failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    donor_id = serializer.validated_data["donor_id"]
    reason   = serializer.validated_data["reason"]

    try:
        donor = DonorProfile.objects.get(id=donor_id)
    except DonorProfile.DoesNotExist:
        return Response(
            {"error": True, "message": "Donor not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Prevent duplicate pending requests
    existing = ContactRequest.objects.filter(
        hospital=hospital, donor=donor, status=ContactRequest.Status.PENDING
    ).exists()
    if existing:
        return Response(
            {"error": True, "message": "A pending contact request already exists for this donor."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    contact_request = ContactRequest.objects.create(
        hospital=hospital,
        donor=donor,
        initiated_by=request.user,
        reason=reason,
        expires_at=timezone.now() + timedelta(hours=2),
    )

    # TODO: Send SMS to donor via Africa's Talking
    print(f"[DEV] SMS to {donor.user.phone}: {hospital.facility_name} needs your help. "
          f"Reply YES to share your contact or NO to decline.")

    return Response(
        {
            "message": "Contact request initiated",
            "request_id": contact_request.id,
            "status": "pending_donor_response",
            "expires_at": contact_request.expires_at,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@hospital_member_required
def list_contact_requests(request):
    hospital = get_hospital(request.user)
    if not hospital:
        return Response({"error": True, "message": "Hospital not found."}, status=404)

    requests_qs = ContactRequest.objects.filter(
        hospital=hospital
    ).select_related("donor__user")

    serializer = ContactRequestSerializer(requests_qs, many=True)
    return Response({"count": requests_qs.count(), "results": serializer.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def respond_to_contact_request(request, request_id):
    """Donor accepts or declines a contact request."""
    if request.user.role != User.Role.DONOR:
        return Response(
            {"error": True, "message": "Only donors can respond to contact requests."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        contact_request = ContactRequest.objects.get(
            id=request_id, donor__user=request.user
        )
    except ContactRequest.DoesNotExist:
        return Response({"error": True, "message": "Request not found."}, status=404)

    if contact_request.is_expired:
        contact_request.status = ContactRequest.Status.EXPIRED
        contact_request.save(update_fields=["status"])
        return Response({"error": True, "message": "This request has expired."}, status=400)

    response_action = request.data.get("response")  # "accept" or "decline"

    if response_action == "accept":
        contact_request.status = ContactRequest.Status.ACCEPTED
        contact_request.responded_at = timezone.now()
        contact_request.save()

        # TODO: Send full donor contact details to hospital via SMS/email
        print(f"[DEV] Hospital {contact_request.hospital.facility_name} can now contact "
              f"{contact_request.donor.user.full_name} at {contact_request.donor.user.phone}")

        return Response({
            "message": "Contact request accepted. The hospital will be in touch.",
            "status": "accepted",
        })

    elif response_action == "decline":
        contact_request.status = ContactRequest.Status.DECLINED
        contact_request.responded_at = timezone.now()
        contact_request.save()
        return Response({"message": "Contact request declined.", "status": "declined"})

    return Response(
        {"error": True, "message": "response must be 'accept' or 'decline'."},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def donor_contact_requests(request):
    """Donor views all contact requests directed at them."""
    if request.user.role != User.Role.DONOR:
        return Response(
            {"error": True, "message": "Only donors can access this."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        donor_profile = request.user.donor_profile
    except Exception:
        return Response({"error": True, "message": "Donor profile not found."}, status=404)

    requests_qs = ContactRequest.objects.filter(
        donor=donor_profile
    ).select_related("hospital")

    data = []
    for cr in requests_qs:
        h = cr.hospital
        data.append({
            "request_id": cr.id,
            "hospital": {
                "id": h.id,
                "name": h.facility_name,
                "facility_type": h.facility_type,
                "county": h.county,
                "address": h.address,
                "phone": h.phone,
                "is_verified": h.approval_status == HospitalProfile.ApprovalStatus.APPROVED,
            },
            "reason": cr.reason,
            "status": cr.status,
            "requested_at": cr.requested_at,
            "expires_at": cr.expires_at,
        })

    return Response({"count": len(data), "results": data})