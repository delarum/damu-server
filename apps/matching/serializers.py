from rest_framework import serializers
from .models import ContactRequest
from apps.donors.serializers import DonorPublicSerializer


class ContactRequestCreateSerializer(serializers.Serializer):
    donor_id = serializers.IntegerField()
    reason   = serializers.CharField(max_length=500)


class ContactRequestSerializer(serializers.ModelSerializer):
    donor_name    = serializers.SerializerMethodField()
    donor_phone   = serializers.SerializerMethodField()
    hospital_name = serializers.CharField(source="hospital.facility_name", read_only=True)
    is_expired    = serializers.BooleanField(read_only=True)

    class Meta:
        model  = ContactRequest
        fields = [
            "id", "hospital_name", "donor_name", "donor_phone",
            "reason", "status", "is_expired",
            "requested_at", "responded_at", "expires_at",
        ]

    def get_donor_name(self, obj):
        full_name = obj.donor.user.full_name.strip()
        if obj.status == ContactRequest.Status.ACCEPTED:
            # Donor has consented — show full name.
            return full_name
        parts = full_name.split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[-1][0]}."
        return parts[0] if parts else "Donor"

    def get_donor_phone(self, obj):
        # Only reveal contact details once the donor has explicitly accepted.
        if obj.status == ContactRequest.Status.ACCEPTED:
            return obj.donor.user.phone
        return None

class DonorSearchResultSerializer(serializers.Serializer):
    """What hospitals see in search results — restricted view, no PII."""
    donor_id           = serializers.IntegerField(source="id")
    name               = serializers.SerializerMethodField()
    blood_type         = serializers.CharField()
    distance_km        = serializers.FloatField()
    last_donation_date = serializers.DateField()
    contact_preference = serializers.CharField(source="preferred_contact_method")
    is_available       = serializers.BooleanField()
    county             = serializers.CharField()
    town               = serializers.CharField()
    insurance_provider = serializers.CharField()

    def get_name(self, obj):
        parts = obj.user.full_name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[-1][0]}."
        return parts[0] if parts else "Donor"