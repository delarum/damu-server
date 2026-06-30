from rest_framework import serializers
from .models import DonorProfile


class DonorProfileSerializer(serializers.ModelSerializer):
    """Full profile — for the donor themselves."""
    full_name   = serializers.CharField(source="user.full_name", read_only=True)
    phone       = serializers.CharField(source="user.phone", read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model  = DonorProfile
        fields = [
            "id", "full_name", "phone",
            "blood_type", "donor_type", "organs_pledged",
            "gender", "height_cm", "weight_kg",
            "county", "sub_county", "town",
            "preferred_contact_method",
            "insurance_provider",
            "availability_status", "is_available", "cooldown_until",
            "verification_status",
            "emergency_contact_name", "emergency_contact_phone",
            "last_donation_date",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "verification_status", "cooldown_until",
            "created_at", "updated_at",
        ]

    def validate_organs_pledged(self, value):
        valid = DonorProfile.ORGAN_CHOICES
        for organ in value:
            if organ not in valid:
                raise serializers.ValidationError(
                    f"'{organ}' is not a valid organ. Choose from: {valid}"
                )
        return value

    def validate(self, data):
        donor_type = data.get("donor_type", getattr(self.instance, "donor_type", None))
        organs     = data.get("organs_pledged", getattr(self.instance, "organs_pledged", []))

        if donor_type in ["organ", "both"] and not organs:
            raise serializers.ValidationError(
                {"organs_pledged": "Please specify at least one organ to pledge."}
            )
        return data


class DonorProfileCreateSerializer(DonorProfileSerializer):
    """Used on POST — includes location fields."""
    class Meta(DonorProfileSerializer.Meta):
        fields = DonorProfileSerializer.Meta.fields + ["address", "lat", "lng"]


class DonorPublicSerializer(serializers.ModelSerializer):
    """Restricted view shown to hospitals during search — no PII."""
    name         = serializers.SerializerMethodField()
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model  = DonorProfile
        fields = [
            "id", "name", "blood_type", "donor_type",
            "organs_pledged", "preferred_contact_method",
            "last_donation_date", "is_available",
            "county", "town",
        ]

    def get_name(self, obj):
        # Only first name + last initial e.g. "James M."
        parts = obj.user.full_name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[-1][0]}."
        return parts[0] if parts else "Donor"
