# DamuLink Backend

![Django](https://img.shields.io/badge/Django-5.x-green)
![DRF](https://img.shields.io/badge/Django%20REST%20Framework-3.x-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13%2B-blue)
![Redis](https://img.shields.io/badge/Redis-7.x-red)

## Overview

DamuLink is a national donor management platform that connects blood donors, organ donors, hospitals, blood banks, researchers, and healthcare organizations through a secure and scalable digital infrastructure.

The backend is built using Django REST Framework and provides comprehensive APIs for donor registration, hospital onboarding, donor matching, gamification, identity verification, payments, notifications, audit logging, and USSD access.

The platform is designed to serve as a centralized donor network enabling healthcare facilities to efficiently locate eligible donors while maintaining strict privacy and security controls.

---

## Table of Contents

1. [Core Features](#core-features)
2. [Technology Stack](#technology-stack)
3. [System Architecture](#system-architecture)
4. [Project Structure](#project-structure)
5. [Local Development Setup](#local-development-setup)
6. [Environment Variables](#environment-variables)
7. [Database Setup](#database-setup)
8. [Running the Project](#running-the-project)
9. [Background Tasks](#background-tasks)
10. [Authentication & Authorization](#authentication--authorization)
11. [Role-Based Access Control](#role-based-access-control)
12. [API Endpoints](#api-endpoints)
13. [Security Architecture](#security-architecture)
14. [Data Protection & Compliance](#data-protection--compliance)
15. [Third-Party Integrations](#third-party-integrations)
16. [Testing](#testing)
17. [Deployment](#deployment)
18. [Contributing](#contributing)
19. [License](#license)

---

## Core Features

### Donor Management
- Donor registration (blood and organ donors)
- Identity verification (Smile ID integration)
- Blood type management (A+, A-, B+, B-, AB+, AB-, O+, O-)
- Organ donor pledges (kidney, liver, heart, lung, etc.)
- Donation history tracking
- Availability management with cooldown periods
- Donor profile visibility controls

### Hospital Management
- Hospital onboarding and verification
- Facility type classification (public, private, blood bank, research)
- Document upload (license, certificates)
- Staff management with role assignment
- Subscription management (tiered plans)
- Approval workflow (pending, approved, rejected, suspended)

### Matching System
- Blood donor search with radius-based filtering
- Organ donor search by type
- Donor map visualization
- Contact request workflows
- Request expiration and response tracking
- Privacy-preserving masked contact details

### Gamification
- Credits system for donations
- Achievement badges
- Donation milestones
- Credit redemption
- Leaderboards
- Transaction ledger

### Communication
- SMS notifications (Africa's Talking)
- Email notifications (SendGrid)
- USSD access for feature phones
- In-app notifications

### Payments
- M-Pesa STK Push integration
- Stripe subscription management
- Payment history tracking
- Subscription activation and management

### Audit & Compliance
- Comprehensive audit logging
- Immutable action records
- IP address and user agent tracking
- Admin action tracking
- Compliance reporting

### Identity Verification
- ID document upload
- Smile ID integration for verification
- Manual review queue
- Verification status tracking
- Liveness detection

---

## Technology Stack

### Backend
- **Python** 3.12+
- **Django** 5.x
- **Django REST Framework** 3.x
- **SimpleJWT** for authentication
- **Django Filters** for advanced filtering

### Database
- **PostgreSQL** 13+ (production)
- **SQLite** (development)

### Caching & Queues
- **Redis** 7.x (caching, sessions, Celery broker)

### Task Processing
- **Celery** for async tasks
- **Celery Beat** for scheduled tasks
- **Django Celery Beat** for database-backed schedules

### File Storage
- **AWS S3** or **Cloudflare R2** (production)
- Local filesystem (development)

### Email & SMS
- **SendGrid** for transactional emails
- **Africa's Talking** for SMS and USSD

### Identity Verification
- **Smile Identity** for ID verification and liveness detection

### Payments
- **M-Pesa Daraja** for mobile money
- **Stripe** for card payments

### Infrastructure
- **Gunicorn** WSGI server
- **Nginx** reverse proxy
- **WhiteNoise** for static files
- **Docker** containerization

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Donor Web App│  │Donor Mobile  │  │ Hospital Dashboard│  │
│  │              │  │    App       │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Admin Panel  │  │ USSD Gateway │  │ Third-Party Portal│ │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓ HTTPS
┌─────────────────────────────────────────────────────────────┐
│              Django REST API (Gunicorn)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  URL Router (config/urls.py)                         │  │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────────┐  │  │
│  │  │   Auth     │  │   Donors   │  │   Hospitals   │  │  │
│  │  └────────────┘  └────────────┘  └───────────────┘  │  │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────────┐  │  │
│  │  │  Matching  │  │Gamification│  │   Payments    │  │  │
│  │  └────────────┘  └────────────┘  └───────────────┘  │  │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────────┐  │  │
│  │  │Audit/Admin │  │Verification│  │Notifications  │  │  │
│  │  └────────────┘  └────────────┘  └───────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                       │
│  • User accounts & authentication                            │
│  • Donor profiles & medical information                      │
│  • Hospital profiles & subscriptions                         │
│  • Matching requests & contact logs                          │
│  • Gamification data (credits, badges)                       │
│  • Payment records & transactions                            │
│  • Audit logs (immutable)                                    │
│  • Verification records                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                        Redis Cache                            │
│  • Session storage                                           │
│  • JWT token blacklist                                       │
│  • Rate limiting counters                                    │
│  • Celery message broker                                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    Celery Workers                             │
│  • Async notification sending                                │
│  • ID verification processing                                │
│  • Payment webhook handling                                  │
│  • Scheduled tasks (subscription expiry, etc.)               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    External Services                          │
│  • Africa's Talking (SMS, USSD)                              │
│  • Smile Identity (ID verification)                          │
│  • M-Pesa Daraja (mobile payments)                           │
│  • Stripe (card payments)                                    │
│  • SendGrid (email)                                          │
│  • AWS S3 / Cloudflare R2 (file storage)                     │
│  • Google Maps (geocoding, distance calculation)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
damu-server/
├── config/
│   ├── settings/
│   │   ├── base.py           # Shared settings across environments
│   │   ├── development.py    # Development-specific settings
│   │   └── production.py     # Production-specific settings
│   ├── urls.py               # Root URL configuration
│   ├── wsgi.py               # WSGI application entry point
│   └── asgi.py               # ASGI application entry point
│
├── apps/
│   ├── accounts/             # User authentication & authorization
│   │   ├── models.py         # User, OTP models
│   │   ├── views.py          # Registration, login, OTP views
│   │   ├── serializers.py    # Registration, login serializers
│   │   ├── urls.py           # Auth endpoints
│   │   ├── admin_urls.py     # Admin user management endpoints
│   │   ├── admin_views.py    # Superadmin & hospital admin views
│   │   ├── admin_serializers.py
│   │   ├── permissions.py    # Custom permission classes
│   │   └── exceptions.py     # Custom exception handler
│   │
│   ├── donors/               # Donor management
│   │   ├── models.py         # DonorProfile model
│   │   ├── views.py          # Profile CRUD, availability
│   │   ├── serializers.py    # Donor serializers
│   │   ├── urls.py           # Donor endpoints
│   │   └── admin.py
│   │
│   ├── hospitals/            # Hospital management
│   │   ├── models.py         # HospitalProfile, Document, Staff
│   │   ├── views.py          # Profile, documents, staff, subscription
│   │   ├── serializers.py    # Hospital serializers
│   │   ├── urls.py           # Hospital endpoints
│   │   └── admin.py
│   │
│   ├── matching/             # Donor-hospital matching
│   │   ├── models.py         # ContactRequest model
│   │   ├── views.py          # Search, contact requests
│   │   ├── serializers.py    # Search results, contact requests
│   │   ├── urls.py           # Matching endpoints
│   │   └── admin.py
│   │
│   ├── gamification/         # Credits, badges, donations
│   │   ├── models.py         # Badge, DonorBadge, DonationRecord, CreditLedger
│   │   ├── views.py          # Donations, credits, badges
│   │   ├── serializers.py    # Gamification serializers
│   │   ├── services.py       # Business logic (award credits, etc.)
│   │   ├── urls.py           # Gamification endpoints
│   │   └── admin.py
│   │
│   ├── payments/             # Payment processing
│   │   ├── models.py         # Payment model
│   │   ├── views.py          # M-Pesa, Stripe endpoints
│   │   ├── mpesa.py          # M-Pesa Daraja integration
│   │   ├── stripe_service.py # Stripe integration
│   │   ├── urls.py           # Payment endpoints
│   │   └── admin.py
│   │
│   ├── notifications/        # Notification system
│   │   ├── models.py         # Notification model
│   │   ├── views.py          # Send SMS, email, list notifications
│   │   ├── services.py       # Notification service functions
│   │   ├── urls.py           # Notification endpoints
│   │   └── admin.py
│   │
│   ├── verification/         # Identity verification
│   │   ├── models.py         # IdentityVerification model
│   │   ├── views.py          # Upload ID, status, manual review
│   │   ├── smile_identity.py # Smile ID integration
│   │   ├── urls.py           # Verification endpoints
│   │   └── admin.py
│   │
│   ├── audit/                # Audit logging
│   │   ├── models.py         # AuditLog model (immutable)
│   │   ├── views.py          # List audit logs
│   │   ├── middleware.py     # Automatic audit logging middleware
│   │   ├── utils.py          # Audit utility functions
│   │   ├── urls.py           # Audit endpoints
│   │   └── admin.py
│   │
│   ├── ussd/                 # USSD gateway
│   │   ├── models.py         # USSDSession model
│   │   ├── views.py          # USSD callback handler
│   │   ├── menus.py          # USSD menu flows
│   │   ├── urls.py           # USSD endpoints
│   │   └── admin.py
│   │
│   └── third_party/          # Third-party researcher access
│       ├── models.py         # (if applicable)
│       ├── views.py          # Application, data access
│       ├── urls.py           # Third-party endpoints
│       └── admin.py
│
├── utils/
│   ├── __init__.py
│   ├── exceptions.py         # Custom exception handler
│   └── geo.py                # Geospatial utilities
│
├── docs/
│   └── ADMIN_ROLES_AND_PERMISSIONS.md
│
├── requirements.txt          # Python dependencies
├── manage.py                 # Django management script
├── .env.example              # Environment variables template
└── README.md                 # This file
```

---

## Local Development Setup

### Prerequisites

- Python 3.12 or higher
- PostgreSQL 13+ (or use SQLite for quick setup)
- Redis 7.x
- Git

### Clone Repository

```bash
git clone https://github.com/damulink/damu-server.git
cd damu-server
```

### Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root. See `.env.example` for a template.

### Required Variables

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL recommended for production)
DATABASE_URL=postgres://user:password@localhost:5432/damulink
# Or for SQLite (development only):
# DATABASE_URL=sqlite:///db.sqlite3

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT (auto-generated if not provided)
# No manual configuration needed

# Field Encryption (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
FIELD_ENCRYPTION_KEY=your-encryption-key-here

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Email (SendGrid)
SENDGRID_API_KEY=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@damulink.co.ke

# SMS (Africa's Talking)
AT_USERNAME=sandbox
AT_API_KEY=your-at-api-key
AT_SENDER_ID=DamuLink
AT_USSD_CODE=*384*123#

# Identity Verification (Smile Identity)
SMILE_PARTNER_ID=your-partner-id
SMILE_API_KEY=your-api-key

# Payments
# M-Pesa Daraja
MPESA_CONSUMER_KEY=your-consumer-key
MPESA_CONSUMER_SECRET=your-consumer-secret
MPESA_SHORTCODE=your-shortcode
MPESA_PASSKEY=your-passkey
MPESA_STK_URL=https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest
MPESA_TOKEN_URL=https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials
MPESA_CALLBACK_URL=https://your-domain.com/api/v1/payments/mpesa/callback/

# Stripe
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

# File Storage (AWS S3 or Cloudflare R2)
USE_S3=False  # Set to True in production
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=damulink-secure-docs
AWS_S3_REGION_NAME=af-south-1
AWS_S3_CUSTOM_DOMAIN=  # For Cloudflare R2

# Google Maps (optional, for distance calculations)
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

---

## Database Setup

### Option 1: PostgreSQL (Recommended)

```bash
# Create database
psql -U postgres
CREATE DATABASE damulink;
\q

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Option 2: SQLite (Quick Development)

```bash
# SQLite is used automatically if DATABASE_URL is not set
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

---

## Running the Project

### Development Server

```bash
python manage.py runserver
```

Server will be available at: `http://127.0.0.1:8000`

### API Documentation

- **Swagger UI**: `http://127.0.0.1:8000/swagger/`
- **ReDoc**: `http://127.0.0.1:8000/redoc/`
- **OpenAPI JSON**: `http://127.0.0.1:8000/swagger.json`

### Django Admin

`http://127.0.0.1:8000/admin/`

---

## Background Tasks

### Start Redis

```bash
# Windows (using WSL or Docker)
redis-server

# macOS (using Homebrew)
brew services start redis

# Linux
sudo systemctl start redis
```

### Start Celery Worker

```bash
celery -A config worker -l info
```

### Start Celery Beat (Scheduled Tasks)

```bash
celery -A config beat -l info
```

### Run All Services (Development)

Use separate terminal windows or a process manager like `honcho`:

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Django
python manage.py runserver

# Terminal 3: Celery Worker
celery -A config worker -l info

# Terminal 4: Celery Beat
celery -A config beat -l info
```

---

## Authentication & Authorization

### JWT Authentication

The platform uses **SimpleJWT** for authentication.

**Token Lifetimes:**
- Access Token: 15 minutes
- Refresh Token: 7 days
- Refresh token rotation: Enabled
- Token blacklisting: Enabled

**Login Request:**

```http
POST /api/v1/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response:**

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Using the Access Token:**

```http
GET /api/v1/auth/me/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Refreshing the Token:**

```http
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### OTP Verification

New registrations require OTP verification:

```http
POST /api/v1/auth/verify-otp/
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456"
}
```

Resend OTP:

```http
POST /api/v1/auth/resend-otp/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

---

## Role-Based Access Control

### User Roles

| Role | Description |
|------|-------------|
| `donor` | Blood/organ donor, manages own profile |
| `hospital_staff` | Hospital employee, can search donors |
| `hospital_admin` | Hospital administrator, manages staff and subscription |
| `damulink_admin` | Platform superadmin, full access |
| `third_party_researcher` | Approved researcher, anonymized data only |

### Permissions

| Permission | Description |
|------------|-------------|
| `IsDonor` | Donor role required |
| `IsHospitalStaff` | Hospital staff role required |
| `IsHospitalAdmin` | Hospital admin role required |
| `IsPlatformSuperadmin` | Platform superadmin role required |
| `IsVerifiedUser` | User must have verified identity |
| `IsOwnerOrSuperadmin` | Object owner or superadmin |
| `IsHospitalScoped` | User belongs to the hospital |
| `CanViewAuditLogs` | Can view audit logs |
| `CanManageUsers` | Can manage users |
| `CanApproveHospitals` | Can approve/reject hospitals |
| `CanManagePayments` | Can manage payments |
| `CanManageGamification` | Can manage gamification |

---

## API Endpoints

### Base URL

```
http://127.0.0.1:8000/api/v1/
```

---

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register/donor/` | Register as donor | No |
| POST | `/auth/register/hospital/` | Register hospital | No |
| POST | `/auth/login/` | Login (JWT) | No |
| POST | `/auth/logout/` | Logout (blacklist token) | Yes |
| POST | `/auth/token/refresh/` | Refresh access token | No |
| POST | `/auth/verify-otp/` | Verify OTP code | No |
| POST | `/auth/resend-otp/` | Resend OTP code | No |
| POST | `/auth/change-password/` | Change password | Yes |
| GET | `/auth/me/` | Get current user | Yes |

---

### Donor Management

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/donors/profile/` | Create donor profile | Yes | donor |
| GET | `/donors/profile/me/` | Get own profile | Yes | donor |
| PUT/PATCH | `/donors/profile/update/` | Update donor profile | Yes | donor |
| DELETE | `/donors/profile/delete/` | Delete donor profile | Yes | donor |
| POST | `/donors/profile/availability/` | Toggle availability | Yes | donor |
| GET | `/donors/profile/<donor_id>/hospital-view/` | View donor (hospital) | Yes | hospital_staff+ |

**Donor Profile Fields:**
- Blood type (A+, A-, B+, B-, AB+, AB-, O+, O-)
- Gender
- Date of birth
- Weight (kg)
- Height (cm)
- Medical conditions
- Medications
- Allergies
- Donor type (whole_blood, plasma, platelets, organs)
- Organs pledged (kidney, liver, heart, lung, etc.)
- Availability status
- Location (county, sub-county, coordinates)

---

### Hospital Management

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/hospitals/profile/` | Create hospital profile | Yes | hospital_admin |
| GET | `/hospitals/profile/me/` | Get own profile | Yes | hospital_staff+ |
| PUT/PATCH | `/hospitals/profile/update/` | Update hospital profile | Yes | hospital_admin |
| DELETE | `/hospitals/profile/delete/` | Delete hospital profile | Yes | hospital_admin |
| POST | `/hospitals/documents/upload/` | Upload document | Yes | hospital_admin |
| GET | `/hospitals/staff/` | List staff members | Yes | hospital_staff+ |
| POST | `/hospitals/staff/add/` | Add staff member | Yes | hospital_admin |
| DELETE | `/hospitals/staff/<staff_id>/remove/` | Remove staff member | Yes | hospital_admin |
| GET | `/hospitals/subscription/` | Get subscription details | Yes | hospital_admin |
| POST | `/hospitals/subscription/activate/` | Activate subscription | Yes | hospital_admin |

**Hospital Profile Fields:**
- Facility name
- Facility type (public, private, blood_bank, research)
- Registration number
- License number
- County, sub-county
- Address, coordinates
- Phone, email
- Approval status (pending, approved, rejected, suspended)
- Subscription tier (basic, premium, enterprise)
- Search quota

---

### Matching

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/matching/search/blood/` | Search blood donors | Yes | hospital_staff+ |
| GET | `/matching/search/organs/` | Search organ donors | Yes | hospital_staff+ |
| GET | `/matching/donors/map/` | Get donor map data | Yes | hospital_staff+ |
| POST | `/matching/contact-request/` | Initiate contact request | Yes | hospital_staff+ |
| GET | `/matching/contact-requests/` | List hospital's requests | Yes | hospital_staff+ |
| GET | `/matching/contact-requests/mine/` | List donor's requests | Yes | donor |
| POST | `/matching/contact-requests/<id>/respond/` | Respond to request | Yes | donor |

**Search Parameters (Blood):**
- `blood_type` (required): A+, A-, B+, B-, AB+, AB-, O+, O-
- `county` (optional): Filter by county
- `radius_km` (optional): Search radius in kilometers (default: 50)
- `available_only` (optional): Only show available donors (default: true)

**Contact Request Status:**
- `pending` - Awaiting donor response
- `accepted` - Donor accepted
- `declined` - Donor declined
- `expired` - Request expired (7 days)

---

### Donations & Gamification

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/donations/` | Record donation | Yes | hospital_staff+ |
| GET | `/donations/history/` | Get donation history | Yes | donor |
| GET | `/donations/<id>/` | Get donation details | Yes | owner/hospital |
| PATCH | `/donations/<id>/` | Update donation | Yes | hospital_admin |
| DELETE | `/donations/<id>/` | Delete donation | Yes | hospital_admin |
| GET | `/credits/balance/` | Get credit balance | Yes | donor |
| GET | `/credits/ledger/` | Get credit transaction history | Yes | donor |
| POST | `/credits/redeem/` | Redeem credits | Yes | donor |
| GET | `/badges/` | Get donor badges | Yes | donor |

**Credit System:**
- Whole blood donation: 10 credits
- Plasma donation: 15 credits
- Platelet donation: 15 credits
- Organ donation: 100 credits

**Badges:**
- First donation
- 5 donations
- 10 donations
- 25 donations (Champion)
- 50 donations (Legend)
- Blood type-specific badges

---

### Payments

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/payments/mpesa/stk-push/` | Initiate M-Pesa payment | Yes | hospital_admin |
| POST | `/payments/mpesa/callback/` | M-Pesa callback (webhook) | No |
| POST | `/payments/stripe/subscribe/` | Create Stripe subscription | Yes | hospital_admin |
| POST | `/payments/stripe/webhook/` | Stripe webhook | No |
| GET | `/payments/history/` | Get payment history | Yes | hospital_admin |

**Subscription Tiers:**
- **Basic**: KES 2,999/month (50 searches/month)
- **Premium**: KES 7,999/month (200 searches/month)
- **Enterprise**: KES 19,999/month (unlimited searches)

---

### Notifications

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/notifications/sms/` | Send SMS (admin) | Yes | damulink_admin |
| POST | `/notifications/email/` | Send email (admin) | Yes | damulink_admin |
| GET | `/notifications/mine/` | Get my notifications | Yes | All |

**Notification Channels:**
- SMS (Africa's Talking)
- Email (SendGrid)
- In-app

**Notification Types:**
- Contact request received
- Contact request accepted/declined
- Donation confirmed
- Subscription expiring
- Hospital approved/rejected
- Password changed
- OTP verification

---

### USSD

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/ussd/` | USSD callback | No |
| POST | `/ussd/confirm-donation/` | Confirm donation via USSD | No |

**USSD Code:** `*384*123#`

**USSD Flows:**
- Donor flow: Check credits, toggle availability, view contact requests
- Hospital flow: Search donors, check subscription

---

### Verification

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/verification/upload-id/` | Upload ID documents | Yes | donor/hospital |
| GET | `/verification/status/` | Get verification status | Yes | All |
| GET | `/verification/manual-review/` | List pending reviews | Yes | damulink_admin |
| POST | `/verification/manual-review/<id>/` | Review verification | Yes | damulink_admin |

**Verification Status:**
- `pending` - Awaiting verification
- `in_progress` - Being verified (Smile ID)
- `approved` - Verified successfully
- `rejected` - Verification failed
- `manual_review` - Requires manual review

**ID Types:**
- National ID
- Passport
- Driver's License

---

### Third-Party Integrations

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/third-party/apply/` | Apply for access | Yes | third_party_researcher |
| GET | `/third-party/applications/` | List applications | Yes | damulink_admin |
| POST | `/third-party/applications/<id>/review/` | Review application | Yes | damulink_admin |
| GET | `/third-party/data/` | Access anonymized data | Yes | third_party_researcher |

---

### Audit Logs

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/audit/logs/` | List audit logs | Yes | damulink_admin |

**Audit Log Fields:**
- Actor (user who performed action)
- Action (create, update, delete, login, etc.)
- Target user (if applicable)
- IP address
- User agent
- Timestamp
- Metadata (JSON)

**Note:** Audit logs are immutable. Once created, they cannot be modified or deleted.

---

### Administration (Superadmin)

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/admin/superadmin/users/` | List all users | Yes | damulink_admin |
| GET | `/admin/superadmin/users/<id>/` | Get user details | Yes | damulink_admin |
| PUT/PATCH | `/admin/superadmin/users/<id>/` | Update user | Yes | damulink_admin |
| POST | `/admin/superadmin/users/<id>/reset_password/` | Reset user password | Yes | damulink_admin |
| GET | `/admin/superadmin/users/<id>/otp_history/` | Get user OTP history | Yes | damulink_admin |
| GET | `/admin/superadmin/hospitals/` | List all hospitals | Yes | damulink_admin |
| GET | `/admin/superadmin/hospitals/<id>/` | Get hospital details | Yes | damulink_admin |
| PUT/PATCH | `/admin/superadmin/hospitals/<id>/` | Update hospital | Yes | damulink_admin |
| POST | `/admin/superadmin/hospitals/<id>/approve/` | Approve hospital | Yes | damulink_admin |
| POST | `/admin/superadmin/hospitals/<id>/reject/` | Reject hospital | Yes | damulink_admin |
| POST | `/admin/superadmin/hospitals/<id>/suspend/` | Suspend hospital | Yes | damulink_admin |
| POST | `/admin/superadmin/hospitals/<id>/reactivate/` | Reactivate hospital | Yes | damulink_admin |
| GET | `/admin/superadmin/audit-logs/` | List all audit logs | Yes | damulink_admin |
| GET | `/admin/superadmin/stats/` | Get platform statistics | Yes | damulink_admin |

---

### Administration (Hospital Admin)

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/admin/hospital-admin/dashboard/` | Get hospital dashboard | Yes | hospital_admin |
| GET | `/admin/hospital-admin/staff/` | List hospital staff | Yes | hospital_admin |

---

## Security Architecture

### Authentication Security

- **JWT** authentication with short-lived access tokens (15 minutes)
- **Refresh token rotation** for enhanced security
- **Token blacklisting** on logout
- **Role-based authorization** with granular permissions
- **OTP verification** for new registrations
- **Password strength validation** (Django validators)
- **Optional MFA** for donors (future enhancement)
- **Mandatory MFA** for hospital admins (future enhancement)

### Encryption

#### In Transit
- TLS 1.3 (enforced in production)
- HTTPS only (HSTS enabled)
- CORS configured for specific origins

#### At Rest
- **AES-256 encryption** for sensitive fields:
  - Identity document images
  - Medical records
  - Personal information (addresses, phone numbers)
  - Payment information
- **Fernet encryption** for database fields
- **Private S3/R2 buckets** for file storage
- **Signed URLs** with 5-minute expiration

### Audit Logging

All sensitive actions are automatically logged via middleware.

**Captured Metadata:**
- User (actor)
- Role
- Action performed
- Target user/object
- Timestamp
- IP address
- User agent
- Request metadata (JSON)

**Audit Log Properties:**
- Immutable (cannot be modified or deleted)
- Retained indefinitely
- Indexed for fast querying

### Rate Limiting

| Resource | Limit | Scope |
|----------|-------|-------|
| Login attempts | 10 requests | Per hour, per IP |
| Donor searches | 60 requests | Per hour, per user |
| Contact requests | 20 requests | Per hour, per user |
| USSD sessions | 10 requests | Per hour, per phone |
| OTP requests | 5 requests | Per hour, per email |
| General API | 1000 requests | Per day, per user |
| Anonymous API | 100 requests | Per day, per IP |

### File Security

- Private S3/R2 buckets (no public access)
- Signed URLs with 5-minute expiration
- Server-side encryption (AES-256)
- File type validation
- File size limits
- Virus scanning (future enhancement)

### Security Headers

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security` (production)
- `Content-Security-Policy` (production)

---

## Data Protection & Compliance

### Compliance Standards

The platform is designed to comply with:
- **Kenya Data Protection Act (2019)**
- **Privacy by Design** principles
- **Explicit consent** requirements
- **Data minimization** standards
- **Health data protection** obligations
- **Right to erasure** (GDPR-inspired)

### Data Retention

- **Audit logs**: Indefinite retention
- **Donation records**: 7 years (medical records requirement)
- **Payment records**: 7 years (tax compliance)
- **Verification records**: 3 years after verification
- **Inactive accounts**: Archived after 2 years of inactivity

### User Rights

- Right to access personal data
- Right to correct inaccurate data
- Right to delete account (with data retention exceptions)
- Right to data portability
- Right to opt out of communications

### Hospital Obligations

Hospitals are contractually required to:
- Use donor data only for medical purposes
- Report data breaches within 72 hours
- Avoid retaining donor data unnecessarily
- Participate in compliance audits
- Encrypt donor data in transit and at rest

---

## Third-Party Integrations

### Africa's Talking

**Services:**
- SMS notifications
- USSD gateway

**Configuration:**
- `AT_USERNAME`: Africa's Talking username
- `AT_API_KEY`: API key
- `AT_SENDER_ID`: Sender ID for SMS
- `AT_USSD_CODE`: USSD code (e.g., `*384*123#`)

### Smile Identity

**Services:**
- ID document verification
- Liveness detection
- Facial matching

**Configuration:**
- `SMILE_PARTNER_ID`: Partner ID
- `SMILE_API_KEY`: API key

**Supported ID Types:**
- Kenyan National ID
- Kenyan Passport
- Kenyan Driver's License

### M-Pesa Daraja

**Services:**
- STK Push (mobile money payments)
- Transaction callbacks

**Configuration:**
- `MPESA_CONSUMER_KEY`: Consumer key
- `MPESA_CONSUMER_SECRET`: Consumer secret
- `MPESA_SHORTCODE`: Business shortcode
- `MPESA_PASSKEY`: Lipa na M-Pesa passkey
- `MPESA_STK_URL`: STK Push URL
- `MPESA_TOKEN_URL`: OAuth token URL
- `MPESA_CALLBACK_URL`: Callback URL

### Stripe

**Services:**
- Subscription management
- Card payments
- Webhook handling

**Configuration:**
- `STRIPE_SECRET_KEY`: Secret key
- `STRIPE_WEBHOOK_SECRET`: Webhook signing secret

### SendGrid

**Services:**
- Transactional emails
- Email templates

**Configuration:**
- `SENDGRID_API_KEY`: API key
- `DEFAULT_FROM_EMAIL`: Sender email

### AWS S3 / Cloudflare R2

**Services:**
- Secure file storage
- ID document storage
- Medical records storage

**Configuration:**
- `USE_S3`: Set to `True` in production
- `AWS_ACCESS_KEY_ID`: Access key
- `AWS_SECRET_ACCESS_KEY`: Secret key
- `AWS_STORAGE_BUCKET_NAME`: Bucket name
- `AWS_S3_REGION_NAME`: Region (e.g., `af-south-1`)
- `AWS_S3_CUSTOM_DOMAIN`: Custom domain (for Cloudflare R2)

### Google Maps

**Services:**
- Geocoding (address to coordinates)
- Distance matrix API (calculate distances)

**Configuration:**
- `GOOGLE_MAPS_API_KEY`: API key

---

## Testing

### Run All Tests

```bash
python manage.py test
```

### Run Specific App Tests

```bash
# Accounts
python manage.py test apps.accounts

# Donors
python manage.py test apps.donors

# Hospitals
python manage.py test apps.hospitals

# Matching
python manage.py test apps.matching

# Gamification
python manage.py test apps.gamification

# Payments
python manage.py test apps.payments

# Notifications
python manage.py test apps.notifications

# Verification
python manage.py test apps.verification

# Audit
python manage.py test apps.audit

# USSD
python manage.py test apps.ussd
```

### Test Coverage

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run manage.py test

# Generate report
coverage report

# Generate HTML report
coverage html
open htmlcov/index.html
```

### Test Data

Use Django fixtures or factories (if configured) to load test data:

```bash
# Load fixtures
python manage.py loaddata fixtures/initial_data.json

# Create test superuser
python manage.py createsuperuser --settings=config.settings.test
```

---

## Deployment

### Recommended Stack

- **OS**: Ubuntu 22.04 LTS
- **Web Server**: Nginx
- **WSGI Server**: Gunicorn
- **Database**: PostgreSQL 13+
- **Cache**: Redis 7+
- **Task Queue**: Celery + Celery Beat
- **Process Manager**: Systemd
- **Reverse Proxy**: Nginx
- **SSL**: Let's Encrypt (Certbot)

### Pre-Deployment Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set strong `SECRET_KEY`
- [ ] Configure PostgreSQL database
- [ ] Set up Redis
- [ ] Configure S3/R2 for file storage
- [ ] Set up SendGrid for emails
- [ ] Configure Africa's Talking for SMS/USSD
- [ ] Set up Smile Identity
- [ ] Configure M-Pesa Daraja
- [ ] Configure Stripe
- [ ] Set up SSL certificates
- [ ] Configure firewall (UFW)
- [ ] Set up monitoring (Sentry, etc.)
- [ ] Configure logging
- [ ] Set up backups (database, media files)
- [ ] Run security checks (`python manage.py check --deploy`)

### Deployment Steps

#### 1. Clone Repository

```bash
git clone https://github.com/damulink/damu-server.git
cd damu-server
```

#### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with production values
nano .env
```

#### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```

#### 5. Create Superuser

```bash
python manage.py createsuperuser
```

#### 6. Set Up Systemd Services

Create service files for Gunicorn, Celery Worker, and Celery Beat.

**Example: `/etc/systemd/system/damulink.service`**

```ini
[Unit]
Description=Gunicorn daemon for DamuLink
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/damu-server
Environment="PATH=/home/ubuntu/damu-server/venv/bin"
EnvironmentFile=/home/ubuntu/damu-server/.env
ExecStart=/home/ubuntu/damu-server/venv/bin/gunicorn --workers 3 --bind unix:/run/gunicorn.sock config.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Example: `/etc/systemd/system/damulink-celery.service`**

```ini
[Unit]
Description=Celery Worker for DamuLink
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/damu-server
Environment="PATH=/home/ubuntu/damu-server/venv/bin"
EnvironmentFile=/home/ubuntu/damu-server/.env
ExecStart=/home/ubuntu/damu-server/venv/bin/celery -A config worker -l info

[Install]
WantedBy=multi-user.target
```

**Example: `/etc/systemd/system/damulink-celerybeat.service`**

```ini
[Unit]
Description=Celery Beat for DamuLink
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/damu-server
Environment="PATH=/home/ubuntu/damu-server/venv/bin"
EnvironmentFile=/home/ubuntu/damu-server/.env
ExecStart=/home/ubuntu/damu-server/venv/bin/celery -A config beat -l info

[Install]
WantedBy=multi-user.target
```

#### 7. Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl start damulink
sudo systemctl start damulink-celery
sudo systemctl start damulink-celerybeat
sudo systemctl enable damulink
sudo systemctl enable damulink-celery
sudo systemctl enable damulink-celerybeat
```

#### 8. Configure Nginx

**Example: `/etc/nginx/sites-available/damulink`**

```nginx
server {
    listen 80;
    server_name damulink.co.ke www.damulink.co.ke;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name damulink.co.ke www.damulink.co.ke;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/damulink.co.ke/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/damulink.co.ke/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Client body size (for file uploads)
    client_max_body_size 10M;

    # Static files
    location /static/ {
        root /home/ubuntu/damu-server/staticfiles;
    }

    # Media files
    location /media/ {
        root /home/ubuntu/damu-server/media;
    }

    # Django app
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/damulink /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 9. Set Up SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d damulink.co.ke -d www.damulink.co.ke
```

#### 10. Set Up Backups

```bash
# Database backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U postgres damulink > /backups/db_$DATE.sql
gzip /backups/db_$DATE.sql

# Media files backup
tar -czf /backups/media_$DATE.tar.gz /home/ubuntu/damu-server/media

# Keep only last 30 days
find /backups -type f -mtime +30 -delete
```

Add to crontab:

```bash
crontab -e

# Daily backup at 2 AM
0 2 * * * /home/ubuntu/backup.sh
```

---

## Supported Deployment Platforms

- **Railway**: One-click deploy with PostgreSQL and Redis
- **Render**: Managed Django hosting
- **AWS EC2**: Full control, scalable
- **DigitalOcean**: App Platform or Droplets
- **Heroku**: Legacy support
- **Docker**: Containerized deployment

---

## Contributing

We welcome contributions! Please follow these guidelines:

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Write Tests

All new features must include tests:

```bash
python manage.py test apps.your_app
```

### 3. Run Linting

```bash
# Install linting tools
pip install flake8 black isort

# Check code style
flake8 .

# Format code
black .
isort .
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Create a pull request on GitHub with:
- Clear description of changes
- Reference to related issues
- Screenshots (if applicable)
- Test coverage report

### 6. Code Review

- Maintainers will review your PR
- Address any feedback
- Once approved, your PR will be merged

---

## Troubleshooting

### Common Issues

#### 1. Migration Errors

```bash
# Fake migrations if needed
python manage.py migrate --fake

# Reset migrations (development only!)
python manage.py migrate --run-syncdb
```

#### 2. Redis Connection Errors

```bash
# Check Redis is running
redis-cli ping

# Restart Redis
sudo systemctl restart redis
```

#### 3. Celery Worker Not Processing Tasks

```bash
# Check Celery logs
celery -A config worker -l info

# Restart Celery
sudo systemctl restart damulink-celery
```

#### 4. Static Files Not Loading

```bash
# Collect static files
python manage.py collectstatic

# Check Nginx configuration
sudo nginx -t
```

#### 5. Database Connection Errors

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database credentials
python manage.py dbshell
```

---

## License

**Proprietary Software**

Copyright © DamuLink. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution, or modification of this software is strictly prohibited.

---

## Support

For technical support or questions:
- **Email**: support@damulink.co.ke
- **Documentation**: [https://docs.damulink.co.ke](https://docs.damulink.co.ke)
- **Issues**: [GitHub Issues](https://github.com/damulink/damu-server/issues)

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

---

## Roadmap

- [ ] Mobile app (Flutter)
- [ ] Advanced analytics dashboard
- [ ] AI-powered donor matching
- [ ] Multi-language support (Swahili, local languages)
- [ ] Offline mode for USSD
- [ ] Blockchain-based donation records
- [ ] Integration with national health database
- [ ] Telemedicine features
- [ ] Emergency blood request system
- [ ] Donor mobile money rewards

---

**Built with ❤️ by the DamuLink Team**