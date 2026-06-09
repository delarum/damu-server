from django.utils import timezone
from rest_framework import serializers
from .models import HospitalProfile, HospitalDocument, HospitalStaff


class HospitalProfileSerializer(serializers.ModelSerializer):
    admin_name           = serializers.CharField(source="admin.full_name", read_only=True)
    admin_phone          = serializers.CharField(source="admin.phone", read_only=True)
    is_active_subscriber = serializers.BooleanField(read_only=True)
    searches_remaining   = serializers.IntegerField(read_only=True)

    class Meta:
        model  = HospitalProfile
        fields = [
            "id", "admin_name", "admin_phone",
            "facility_name", "facility_type", "license_number", "year_established",
            "address", "county", "lat", "lng",
            "phone", "email", "website",
            "approval_status", "rejection_reason",
            "subscription_tier", "subscription_status", "subscription_expires",
            "is_active_subscriber", "searches_remaining",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "approval_status", "rejection_reason",
            "subscription_status", "subscription_expires",
            "created_at", "updated_at",
        ]


class HospitalProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = HospitalProfile
        fields = [
            "facility_name", "facility_type", "license_number", "year_established",
            "address", "county", "lat", "lng",
            "phone", "email", "website",
        ]

    def validate_license_number(self, value):
        if HospitalProfile.objects.filter(license_number=value).exists():
            raise serializers.ValidationError("A hospital with this license number already exists.")
        return value


class HospitalPublicSerializer(serializers.ModelSerializer):
    """Minimal view for donor-facing hospital listings."""
    class Meta:
        model  = HospitalProfile
        fields = ["id", "facility_name", "facility_type", "county", "address", "lat", "lng", "phone"]


class HospitalDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = HospitalDocument
        fields = ["id", "doc_type", "file", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]


class HospitalStaffSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    phone     = serializers.CharField(source="user.phone", read_only=True)

    class Meta:
        model  = HospitalStaff
        fields = ["id", "full_name", "phone", "added_at"]
        read_only_fields = ["id", "added_at"]


class SubscriptionSerializer(serializers.Serializer):
    tier = serializers.ChoiceField(choices=HospitalProfile.SubscriptionTier.choices)