# DamuLink Admin Roles & Permissions System

## Overview

DamuLink implements a comprehensive role-based access control (RBAC) system with strict separation between **Platform Superadmin** (DamuLink internal team) and **Hospital Admin** (client-side). This document outlines the complete architecture, permissions, and API endpoints.

---

## Table of Contents

1. [Role Definitions](#role-definitions)
2. [Permission Architecture](#permission-architecture)
3. [API Endpoints](#api-endpoints)
4. [Security Features](#security-features)
5. [Implementation Details](#implementation-details)
6. [Frontend Integration](#frontend-integration)

---

## Role Definitions

### 1. Platform Superadmin (ADMIN)

**Highest privilege role** - DamuLink internal team only.

**Capabilities:**
- Full access to all platform features
- Manage all users (view, update, suspend, reset passwords)
- Approve/reject hospital registrations
- View all hospitals and their data
- Access complete audit logs (immutable)
- View platform statistics and analytics
- Manage payments and issue refunds
- Override matching algorithm parameters
- Manage gamification settings
- View verification logs and override failed verifications
- Access USSD session logs
- View notification delivery logs

**Security Requirements:**
- Must have `is_staff=True`
- Separate rate limiting for admin logins
- All actions are fully audited
- Cannot be created via API (manual creation only)

### 2. Hospital Admin (HOSPITAL_ADMIN)

**Client-side role** - strictly scoped to their own hospital.

**Capabilities:**
- View their hospital's dashboard
- Create/manage blood/organ requests for their hospital only
- View donor matches for their requests only
- View their hospital's request history and fulfillment stats
- Manage sub-users within their hospital
- View their payment/billing history

**Restrictions:**
- Cannot see other hospitals' data
- Cannot access platform-wide analytics
- Cannot touch gamification/points system
- Cannot see full donor PII until match is confirmed
- Hospital must be `approval_status='approved'`

### 3. Hospital Staff (HOSPITAL_STAFF)

**Limited access** within hospital context.

**Capabilities:**
- View hospital dashboard (read-only)
- Assist with match management
- Limited based on staff role configuration

**Restrictions:**
- Must be linked to a hospital via `HospitalStaff` model
- Cannot approve/reject requests
- Cannot modify hospital settings

### 4. Donor (DONOR)

**Standard user** - blood/organ donor.

**Capabilities:**
- Manage own profile
- Search for hospitals
- Respond to match requests
- View donation history
- Earn and redeem gamification points

**Restrictions:**
- Cannot access admin features
- Cannot see other donors' full PII

---

## Permission Architecture

### Permission Classes

All permission classes are located in `apps/accounts/permissions.py`:

```python
# Platform-level permissions
IsPlatformSuperadmin     # Full platform access
CanManageUsers           # User CRUD operations
CanApproveHospitals      # Hospital approval/rejection
CanViewAuditLogs         # Read-only audit log access
CanManagePayments        # Payment/refund management
CanManageGamification    # Points/badge management

# Hospital-level permissions
IsHospitalAdmin          # Hospital admin access
IsHospitalStaff          # Hospital staff access
IsHospitalScoped         # Object-level hospital scoping

# General permissions
IsDonor                  # Donor role check
IsVerifiedUser           # Any verified user
IsOwnerOrSuperadmin      # Object ownership or superadmin
ReadOnly                 # Safe methods only
```

### Permission Flow

```
Request → Authentication (JWT) → Permission Check → View Action → Audit Log
```

**Example Flow:**
1. User authenticates with JWT token
2. Permission class checks `request.user.role` and `is_staff` flag
3. For object-level actions, `IsHospitalScoped` ensures data isolation
4. All admin actions create immutable `AuditLog` entries

---

## API Endpoints

### Base URL Structure

```
/api/v1/accounts/
├── register/donor/          # Public - donor registration
├── register/hospital/       # Public - hospital registration
├── verify-otp/              # Public - OTP verification
├── resend-otp/              # Public - resend OTP
├── login/                   # Public - JWT login
├── token/refresh/           # Public - JWT refresh
├── logout/                  # Authenticated - blacklist token
├── me/                      # Authenticated - current user
├── change-password/         # Authenticated - change password
│
├── superadmin/              # ⚠️ PLATFORM SUPERADMIN ONLY
│   ├── users/               # CRUD on all users
│   │   ├── GET /           # List users (filterable)
│   │   ├── GET /{id}/      # User details
│   │   ├── PATCH /{id}/    # Update user
│   │   ├── POST /{id}/reset_password/  # Reset password
│   │   └── GET /{id}/otp_history/      # View OTP history
│   │
│   ├── hospitals/           # Hospital management
│   │   ├── GET /           # List hospitals
│   │   ├── GET /{id}/      # Hospital details
│   │   ├── POST /{id}/approve/    # Approve hospital
│   │   ├── POST /{id}/reject/     # Reject hospital
│   │   ├── POST /{id}/suspend/    # Suspend hospital
│   │   └── POST /{id}/reactivate/ # Reactivate hospital
│   │
│   ├── audit-logs/          # Read-only audit trail
│   │   ├── GET /           # List audit logs
│   │   └── GET /{id}/      # Audit log details
│   │
│   └── stats/               # Platform statistics
│       └── GET /           # Dashboard stats
│
└── hospital-admin/          # ⚠️ HOSPITAL ADMIN ONLY
    └── dashboard/
        ├── GET /dashboard/  # Hospital stats
        └── GET /staff/      # List staff members
```

### Authentication

All admin endpoints require:
- Valid JWT token in `Authorization: Bearer <token>` header
- User role must match permission requirements
- For hospital admin: hospital must be approved

---

## Security Features

### 1. **Data Isolation**

Hospital admins can **only** access their own hospital's data:

```python
class IsHospitalScoped(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == User.Role.ADMIN and request.user.is_staff:
            return True  # Superadmin bypass
        
        # Hospital admin can only access their own hospital
        if hasattr(request.user, 'hospital_profile'):
            user_hospital = request.user.hospital_profile
            return obj.hospital == user_hospital
        
        return False
```

### 2. **Immutable Audit Logs**

All admin actions are logged and **cannot be modified or deleted**:

```python
class AuditLog(models.Model):
    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("AuditLog records are immutable")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise PermissionError("AuditLog records cannot be deleted")
```

**Logged Actions:**
- User updates (which fields changed)
- Password resets (with user notification)
- Hospital approvals/rejections
- OTP history views
- All admin actions with full context

### 3. **PII Protection**

**Donor PII is protected:**
- Hospital admins see: blood type, availability, match status
- Hospital admins **do not** see: full name, national ID, contact info
- Full PII only revealed after mutual match confirmation

**OTP Security:**
- Raw OTP codes are **never** exposed via API
- Only status (used/unused, timestamps) is visible
- OTPs expire after 10 minutes

### 4. **Rate Limiting**

Separate rate limits for admin logins:
```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "login": "10/hour",  # Stricter for admin accounts
    }
}
```

### 5. **Email Notifications**

All sensitive admin actions trigger email notifications:
- Password resets
- Hospital approvals/rejections
- Account suspensions

---

## Implementation Details

### Files Created/Modified

**New Files:**
```
apps/accounts/
├── permissions.py          # Permission classes
├── admin_serializers.py    # Admin-specific serializers
├── admin_views.py          # Admin ViewSets
├── admin_urls.py           # Admin URL routing
└── migrations/
    └── 0002_email_not_null.py  # Email migration

docs/
└── ADMIN_ROLES_AND_PERMISSIONS.md  # This document
```

**Modified Files:**
```
apps/accounts/
├── models.py               # Email as USERNAME_FIELD
├── serializers.py          # Email-based auth
├── views.py                # Email OTP integration
├── urls.py                 # Admin URL inclusion
└── admin.py                # Updated for email

config/settings/base.py     # Added django_filters
requirements.txt            # Added sendgrid, django-filter
```

### Key Design Decisions

1. **Email as Primary Identifier**
   - Changed from phone to email for authentication
   - OTPs sent via SendGrid (production) or console (dev)
   - Phone is now optional

2. **Separate Admin Namespaces**
   - `/superadmin/` - Platform superadmin endpoints
   - `/hospital-admin/` - Hospital admin endpoints
   - Clear separation prevents accidental access

3. **Immutable Audit Trail**
   - AuditLog records cannot be updated or deleted
   - Even superadmins cannot modify audit entries
   - Full context captured (IP, user agent, metadata)

4. **Least Privilege Principle**
   - Hospital admins see minimal donor PII
   - Staff have limited access within hospital scope
   - Superadmin required for platform-wide changes

---

## Frontend Integration

### Authentication Flow

```javascript
// 1. Login
POST /api/v1/accounts/login/
{
  "email": "admin@damulink.co.ke",
  "password": "password"
}

// Response
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": {
    "id": 1,
    "role": "damulink_admin",
    "is_verified": true,
    "full_name": "Admin User"
  }
}

// 2. Use token in subsequent requests
Authorization: Bearer eyJ...
```

### Admin Dashboard Routes

```javascript
// Platform Superadmin Routes
const superadminRoutes = [
  '/superadmin/users',
  '/superadmin/hospitals',
  '/superadmin/audit-logs',
  '/superadmin/stats'
];

// Hospital Admin Routes
const hospitalAdminRoutes = [
  '/hospital-admin/dashboard',
  '/hospital-admin/staff'
];
```

### Example API Calls

**List Users (Superadmin):**
```javascript
GET /api/v1/accounts/superadmin/users/
Authorization: Bearer <token>

// Response
{
  "count": 150,
  "results": [
    {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "donor",
      "is_verified": true,
      "is_active": true,
      "created_at": "2026-01-01T00:00:00Z",
      "hospital_name": null
    }
  ]
}
```

**Approve Hospital:**
```javascript
POST /api/v1/accounts/superadmin/hospitals/5/approve/
Authorization: Bearer <token>

// Response
{
  "message": "Nairobi Hospital has been approved",
  "hospital": { /* full hospital details */ }
}
```

**Hospital Dashboard:**
```javascript
GET /api/v1/accounts/hospital-admin/dashboard/dashboard/
Authorization: Bearer <token>

// Response
{
  "facility_name": "Nairobi Hospital",
  "approval_status": "approved",
  "subscription_tier": "professional",
  "searches_remaining": 450,
  "total_requests": 120,
  "pending_matches": 5,
  "completed_donations": 85
}
```

---

## Testing

### Create Superadmin User

```bash
python manage.py createsuperuser
# Email: admin@damulink.co.ke
# Must set is_staff=True in admin panel
```

### Test Admin Endpoints

```bash
# 1. Login
curl -X POST http://127.0.0.1:8000/api/v1/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@damulink.co.ke","password":"password"}'

# 2. Access admin endpoint
curl http://127.0.0.1:8000/api/v1/accounts/superadmin/stats/ \
  -H "Authorization: Bearer <access_token>"

# 3. List users
curl http://127.0.0.1:8000/api/v1/accounts/superadmin/users/ \
  -H "Authorization: Bearer <access_token>"
```

---

## Compliance & Best Practices

### Kenya Data Protection Act Compliance

1. **Data Minimization**: Only collect necessary PII
2. **Purpose Limitation**: Data used only for stated purposes
3. **Storage Limitation**: Regular data audits and cleanup
4. **Accountability**: Full audit trail of all data access

### Security Best Practices

1. **Never expose raw OTP codes** via API
2. **Always log admin actions** with full context
3. **Rate limit admin logins** separately from regular users
4. **Use HTTPS** in production (enforced in settings)
5. **Regular security audits** of admin access logs
6. **Separate environments** for staging/production

---

## Migration Notes

### Email Migration (0002_email_not_null)

**Purpose:** Changed `email` from optional to required, unique field.

**Process:**
1. Populated null emails with placeholders: `user_{id}@placeholder.damulink.co.ke`
2. Resolved duplicate emails by appending user ID
3. Set `email` as non-nullable and unique

**Impact:**
- All users now have email addresses
- Email is the primary authentication identifier
- Phone is now optional

---

## Future Enhancements

### Planned Features

1. **Granular Superadmin Permissions**
   - Read-only support staff
   - Hospital approval specialists
   - Payment managers
   - Feature flags for sensitive operations

2. **Two-Factor Authentication for Admins**
   - Mandatory 2FA for all superadmin accounts
   - TOTP-based (Google Authenticator, etc.)

3. **Advanced Filtering**
   - Date range filters for audit logs
   - Bulk actions for user management
   - Export functionality (CSV, PDF)

4. **Real-time Notifications**
   - WebSocket alerts for admin actions
   - Email digests for pending approvals

5. **Admin Dashboard UI**
   - React-based admin interface
   - Real-time statistics
   - Interactive audit log viewer

---

## Support

For questions or issues:
- **Email**: tech@damulink.co.ke
- **Documentation**: https://docs.damulink.co.ke
- **GitHub Issues**: https://github.com/delarum/damu-server/issues

---

**Last Updated:** 2026-07-07
**Version:** 1.0.0
**Status:** Production Ready ✅