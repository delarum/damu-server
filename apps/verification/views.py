import base64

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.donors.models import DonorProfile
from .models import IdentityVerification
from .smile_identity import verify_identity, is_verified


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_id_documents(request):
    """
    Step 1 — Donor uploads ID documents and selfie.
    Triggers automated Smile Identity verification.
    """
    user = request.user

    if user.role != User.Role.DONOR:
        return Response(
            {"error": True, "message": "Only donors can submit identity documents."},
            status=status.HTTP_403_FORBIDDEN,
        )

    id_type   = request.data.get("id_type", "national_id")
    id_number = request.data.get("id_number", "")
    front     = request.FILES.get("front_image")
    back      = request.FILES.get("back_image")
    selfie    = request.FILES.get("selfie_image")

    if not all([front, selfie, id_number]):
        return Response(
            {"error": True, "message": "front_image, selfie_image, and id_number are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Create or update verification record
    verification, _ = IdentityVerification.objects.update_or_create(
        user=user,
        defaults={
            "id_type":      id_type,
            "id_number":    id_number,
            "front_image":  front,
            "back_image":   back,
            "selfie_image": selfie,
            "status":       IdentityVerification.Status.PENDING,
        },
    )

    # Encode images for Smile Identity
    front_b64  = base64.b64encode(front.read()).decode()
    selfie_b64 = base64.b64encode(selfie.read()).decode()

    try:
        result = verify_identity(
            id_image_base64=front_b64,
            selfie_base64=selfie_b64,
            id_type=id_type.upper(),
            id_number=id_number,
        )

        verification.provider_result = result
        verification.provider_ref    = result.get("SmileJobID", "")

        if is_verified(result):
            verification.status      = IdentityVerification.Status.APPROVED
            verification.reviewed_at = timezone.now()
            # Mark the user as verified
            user.is_verified = True
            user.save(update_fields=["is_verified"])
            # Mark donor profile as verified if it exists
            try:
                user.donor_profile.verification_status = DonorProfile.VerificationStatus.VERIFIED
                user.donor_profile.save(update_fields=["verification_status"])
            except DonorProfile.DoesNotExist:
                pass
        else:
            # Send to manual review queue
            verification.status = IdentityVerification.Status.MANUAL

        verification.save()

    except Exception as e:
        verification.status = IdentityVerification.Status.MANUAL
        verification.provider_result = {"error": str(e)}
        verification.save()

    return Response(
        {
            "message":             "Documents uploaded successfully",
            "verification_status": verification.status,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def verification_status(request):
    """Donor checks their verification status."""
    try:
        verification = request.user.verification
        return Response(
            {
                "status":          verification.status,
                "id_type":         verification.id_type,
                "submitted_at":    verification.submitted_at,
                "reviewed_at":     verification.reviewed_at,
                "rejection_reason": verification.rejection_reason,
            }
        )
    except IdentityVerification.DoesNotExist:
        return Response(
            {"status": "not_submitted", "message": "No verification documents submitted yet."}
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def manual_review_decision(request, verification_id):
    """DamuLink admin approves or rejects a manual review case."""
    if request.user.role != User.Role.ADMIN:
        return Response({"error": True, "message": "Admin access required."}, status=403)

    try:
        verification = IdentityVerification.objects.get(id=verification_id)
    except IdentityVerification.DoesNotExist:
        return Response({"error": True, "message": "Verification not found."}, status=404)

    decision = request.data.get("decision")  # "approve" or "reject"
    reason   = request.data.get("reason", "")

    if decision == "approve":
        verification.status      = IdentityVerification.Status.APPROVED
        verification.reviewed_at = timezone.now()
        verification.reviewed_by = request.user
        verification.save()

        verification.user.is_verified = True
        verification.user.save(update_fields=["is_verified"])

        try:
            verification.user.donor_profile.verification_status = DonorProfile.VerificationStatus.VERIFIED
            verification.user.donor_profile.save(update_fields=["verification_status"])
        except DonorProfile.DoesNotExist:
            pass

        return Response({"message": "Verification approved."})

    elif decision == "reject":
        verification.status           = IdentityVerification.Status.REJECTED
        verification.rejection_reason = reason
        verification.reviewed_at      = timezone.now()
        verification.reviewed_by      = request.user
        verification.save()

        try:
            verification.user.donor_profile.verification_status = DonorProfile.VerificationStatus.REJECTED
            verification.user.donor_profile.save(update_fields=["verification_status"])
        except DonorProfile.DoesNotExist:
            pass

        return Response({"message": "Verification rejected."})

    return Response(
        {"error": True, "message": "decision must be 'approve' or 'reject'."},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def manual_review_queue(request):
    """Admin views all pending manual review cases."""
    if request.user.role != User.Role.ADMIN:
        return Response({"error": True, "message": "Admin access required."}, status=403)

    pending = IdentityVerification.objects.filter(
        status=IdentityVerification.Status.MANUAL
    ).select_related("user")

    data = [
        {
            "id":           v.id,
            "user":         v.user.full_name,
            "phone":        v.user.phone,
            "id_type":      v.id_type,
            "id_number":    v.id_number,
            "submitted_at": v.submitted_at,
        }
        for v in pending
    ]
    return Response({"count": len(data), "results": data})