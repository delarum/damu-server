"""
Comprehensive permission system for DamuLink admin roles.
Separates Platform Superadmin from Hospital Admin with proper scoping.
"""
from rest_framework import permissions
from apps.accounts.models import User


class IsPlatformSuperadmin(permissions.BasePermission):
    """
    Platform superadmin (DamuLink internal team).
    Full access to all platform features.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
            and request.user.is_staff
        )


class IsHospitalAdmin(permissions.BasePermission):
    """
    Hospital admin (client-side).
    Scoped to their own hospital only.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.HOSPITAL_ADMIN
            and hasattr(request.user, 'hospital_profile')
            and request.user.hospital_profile.approval_status == 'approved'
        )


class IsHospitalStaff(permissions.BasePermission):
    """
    Hospital staff member.
    Limited access based on staff role.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.HOSPITAL_STAFF
            and hasattr(request.user, 'hospital_staff')
        )


class IsDonor(permissions.BasePermission):
    """Donor role."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.DONOR


class IsVerifiedUser(permissions.BasePermission):
    """Any verified user."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_verified


class IsOwnerOrSuperadmin(permissions.BasePermission):
    """
    Object-level permission: allow access if user is the owner or platform superadmin.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Platform superadmin has full access
        if request.user.role == User.Role.ADMIN and request.user.is_staff:
            return True
        
        # Check if user owns the object
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'admin'):
            return obj.admin == request.user
        
        return False


class IsHospitalScoped(permissions.BasePermission):
    """
    Ensures hospital admin/staff can only access their own hospital's data.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Platform superadmin has full access
        if request.user.role == User.Role.ADMIN and request.user.is_staff:
            return True
        
        # Hospital admin/staff can only access their own hospital
        if hasattr(request.user, 'hospital_profile'):
            user_hospital = request.user.hospital_profile
            if hasattr(obj, 'hospital'):
                return obj.hospital == user_hospital
            elif hasattr(obj, 'hospital_profile'):
                return obj == user_hospital
        
        return False


class CanViewAuditLogs(permissions.BasePermission):
    """Only platform superadmins can view audit logs."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
            and request.user.is_staff
        )


class CanManageUsers(permissions.BasePermission):
    """Only platform superadmins can manage users."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
            and request.user.is_staff
        )


class CanApproveHospitals(permissions.BasePermission):
    """Only platform superadmins can approve/reject hospitals."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
            and request.user.is_staff
        )


class CanManagePayments(permissions.BasePermission):
    """Only platform superadmins can manage payments/refunds."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
            and request.user.is_staff
        )


class CanManageGamification(permissions.BasePermission):
    """Only platform superadmins can manage gamification settings."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
            and request.user.is_staff
        )


class ReadOnly(permissions.BasePermission):
    """Read-only access for authenticated users."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.method in permissions.SAFE_METHODS