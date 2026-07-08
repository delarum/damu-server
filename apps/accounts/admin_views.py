"""
Admin API views for Platform Superadmin and Hospital Admin.
"""
from django.utils import timezone
from django.db.models import Count, Q
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import User, OTPVerification
from .admin_serializers import (
    AdminUserListSerializer,
    AdminUserDetailSerializer,
    AdminUserUpdateSerializer,
    AdminHospitalListSerializer,
    AdminHospitalDetailSerializer,
    AdminHospitalApprovalSerializer,
    AdminOTPListSerializer,
    AdminAuditLogSerializer,
    AdminStatsSerializer,
)
from .permissions import (
    IsPlatformSuperadmin,
    IsHospitalAdmin,
    CanManageUsers,
    CanApproveHospitals,
    CanViewAuditLogs,
)
from apps.hospitals.models import HospitalProfile
from apps.donors.models import DonorProfile
from apps.matching.models import ContactRequest
from apps.audit.models import AuditLog
from apps.gamification.models import Badge, DonationRecord


# ============================================================================
# PLATFORM SUPERADMIN VIEWSETS
# ============================================================================

class AdminUserViewSet(viewsets.ModelViewSet):
    """
    Platform superadmin user management.
    Full CRUD on all users with audit logging.
    """
    permission_classes = [IsAuthenticated, CanManageUsers]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_verified', 'is_active']
    search_fields = ['email', 'full_name', 'phone', 'national_id']
    ordering_fields = ['created_at', 'full_name', 'email']
    ordering = ['-created_at']

    def get_queryset(self):
        return User.objects.all().select_related('hospital_profile', 'donor_profile')

    def get_serializer_class(self):
        if self.action == 'list':
            return AdminUserListSerializer
        elif self.action in ['update', 'partial_update']:
            return AdminUserUpdateSerializer
        return AdminUserDetailSerializer

    def perform_update(self, serializer):
        """Log admin user updates."""
        user = serializer.save()
        
        # Log the action
        AuditLog.objects.create(
            actor=self.request.user,
            actor_role=self.request.user.role,
            action=AuditLog.Action.ADMIN_ACTION,
            target_user=user,
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            endpoint=self.request.path,
            method=self.request.method,
            metadata={
                "action": "user_update",
                "updated_fields": list(serializer.validated_data.keys()),
                "user_id": user.id,
            }
        )

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Admin-initiated password reset."""
        user = self.get_object()
        
        # Generate temporary password
        import secrets
        import string
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        user.set_password(temp_password)
        user.save()
        
        # Send email notification
        from apps.notifications.services import send_email
        subject = "Your DamuLink password has been reset"
        message = (
            f"Your password has been reset by an administrator.\n"
            f"Your temporary password is: {temp_password}\n"
            f"Please log in and change your password immediately.\n"
            f"If you did not request this, please contact support immediately."
        )
        send_email(user, subject, message)
        
        # Log the action
        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action=AuditLog.Action.ADMIN_ACTION,
            target_user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            endpoint=request.path,
            method=request.method,
            metadata={
                "action": "password_reset",
                "user_id": user.id,
                "user_email": user.email,
            }
        )
        
        return Response({
            "message": "Password reset successfully",
            "temporary_password": temp_password
        })

    @action(detail=True, methods=['get'])
    def otp_history(self, request, pk=None):
        """View OTP history for a user (status only, never raw codes)."""
        user = self.get_object()
        otps = OTPVerification.objects.filter(user=user).order_by('-created_at')[:50]
        serializer = AdminOTPListSerializer(otps, many=True)
        
        # Log the action
        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action=AuditLog.Action.ADMIN_ACTION,
            target_user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            endpoint=request.path,
            method=request.method,
            metadata={
                "action": "view_otp_history",
                "user_id": user.id,
            }
        )
        
        return Response(serializer.data)


class AdminHospitalViewSet(viewsets.ModelViewSet):
    """
    Platform superadmin hospital management.
    Approve/reject hospitals, view all hospitals.
    """
    permission_classes = [IsAuthenticated, CanApproveHospitals]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['approval_status', 'subscription_tier', 'facility_type', 'county']
    search_fields = ['facility_name', 'license_number', 'county']
    ordering_fields = ['created_at', 'facility_name', 'approval_status']
    ordering = ['-created_at']

    def get_queryset(self):
        return HospitalProfile.objects.all().select_related('admin')

    def get_serializer_class(self):
        if self.action == 'list':
            return AdminHospitalListSerializer
        elif self.action in ['approve', 'reject']:
            return AdminHospitalApprovalSerializer
        return AdminHospitalDetailSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a hospital."""
        hospital = self.get_object()
        serializer = AdminHospitalApprovalSerializer(hospital, data=request.data)
        
        if serializer.is_valid():
            hospital = serializer.save(
                approved_by=request.user,
                approved_at=timezone.now()
            )
            
            # Send notification
            from apps.notifications.services import notify_hospital_approved
            notify_hospital_approved(hospital.admin, hospital.facility_name)
            
            # Log the action
            AuditLog.objects.create(
                actor=request.user,
                actor_role=request.user.role,
                action=AuditLog.Action.HOSPITAL_APPROVE,
                target_user=hospital.admin,
                ip_address=request.META.get('REMOTE_ADDR'),
                endpoint=request.path,
                method=request.method,
                metadata={
                    "action": "hospital_approve",
                    "hospital_id": hospital.id,
                    "facility_name": hospital.facility_name,
                }
            )
            
            return Response({
                "message": f"{hospital.facility_name} has been approved",
                "hospital": AdminHospitalDetailSerializer(hospital).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def grant_subscription(self, request, pk=None):
      """Manually grant a subscription without payment (admin override)."""
      hospital = self.get_object()
    
      tier = request.data.get('subscription_tier', HospitalProfile.SubscriptionTier.PROFESSIONAL)
      duration_days = request.data.get('duration_days', 365)
    
      hospital.subscription_tier = tier
      hospital.subscription_status = 'active'
      hospital.subscription_expires = timezone.now() + timezone.timedelta(days=duration_days)
      hospital.save()
    
    # Log the action
      AuditLog.objects.create(
        actor=request.user,
        actor_role=request.user.role,
        action=AuditLog.Action.ADMIN_ACTION,
        target_user=hospital.admin,
        ip_address=request.META.get('REMOTE_ADDR'),
        endpoint=request.path,
        method=request.method,
        metadata={
            "action": "grant_subscription",
            "hospital_id": hospital.id,
            "facility_name": hospital.facility_name,
            "tier": tier,
            "duration_days": duration_days,
            "granted_by": request.user.email,
        }
    )
    
      return Response({
        "message": f"{hospital.facility_name} granted {tier} subscription for {duration_days} days",
        "hospital": AdminHospitalDetailSerializer(hospital).data
    })

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a hospital."""
        hospital = self.get_object()
        serializer = AdminHospitalApprovalSerializer(hospital, data=request.data)
        
        if serializer.is_valid():
            hospital = serializer.save()
            
            # Log the action
            AuditLog.objects.create(
                actor=request.user,
                actor_role=request.user.role,
                action=AuditLog.Action.HOSPITAL_REJECT,
                target_user=hospital.admin,
                ip_address=request.META.get('REMOTE_ADDR'),
                endpoint=request.path,
                method=request.method,
                metadata={
                    "action": "hospital_reject",
                    "hospital_id": hospital.id,
                    "facility_name": hospital.facility_name,
                    "reason": hospital.rejection_reason,
                }
            )
            
            return Response({
                "message": f"{hospital.facility_name} has been rejected",
                "hospital": AdminHospitalDetailSerializer(hospital).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend a hospital's ability to post requests."""
        hospital = self.get_object()
        hospital.approval_status = HospitalProfile.ApprovalStatus.SUSPENDED
        hospital.save()
        
        # Log the action
        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action=AuditLog.Action.ADMIN_ACTION,
            target_user=hospital.admin,
            ip_address=request.META.get('REMOTE_ADDR'),
            endpoint=request.path,
            method=request.method,
            metadata={
                "action": "hospital_suspend",
                "hospital_id": hospital.id,
                "facility_name": hospital.facility_name,
            }
        )
        
        return Response({"message": f"{hospital.facility_name} has been suspended"})

    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """Reactivate a suspended hospital."""
        hospital = self.get_object()
        hospital.approval_status = HospitalProfile.ApprovalStatus.APPROVED
        hospital.save()
        
        # Log the action
        AuditLog.objects.create(
            actor=request.user,
            actor_role=request.user.role,
            action=AuditLog.Action.ADMIN_ACTION,
            target_user=hospital.admin,
            ip_address=request.META.get('REMOTE_ADDR'),
            endpoint=request.path,
            method=request.method,
            metadata={
                "action": "hospital_reactivate",
                "hospital_id": hospital.id,
                "facility_name": hospital.facility_name,
            }
        )
        
        return Response({"message": f"{hospital.facility_name} has been reactivated"})


class AdminAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View audit logs - read-only, immutable.
    """
    permission_classes = [IsAuthenticated, CanViewAuditLogs]
    serializer_class = AdminAuditLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'actor_role']
    search_fields = ['actor__email', 'actor__full_name', 'action', 'endpoint']
    ordering_fields = ['timestamp', 'action']
    ordering = ['-timestamp']

    def get_queryset(self):
        return AuditLog.objects.all().select_related('actor', 'target_user')


class AdminStatsView(viewsets.ViewSet):
    """
    Platform statistics dashboard.
    """
    permission_classes = [IsAuthenticated, IsPlatformSuperadmin]

    def list(self, request):
        """Get platform statistics."""
        now = timezone.now()
        last_30_days = now - timezone.timedelta(days=30)
        
        stats = {
            "total_users": User.objects.count(),
            "total_donors": User.objects.filter(role=User.Role.DONOR).count(),
            "total_hospitals": User.objects.filter(role=User.Role.HOSPITAL_ADMIN).count(),
            "pending_hospitals": HospitalProfile.objects.filter(approval_status='pending').count(),
            "active_hospitals": HospitalProfile.objects.filter(approval_status='approved').count(),
            "total_matches": ContactRequest.objects.count(),
            "total_donations": DonorProfile.objects.aggregate(
                total=Count('donations')
            )['total'] or 0,
            "recent_registrations": User.objects.filter(created_at__gte=last_30_days).count(),
            "recent_logins": AuditLog.objects.filter(
                action=AuditLog.Action.LOGIN,
                timestamp__gte=last_30_days
            ).count(),
        }
        
        serializer = AdminStatsSerializer(stats)
        return Response(serializer.data)


# ============================================================================
# HOSPITAL ADMIN VIEWSETS
# ============================================================================

class HospitalAdminViewSet(viewsets.ViewSet):
    """
    Hospital admin dashboard - scoped to their hospital only.
    """
    permission_classes = [IsAuthenticated, IsHospitalAdmin]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Hospital admin dashboard stats."""
        hospital = request.user.hospital_profile
        
        # Get stats for this hospital only
        stats = {
            "facility_name": hospital.facility_name,
            "approval_status": hospital.approval_status,
            "subscription_tier": hospital.subscription_tier,
            "searches_remaining": hospital.searches_remaining,
            "total_requests": ContactRequest.objects.filter(hospital=hospital).count(),
            "pending_matches": ContactRequest.objects.filter(
                hospital=hospital,
                status='pending'
            ).count(),
            "completed_donations": DonationRecord.objects.filter(
                request__hospital=hospital,
                status='completed'
            ).count() if hasattr(DonationRecord, 'objects') else 0,
        }
        
        return Response(stats)

    @action(detail=False, methods=['get'])
    def staff(self, request):
        """List staff members for this hospital."""
        hospital = request.user.hospital_profile
        staff_members = hospital.staff.all().select_related('user')
        
        data = []
        for staff in staff_members:
            data.append({
                "id": staff.id,
                "user_id": staff.user.id,
                "full_name": staff.user.full_name,
                "email": staff.user.email,
                "added_at": staff.added_at,
            })
        
        return Response(data)