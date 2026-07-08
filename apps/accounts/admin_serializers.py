"""
Serializers for admin API endpoints.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import OTPVerification
from apps.hospitals.models import HospitalProfile
from apps.donors.models import DonorProfile
from apps.audit.models import AuditLog

User = get_user_model()


class AdminUserListSerializer(serializers.ModelSerializer):
    """List view for users - minimal PII for privacy."""
    hospital_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "role", "is_verified", 
            "is_active", "created_at", "hospital_name"
        ]
    
    def get_hospital_name(self, obj):
        if hasattr(obj, 'hospital_profile'):
            return obj.hospital_profile.facility_name
        return None


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """Detailed view for a single user - full access for superadmin."""
    hospital_profile = serializers.SerializerMethodField()
    donor_profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "phone", "role", "is_verified",
            "is_active", "is_staff", "national_id", "date_of_birth",
            "created_at", "updated_at", "hospital_profile", "donor_profile"
        ]
    
    def get_hospital_profile(self, obj):
        if hasattr(obj, 'hospital_profile'):
            return {
                "id": obj.hospital_profile.id,
                "facility_name": obj.hospital_profile.facility_name,
                "facility_type": obj.hospital_profile.facility_type,
                "approval_status": obj.hospital_profile.approval_status,
                "county": obj.hospital_profile.county,
            }
        return None
    
    def get_donor_profile(self, obj):
        if hasattr(obj, 'donor_profile'):
            return {
                "id": obj.donor_profile.id,
                "blood_type": obj.donor_profile.blood_type,
                "is_available": obj.donor_profile.is_available,
                "total_donations": obj.donor_profile.total_donations,
            }
        return None


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Update user fields - for superadmin actions."""
    
    class Meta:
        model = User
        fields = ["is_verified", "is_active", "is_staff", "role"]
    
    def validate_role(self, value):
        # Prevent creating more superadmins through API
        if value == User.Role.ADMIN:
            raise serializers.ValidationError("Cannot assign ADMIN role through this endpoint.")
        return value


class AdminHospitalListSerializer(serializers.ModelSerializer):
    """List hospitals for admin."""
    admin_email = serializers.EmailField(source='admin.email', read_only=True)
    admin_name = serializers.CharField(source='admin.full_name', read_only=True)
    is_approved = serializers.SerializerMethodField()

    class Meta:
        model = HospitalProfile
        fields = [
            "id", "facility_name", "facility_type", "license_number",
            "county", "approval_status", "is_approved", "subscription_tier",
            "subscription_status", "admin_email", "admin_name",
            "created_at", "approved_at"
        ]

    def get_is_approved(self, obj):
        return obj.approval_status == HospitalProfile.ApprovalStatus.APPROVED


class AdminHospitalDetailSerializer(serializers.ModelSerializer):
    """Detailed hospital view for admin."""
    admin = AdminUserListSerializer(read_only=True)
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = HospitalProfile
        fields = [
            "id", "facility_name", "facility_type", "license_number",
            "year_established", "address", "county", "lat", "lng",
            "phone", "email", "website", "approval_status",
            "rejection_reason", "approved_at", "approved_by",
            "subscription_tier", "subscription_status",
            "subscription_expires", "search_quota", "search_limit",
            "admin", "documents_count", "created_at", "updated_at"
        ]
    
    def get_documents_count(self, obj):
        return obj.documents.count()


class AdminHospitalApprovalSerializer(serializers.ModelSerializer):
    """Approve/reject hospital."""
    class Meta:
        model = HospitalProfile
        fields = ["approval_status", "rejection_reason"]
    
    def validate(self, data):
        if data.get('approval_status') == HospitalProfile.ApprovalStatus.REJECTED:
            if not data.get('rejection_reason'):
                raise serializers.ValidationError(
                    {"rejection_reason": "Rejection reason is required when rejecting."}
                )
        return data


class AdminOTPListSerializer(serializers.ModelSerializer):
    """List OTPs - never show raw codes, only status."""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = OTPVerification
        fields = [
            "id", "user_email", "purpose", "is_used",
            "created_at", "expires_at"
        ]


class AdminAuditLogSerializer(serializers.ModelSerializer):
    """Audit log entries for admin review."""
    actor_email = serializers.EmailField(source='actor.email', read_only=True)
    actor_name = serializers.CharField(source='actor.full_name', read_only=True)
    target_email = serializers.EmailField(source='target_user.email', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            "id", "actor_email", "actor_name", "actor_role",
            "action", "target_email", "ip_address", "endpoint",
            "method", "metadata", "timestamp"
        ]


class AdminStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_donors = serializers.IntegerField()
    total_hospitals = serializers.IntegerField()
    pending_hospitals = serializers.IntegerField()
    active_hospitals = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    total_matches = serializers.IntegerField()
    total_donations = serializers.IntegerField()
    recent_registrations = serializers.IntegerField()
    recent_logins = serializers.IntegerField()