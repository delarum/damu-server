"""
Admin API URL patterns.
Separates Platform Superadmin from Hospital Admin endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .admin_views import (
    AdminUserViewSet,
    AdminHospitalViewSet,
    AdminAuditLogViewSet,
    AdminStatsView,
    HospitalAdminViewSet,
)

# ============================================================================
# PLATFORM SUPERADMIN ROUTES
# ============================================================================

superadmin_router = DefaultRouter()
superadmin_router.register(r'users', AdminUserViewSet, basename='admin-users')
superadmin_router.register(r'hospitals', AdminHospitalViewSet, basename='admin-hospitals')
superadmin_router.register(r'audit-logs', AdminAuditLogViewSet, basename='admin-audit-logs')
superadmin_router.register(r'stats', AdminStatsView, basename='admin-stats')

# ============================================================================
# HOSPITAL ADMIN ROUTES
# ============================================================================

hospital_admin_router = DefaultRouter()
hospital_admin_router.register(r'dashboard', HospitalAdminViewSet, basename='hospital-admin-dashboard')

# ============================================================================
# URL PATTERNS
# ============================================================================

urlpatterns = [
    # Platform Superadmin endpoints
    path('superadmin/', include(superadmin_router.urls)),
    
    # Hospital Admin endpoints
    path('hospital-admin/', include(hospital_admin_router.urls)),
]