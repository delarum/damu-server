from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.accounts.models import User
from apps.donors.models import DonorProfile
from .models import ThirdPartyApplication


@api_view(["POST"])
@permission_classes([AllowAny])
def submit_application(request):
    """Any organisation submits a third-party data access application."""
    required = ["org_name", "org_type", "purpose", "data_requested",
                "contact_name", "contact_email"]
    missing  = [f for f in required if not request.data.get(f)]
    if missing:
        return Response(
            {"error": True, "message": f"Missing required fields: {missing}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    app = ThirdPartyApplication.objects.create(
        org_name        = request.data.get("org_name"),
        org_type        = request.data.get("org_type", "other"),
        country         = request.data.get("country", "Kenya"),
        website         = request.data.get("website", ""),
        registration_no = request.data.get("registration_no", ""),
        purpose         = request.data.get("purpose"),
        data_requested  = request.data.get("data_requested"),
        duration_months = int(request.data.get("duration_months", 6)),
        dpa_signed      = bool(request.data.get("dpa_signed", False)),
        nda_signed      = bool(request.data.get("nda_signed", False)),
        ethics_approved = bool(request.data.get("ethics_approved", False)),
        contact_name    = request.data.get("contact_name"),
        contact_email   = request.data.get("contact_email"),
        contact_phone   = request.data.get("contact_phone", ""),
        dpo_name        = request.data.get("dpo_name", ""),
        dpo_email       = request.data.get("dpo_email", ""),
    )

    return Response(
        {
            "message":        "Application submitted successfully. We will review within 5-10 business days.",
            "application_id": app.id,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_applications(request):
    """Admin views all third-party applications."""
    if request.user.role != User.Role.ADMIN:
        return Response({"error": True, "message": "Admin access required."}, status=403)

    apps = ThirdPartyApplication.objects.all().order_by("-created_at")
    status_filter = request.query_params.get("status")
    if status_filter:
        apps = apps.filter(status=status_filter)

    data = [
        {
            "id":          a.id,
            "org_name":    a.org_name,
            "org_type":    a.org_type,
            "purpose":     a.purpose[:100],
            "status":      a.status,
            "created_at":  a.created_at,
            "dpa_signed":  a.dpa_signed,
            "nda_signed":  a.nda_signed,
        }
        for a in apps
    ]
    return Response({"count": len(data), "results": data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def review_application(request, app_id):
    """Admin approves or rejects a third-party application."""
    if request.user.role != User.Role.ADMIN:
        return Response({"error": True, "message": "Admin access required."}, status=403)

    try:
        app = ThirdPartyApplication.objects.get(id=app_id)
    except ThirdPartyApplication.DoesNotExist:
        return Response({"error": True, "message": "Application not found."}, status=404)

    decision = request.data.get("decision")
    reason   = request.data.get("reason", "")

    if decision == "approve":
        app.status       = ThirdPartyApplication.Status.APPROVED
        app.approved_at  = timezone.now()
        app.reviewed_by  = request.user
        app.access_expires = timezone.now() + timedelta(days=30 * app.duration_months)
        app.save()
        return Response(
            {
                "message":       "Application approved.",
                "access_expires": app.access_expires,
            }
        )

    elif decision == "reject":
        app.status           = ThirdPartyApplication.Status.REJECTED
        app.rejection_reason = reason
        app.reviewed_by      = request.user
        app.save()
        return Response({"message": "Application rejected."})

    elif decision == "revoke":
        app.status      = ThirdPartyApplication.Status.REVOKED
        app.reviewed_by = request.user
        app.save()
        return Response({"message": "Access revoked."})

    return Response(
        {"error": True, "message": "decision must be 'approve', 'reject', or 'revoke'."},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def aggregate_data(request):
    """
    Approved third-party researchers access anonymised aggregate data only.
    No PII — county-level counts, blood type distributions, totals.
    """
    if request.user.role != User.Role.THIRD_PARTY:
        return Response(
            {"error": True, "message": "Third-party researcher access required."},
            status=403,
        )

    try:
        app = request.user.third_party_profile
        if app.status != ThirdPartyApplication.Status.APPROVED:
            return Response({"error": True, "message": "Your application is not approved."}, status=403)
        if app.access_expires and timezone.now() > app.access_expires:
            return Response({"error": True, "message": "Your access has expired."}, status=403)
    except ThirdPartyApplication.DoesNotExist:
        return Response({"error": True, "message": "No approved application found."}, status=403)

    from django.db.models import Count

    # Aggregate — no PII exposed
    blood_distribution = (
        DonorProfile.objects.values("blood_type")
        .annotate(count=Count("id"))
        .order_by("blood_type")
    )

    county_distribution = (
        DonorProfile.objects.values("county")
        .annotate(count=Count("id"))
        .order_by("-count")[:20]
    )

    total_donors = DonorProfile.objects.count()
    verified_donors = DonorProfile.objects.filter(verification_status="verified").count()

    return Response(
        {
            "total_donors":        total_donors,
            "verified_donors":     verified_donors,
            "blood_distribution":  list(blood_distribution),
            "county_distribution": list(county_distribution),
            "note":                "All data is anonymised and aggregated. No personally identifiable information is included.",
        }
    )