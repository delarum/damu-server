# DamuLink Backend

## Overview

DamuLink is a national donor management platform that connects blood donors, organ donors, hospitals, blood banks, researchers, and healthcare organizations through a secure and scalable digital infrastructure.

The backend is built using Django REST Framework and provides APIs for donor registration, hospital onboarding, donor matching, gamification, identity verification, payments, notifications, audit logging, and USSD access.

The platform is designed to serve as a centralized donor network enabling healthcare facilities to efficiently locate eligible donors while maintaining strict privacy and security controls.

---

# Table of Contents

1. Overview
2. Core Features
3. Technology Stack
4. System Architecture
5. Project Structure
6. Local Development Setup
7. Environment Variables
8. Database Setup
9. Running the Project
10. Background Tasks
11. Authentication
12. Role Based Access Control
13. API Endpoints
14. Security Architecture
15. Data Protection & Compliance
16. Third-Party Integrations
17. Testing
18. Deployment
19. Contributing
20. License

---

# Core Features

## Donor Management

* Donor registration
* Identity verification
* Blood donor management
* Organ donor registration
* Donation history tracking
* Availability management

## Hospital Management

* Hospital onboarding
* Facility verification
* Staff management
* Subscription management

## Matching System

* Blood donor matching
* Organ donor matching
* Radius-based searches
* Availability filtering
* Contact request workflows

## Gamification

* Credits system
* Achievement badges
* Donation milestones
* Leaderboards

## Communication

* SMS notifications
* Email notifications
* USSD access
* Future push notifications

## Payments

* M-Pesa subscriptions
* Stripe subscriptions
* Billing management

---

# Technology Stack

## Backend

* Python 3.12+
* Django 5.x
* Django REST Framework

## Database

* PostgreSQL

## Caching & Queues

* Redis

## Task Processing

* Celery
* Celery Beat

## Authentication

* JWT (SimpleJWT)

## Storage

* AWS S3
* Cloudflare R2

## Infrastructure

* Gunicorn
* Nginx
* Docker

---

# System Architecture

Client Applications

* Donor Web App
* Donor Mobile App
* Hospital Dashboard
* Admin Dashboard
* USSD Gateway

↓

Django REST API

↓

PostgreSQL

↓

Redis

↓

Celery Workers

↓

External Services

* Africa's Talking
* Smile Identity
* M-Pesa Daraja
* Stripe
* SendGrid
* AWS S3

---

# Project Structure

```text
damulink-backend/

├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── accounts/
│   ├── donors/
│   ├── hospitals/
│   ├── matching/
│   ├── payments/
│   ├── notifications/
│   ├── verification/
│   ├── gamification/
│   ├── ussd/
│   ├── audit/
│   └── third_party/
│
├── utils/
├── media/
├── static/
├── requirements/
└── manage.py
```

---

# Local Development Setup

## Clone Repository

```bash
git clone https://github.com/damulink/backend.git

cd backend
```

## Create Virtual Environment

```bash
python -m venv venv
```

## Activate Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux/macOS

```bash
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file in the project root.

```env
SECRET_KEY=

DEBUG=True

ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=damulink
DB_USER=postgres
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0

AT_USERNAME=
AT_API_KEY=

STRIPE_SECRET_KEY=

MPESA_CONSUMER_KEY=
MPESA_CONSUMER_SECRET=
MPESA_SHORTCODE=
MPESA_PASSKEY=

SENDGRID_API_KEY=

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=

SMILE_PARTNER_ID=
SMILE_API_KEY=
```

---

# Database Setup

Create database:

```sql
CREATE DATABASE damulink;
```

Run migrations:

```bash
python manage.py makemigrations

python manage.py migrate
```

Create administrator:

```bash
python manage.py createsuperuser
```

---

# Running the Project

```bash
python manage.py runserver
```

Server:

```text
http://127.0.0.1:8000
```

---

# Background Tasks

Start Redis:

```bash
redis-server
```

Start Celery Worker:

```bash
celery -A config worker -l info
```

Start Celery Beat:

```bash
celery -A config beat -l info
```

---

# Authentication

Authentication uses JWT.

Access Token:

* 15 minutes

Refresh Token:

* 7 days

Header:

```http
Authorization: Bearer <access_token>
```

---

# Role Based Access Control

## donor

* Manage own profile
* View credits
* View donation history

## hospital_staff

* Search donors
* Initiate contact requests

## hospital_admin

* Manage subscription
* Manage staff
* View hospital audit logs

## damulink_admin

* Full platform access

## third_party_researcher

* Approved anonymized datasets only

---

# API Endpoints

## Authentication

| Method | Endpoint |
|----------|----------|
| POST | /api/v1/auth/register/donor/ |
| POST | /api/v1/auth/register/hospital/ |
| POST | /api/v1/auth/login/ |
| POST | /api/v1/auth/logout/ |
| POST | /api/v1/auth/verify-otp/ |
| POST | /api/v1/auth/resend-otp/ |
| POST | /api/v1/auth/change-password/ |
| POST | /api/v1/auth/token/refresh/ |
| GET | /api/v1/auth/me/ |

---

## Donor Management

| Method | Endpoint |
|----------|----------|
| POST | /api/v1/donors/profile/ |
| GET | /api/v1/donors/profile/me/ |
| PUT/PATCH | /api/v1/donors/profile/update/ |
| DELETE | /api/v1/donors/profile/delete/ |
| POST | /api/v1/donors/profile/availability/ |

---

## Hospital Management

| Method | Endpoint |
|----------|----------|
| POST | /api/v1/hospitals/profile/ |
| GET | /api/v1/hospitals/profile/me/ |
| PUT/PATCH | /api/v1/hospitals/profile/update/ |
| DELETE | /api/v1/hospitals/profile/delete/ |
| POST | /api/v1/hospitals/documents/upload/ |
| GET | /api/v1/hospitals/staff/ |
| POST | /api/v1/hospitals/staff/add/ |
| DELETE | /api/v1/hospitals/staff/{staff_id}/remove/ |
| GET | /api/v1/hospitals/subscription/ |
| POST | /api/v1/hospitals/subscription/activate/ |

---

## Matching

| Method | Endpoint |
|----------|----------|
| GET | /api/v1/matching/search/blood/ |
| GET | /api/v1/matching/search/organs/ |
| POST | /api/v1/matching/contact-request/ |
| GET | /api/v1/matching/contact-requests/ |
| GET | /api/v1/matching/contact-requests/mine/ |
| POST | /api/v1/matching/contact-requests/{request_id}/respond/ |

---

## Donations & Gamification

| Method | Endpoint |
|----------|----------|
| POST | /api/v1/donations/ |
| GET | /api/v1/donations/history/ |
| GET/PUT/DELETE | /api/v1/donations/{donation_id}/ |
| GET | /api/v1/credits/balance/ |
| GET | /api/v1/credits/ledger/ |
| POST | /api/v1/credits/redeem/ |
| GET | /api/v1/badges/ |

---

## Payments

| Method | Endpoint |
|----------|----------|
| POST | /api/v1/payments/mpesa/stk-push/ |
| POST | /api/v1/payments/mpesa/callback/ |
| POST | /api/v1/payments/stripe/subscribe/ |
| POST | /api/v1/payments/stripe/webhook/ |
| GET | /api/v1/payments/history/ |

---

## Notifications

| Method | Endpoint |
|----------|----------|
| POST | /api/v1/notifications/sms/ |
| POST | /api/v1/notifications/email/ |
| GET | /api/v1/notifications/mine/ |

---

## USSD

| Method | Endpoint |
|----------|----------|
| POST | /api/v1/ussd/ |
| POST | /api/v1/ussd/confirm-donation/ |

---

## Verification

| Method | Endpoint |
|----------|----------|
| POST | /api/v1/verification/upload-id/ |
| GET | /api/v1/verification/status/ |
| GET | /api/v1/verification/manual-review/ |
| POST | /api/v1/verification/manual-review/{verification_id}/ |

---

## Third Party Integrations

| Method | Endpoint |
|----------|----------|
| POST | /api/v1/third-party/apply/ |
| GET | /api/v1/third-party/applications/ |
| POST | /api/v1/third-party/applications/{app_id}/review/ |
| GET | /api/v1/third-party/data/ |

---

## Audit Logs

| Method | Endpoint |
|----------|----------|
| GET | /api/v1/audit/logs/ |

## Authentication

```http
POST /api/v1/auth/register/donor/
POST /api/v1/auth/register/hospital/
POST /api/v1/auth/login/
POST /api/v1/auth/logout/
POST /api/v1/auth/token/refresh/
POST /api/v1/auth/verify-otp/
POST /api/v1/auth/resend-otp/
POST /api/v1/auth/change-password/
POST /api/v1/auth/forgot-password/
POST /api/v1/auth/reset-password/
```

---

## Donors

```http
POST   /api/v1/donors/profile/
GET    /api/v1/donors/profile/
PATCH  /api/v1/donors/profile/
DELETE /api/v1/donors/profile/

PATCH  /api/v1/donors/availability/

GET    /api/v1/donors/dashboard/
```

---

## Verification

```http
POST /api/v1/verification/upload-id/

GET  /api/v1/verification/status/
```

---

## Donations

```http
POST   /api/v1/donations/

GET    /api/v1/donations/history/

GET    /api/v1/donations/{id}/

PATCH  /api/v1/donations/{id}/

DELETE /api/v1/donations/{id}/
```

---

## Matching

```http
GET  /api/v1/matching/search/blood/

GET  /api/v1/matching/search/organs/

POST /api/v1/matching/contact-request/

GET  /api/v1/matching/contact-requests/

POST /api/v1/matching/contact-requests/{id}/approve/

POST /api/v1/matching/contact-requests/{id}/decline/
```

---

## Hospitals

```http
POST   /api/v1/hospitals/profile/

GET    /api/v1/hospitals/profile/

PATCH  /api/v1/hospitals/profile/

DELETE /api/v1/hospitals/profile/

POST   /api/v1/hospitals/upload-license/

POST   /api/v1/hospitals/staff/

GET    /api/v1/hospitals/staff/

PATCH  /api/v1/hospitals/staff/{id}/

DELETE /api/v1/hospitals/staff/{id}/
```

---

## Subscriptions & Payments

```http
GET  /api/v1/subscriptions/current/

POST /api/v1/subscriptions/

POST /api/v1/subscriptions/cancel/

POST /api/v1/payments/mpesa/stk-push/

POST /api/v1/payments/mpesa/callback/

POST /api/v1/payments/stripe/subscribe/

POST /api/v1/payments/stripe/webhook/
```

---

## Credits & Gamification

```http
GET /api/v1/credits/balance/

GET /api/v1/credits/ledger/

POST /api/v1/credits/redeem/

GET /api/v1/gamification/badges/

GET /api/v1/gamification/leaderboard/
```

---

## Notifications

```http
POST /api/v1/notifications/sms/

POST /api/v1/notifications/email/

GET  /api/v1/notifications/history/
```

---

## USSD

```http
POST /api/v1/ussd/

POST /api/v1/ussd/confirm-donation/

POST /api/v1/ussd/credits/

POST /api/v1/ussd/availability/
```

---

## Third Party

```http
POST /api/v1/third-party/applications/

GET  /api/v1/third-party/applications/{id}/

GET  /api/v1/third-party/datasets/
```

---

## Administration

```http
POST /api/v1/admin/hospitals/{id}/approve/

POST /api/v1/admin/hospitals/{id}/reject/

GET  /api/v1/admin/audit-logs/

GET  /api/v1/admin/metrics/

GET  /api/v1/admin/users/

PATCH /api/v1/admin/users/{id}/

DELETE /api/v1/admin/users/{id}/
```

---

# Security Architecture

## Authentication Security

* JWT authentication
* Refresh token rotation
* Role-based authorization
* Optional MFA for donors
* Mandatory MFA for hospitals

## Encryption

### In Transit

* TLS 1.3
* HTTPS enforced

### At Rest

AES-256 encryption applied to:

* Identity documents
* Insurance information
* Medical records
* Addresses

---

## Audit Logging

All sensitive actions are logged.

Captured metadata:

* User
* Role
* Timestamp
* IP address
* User agent
* Action performed

Audit records are immutable.

---

## Rate Limiting

| Resource         | Limit      |
| ---------------- | ---------- |
| Login Attempts   | 5 failures |
| Donor Searches   | 60/hour    |
| Contact Requests | 20/hour    |
| USSD Sessions    | 10/hour    |

---

## File Security

* Private S3/R2 buckets
* Signed URLs
* 5-minute expiration
* Server-side encryption

---

# Data Protection & Compliance

The platform is designed to comply with:

* Kenya Data Protection Act (2019)
* Privacy by Design principles
* Explicit consent requirements
* Data minimization standards
* Health data protection obligations

Hospitals are contractually required to:

* Use donor data only for medical purposes
* Report breaches immediately
* Avoid retaining donor data unnecessarily
* Participate in compliance audits

---

# Third-Party Integrations

## Africa's Talking

* SMS
* USSD

## Smile Identity

* ID verification
* Liveness detection

## M-Pesa Daraja

* Subscription payments

## Stripe

* Card payments

## SendGrid

* Transactional emails

## AWS S3 / Cloudflare R2

* Secure file storage

---

# Testing

Run all tests:

```bash
python manage.py test
```

Run application tests:

```bash
python manage.py test apps.donors
```

Coverage:

```bash
coverage run manage.py test

coverage report
```

---

# Deployment

Recommended stack:

* Nginx
* Gunicorn
* PostgreSQL
* Redis
* Celery

Collect static files:

```bash
python manage.py collectstatic
```

Run Gunicorn:

```bash
gunicorn config.wsgi:application
```

Supported deployment platforms:

* Railway
* Render
* AWS EC2
* DigitalOcean

---

# Contributing

1. Create feature branch.
2. Write tests.
3. Run linting.
4. Submit pull request.
5. Await review.

---

# License

Proprietary Software

Copyright © DamuLink.

All rights reserved.
