# DamuLink — System Design & Technical Documentation

> **"Damu"** (Swahili for *blood*) — a platform connecting hospitals, blood donors, and organ donors across the country.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [User Roles & Portals](#3-user-roles--portals)
4. [Donor Registration Flow](#4-donor-registration-flow)
5. [Hospital Registration & Subscription Flow](#5-hospital-registration--subscription-flow)
6. [Donor Gamification & Credits System](#6-donor-gamification--credits-system)
7. [Hospital–Donor Matching System](#7-hospitaldnor-matching-system)
8. [USSD Fallback System](#8-ussd-fallback-system)
9. [Security & Data Access Control](#9-security--data-access-control)
10. [Third-Party Data Access (Non-Hospital)](#10-third-party-data-access-non-hospital)
11. [Monetization Model](#11-monetization-model)
12. [API Stack & Integrations](#12-api-stack--integrations)
13. [Django Backend Structure](#13-django-backend-structure)
14. [Database Schema Overview](#14-database-schema-overview)
15. [Compliance & Legal Considerations](#15-compliance--legal-considerations)

---

## 1. Project Overview

DamuLink is a national health infrastructure platform that:

- Connects **hospitals** with registered **blood donors** and **organ donors**
- Enables **hospital-to-hospital** blood/organ resource sharing
- Provides a **gamified donor experience** to encourage and sustain donor participation
- Awards donors **redeemable health credits** for their contributions
- Offers a **USSD fallback** so hospitals can reach donors even without internet
- Enforces **strict, tiered data access controls** to protect donor privacy

The platform is designed to be **indispensable to hospitals** by being the single national source of truth for donor availability, making it harder to function without it than with it.

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                        DamuLink Platform                  │
│                                                          │
│  ┌───────────────┐        ┌──────────────────────────┐   │
│  │  Donor Portal │        │     Hospital Portal       │   │
│  │  (Gamified)   │        │  (Clinical Dashboard)     │   │
│  └──────┬────────┘        └────────────┬─────────────┘   │
│         │                              │                  │
│         └──────────┬───────────────────┘                  │
│                    │                                      │
│           ┌────────▼──────────┐                           │
│           │   Django REST API  │                           │
│           │   (Core Backend)  │                           │
│           └────────┬──────────┘                           │
│                    │                                      │
│    ┌───────────────┼────────────────────┐                 │
│    │               │                    │                 │
│  ┌─▼──────┐  ┌─────▼──────┐  ┌─────────▼────┐           │
│  │ Postgres│  │   Redis    │  │  Celery       │           │
│  │ (Main) │  │  (Cache/   │  │  (Async Tasks)│           │
│  │        │  │  Sessions) │  │               │           │
│  └────────┘  └────────────┘  └───────────────┘           │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │               External Integrations               │    │
│  │  USSD Gateway | SMS | Payment | Document OCR |   │    │
│  │  Mapping API  | Health Insurance APIs            │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.x + Django REST Framework |
| Database | PostgreSQL (primary), Redis (cache, sessions, queues) |
| Task Queue | Celery + Redis |
| Authentication | JWT (SimpleJWT) + OAuth2 (hospital SSO) |
| Storage | AWS S3 or Cloudflare R2 (documents, IDs) |
| USSD | Africa's Talking USSD API |
| SMS | Africa's Talking SMS / Twilio |
| Payments | Stripe + M-Pesa (Daraja API) |
| Maps | Google Maps Platform / OpenStreetMap (Leaflet) |
| Document Verification | Smile Identity / Jumio OCR |
| Email | SendGrid / AWS SES |
| Hosting | Railway / Render / AWS EC2 (behind Nginx + Gunicorn) |

---

## 3. User Roles & Portals

### 3.1 Donor Portal (Gamified)

Designed to feel like a **social health community**, not a medical form. Think: clean UI, progress bars, badges, impact counters.

**Who registers here:**
- Blood donors
- Organ donors
- People who are both

**What they see:**
- Personal health profile & donor card
- Donation history timeline
- Credit balance & redemption options
- Community leaderboard (optional, opt-in)
- Impact stats ("Your blood has helped X people this year")
- Upcoming donation eligibility countdown
- Nearby hospitals that accept walk-in donations
- Notification feed (urgent calls, reminders)

---

### 3.2 Hospital Portal (Clinical Dashboard)

Designed to feel like a **professional clinical tool** — clean, fast, data-dense.

**Who registers here:**
- Public hospitals
- Private hospitals
- Blood banks
- Medical facilities with verified licenses

**What they see:**
- National donor search (filter by blood type, location, organ type, availability)
- Hospital network: see nearby hospitals' blood stock levels (if they share)
- Donor contact initiation (triggers anonymized outreach; direct contact only after donor consent)
- Request management dashboard
- Subscription & billing management
- Audit logs (who searched what, when)
- Analytics: donor density maps by region, response rates, etc.

---

### 3.3 Admin Portal (Internal DamuLink Staff)

- Approve/reject hospital registrations
- Review third-party data access applications
- Monitor USSD usage
- Manage credit redemption disputes
- System health monitoring

---

## 4. Donor Registration Flow

### 4.1 Registration Steps

**Step 1 — Account Creation**
- Full legal name
- Phone number (becomes primary identifier, used for USSD fallback)
- National ID number or Passport number
- Date of birth
- Email (optional but recommended)

**Step 2 — Identity Verification**
- Upload: National ID (front & back), Passport, or Alien ID
- Selfie photo for liveness check
- Verification via **Smile Identity** or **Jumio** (automated OCR + face match)
- Manual fallback: admin review queue for failed automated checks

**Step 3 — Medical & Donor Profile**
- Blood type (ABO + Rhesus: A+, A−, B+, B−, AB+, AB−, O+, O−)
- Donor type: Blood only / Organ only / Both
- If organ donor: specify which organs (kidney, liver, cornea, heart, bone marrow, etc.)
- Known medical conditions (optional, used for eligibility screening)
- Last donation date (if previously donated elsewhere)

**Step 4 — Location & Contact**
- County / Sub-county / Town
- Physical address (home or work — whichever they prefer to be contacted at)
- GPS coordinates (captured via browser geolocation or manually pinned on map)
- Preferred contact method: call / SMS / WhatsApp
- Emergency contact (name + phone)

**Step 5 — Health Insurance (Optional)**
- Insurance provider (e.g., SHA, Jubilee Health, AAR, NHIF/SHIF, Britam, CIC, Madison)
- Policy/member number
- This is used to show hospitals relevant coverage when a donor is being contacted

**Step 6 — Consent & Privacy**
- Informed consent for data sharing with verified hospitals
- Option: allow contact for urgent requests only / all requests
- Option: appear on community leaderboard (anonymous by default)
- Terms & Privacy Policy acceptance

**Step 7 — Gamification Onboarding**
- Assign a donor "Hero Class" (e.g., "Rookie Lifesaver" to start)
- Show welcome animation + first badge ("First Step")
- Brief tutorial of the donor dashboard

---

### 4.2 Donor Eligibility Rules (System-Enforced)

| Rule | Logic |
|---|---|
| Blood donation cooldown | 56 days (8 weeks) after whole blood donation |
| Platelet cooldown | 7 days |
| Age gate | 18–65 years (configurable per organ type) |
| Weight minimum | 50 kg (flagged at registration, verified at donation center) |
| Organ donor cooldown | N/A — organs are one-time; system marks as "pledged" |

The system automatically greys out a donor's profile from hospital search during their cooldown period and re-enables it automatically.

---

## 5. Hospital Registration & Subscription Flow

### 5.1 Registration Steps

**Step 1 — Facility Information**
- Hospital name
- Facility type: Public / Private / NGO / Blood Bank
- Physical address + GPS pin
- Facility license number (Kenya: issued by Kenya Medical Practitioners and Dentists Council / Ministry of Health)
- Year established

**Step 2 — Document Uploads**
- Facility registration certificate
- Operating license (current year)
- Tax compliance certificate (KRA PIN certificate)
- Authorized representative's ID + staff ID / letter of authority

**Step 3 — Authorized Representative**
- Full name, title, email, phone
- This person becomes the hospital's primary admin account

**Step 4 — Review & Approval**
- DamuLink admin reviews documents (SLA: 2 business days)
- Email + SMS notification on approval/rejection
- Rejection includes reason + resubmission instructions

**Step 5 — Subscription & Payment**
- On approval, hospital is prompted to subscribe
- Hospital cannot access the donor database until subscribed

---

### 5.2 Subscription Tiers

| Tier | Monthly Fee | Searches/Month | Features |
|---|---|---|---|
| **Starter** | KES 5,000 | 100 donor searches | Basic search, SMS contact initiation |
| **Professional** | KES 15,000 | 500 donor searches | + Organ donor access, hospital network, analytics |
| **Enterprise** | KES 40,000 | Unlimited | + API access, dedicated account manager, SLA uptime guarantee |
| **Public Hospital** | KES 1,500 | 300 donor searches | Subsidized for government-registered facilities |

Payments via **M-Pesa Daraja API (STK Push)** or **card (Stripe)**.

Auto-renewal with 7-day advance warning. Lapsed hospitals lose search access but retain their account.

---

## 6. Donor Gamification & Credits System

### 6.1 Blood Donor Credits

Every confirmed blood donation earns credits:

| Action | Credits Earned |
|---|---|
| First-ever donation | 200 credits (welcome bonus) |
| Whole blood donation | 100 credits |
| Platelet donation | 150 credits |
| Plasma donation | 120 credits |
| Referring a new donor (who donates) | 50 credits |
| Completing profile 100% | 30 credits |
| Responding to an urgent hospital request | 75 bonus credits |

**Milestones & Badges:**

| Donations | Badge | Title |
|---|---|---|
| 1 |  First Drop | Rookie Lifesaver |
| 3 |  Triple Pulse | Bronze Donor |
| 5 |  High Five | Silver Lifesaver |
| 10 |  Decade Donor | Gold Guardian |
| 20 |  Legend | Platinum Hero |
| 50 |  Immortal | Damu Legend |

**Credit Redemption:**
- Credits are redeemable at any partnered hospital as partial payment against bills
- 100 credits = KES 100 equivalent (adjustable by DamuLink admin)
- Can be used for outpatient bills, lab tests, pharmacy
- Cannot be cashed out (health-use only, prevents abuse)
- Credits expire after 3 years of inactivity

---

### 6.2 Organ Donor Incentives

Since organ donation is typically a one-time posthumous act, incentives work differently:

**Living organ donors (e.g., kidney, partial liver):**
- Awarded a significant one-time credit grant (e.g., 5,000 credits = KES 5,000)
- Lifetime "Hero Donor" badge on profile
- Priority access for the donor themselves if they ever need blood at a partnered hospital (flagged in their profile)
- Optional: DamuLink can partner with insurance providers for preferential premiums for registered organ donors (future phase)

**Pledged organ donors (posthumous):**
- Receive "Pledged Hero" status on their profile
- Family of a deceased pledged donor who donates receives a one-time credit grant (1,000 credits) redeemable by any registered next-of-kin on DamuLink
- Future phase: partnership with funeral homes for discounted services

---

### 6.3 Gamification Feed & Social Features

- Activity feed: "You just unlocked the Silver Lifesaver badge!"
- Community stats: "1,204 units of blood donated nationally this week"
- Optional: Connect with other donors (no medical info shown, just badges + first name)
- Urgent blood calls: Donors opted into urgent alerts receive a push notification and SMS when a hospital near them has a critical need for their blood type

---

## 7. Hospital–Donor Matching System

### 7.1 Search & Filter

Hospitals search the donor database with:

| Filter | Options |
|---|---|
| Blood type | ABO + Rh (all 8 types) |
| Donation type | Blood / Specific organ |
| Location | Radius from hospital (5km, 10km, 25km, 50km, national) |
| Availability | Available now / Available after [date] |
| Last donation | Never donated / Donated before |
| Contact preference | Call / SMS / WhatsApp |

Results show:
- Donor's first name + last initial (e.g., "James M.")
- Blood type
- Distance from hospital
- Last donation date
- Contact preference
- Credits earned (as a trust signal)
- Insurance provider (relevant for hospital billing)

**Full contact details are only revealed after the hospital initiates a formal contact request**, which is logged in the audit trail.

---

### 7.2 Contact Initiation

1. Hospital clicks "Contact Donor" on a matched result
2. System logs the request (timestamp, hospital ID, donor ID, reason)
3. Donor receives an SMS/WhatsApp: *"[Hospital Name] needs your help. They are looking for [blood type] blood donors urgently. Reply YES to share your contact or NO to decline."*
4. If donor replies YES → hospital receives full contact details
5. If donor replies NO or no reply in 2 hours → marked as unavailable; hospital can try next match
6. Donors can set auto-accept for emergency requests in their settings

---

### 7.3 Hospital-to-Hospital Network

Hospitals can also post blood stock availability/needs:

- "Nairobi West Hospital has 12 units of O+ available — willing to transfer"
- "Kenyatta National Hospital urgently needs AB- platelets"

Only verified, subscribed hospitals see this board. Stock updates can be done manually or via API integration with hospital LIMS (Lab Information Management System).

---

## 8. USSD Fallback System

### 8.1 Why USSD?

Many hospitals, especially rural public facilities, have unreliable internet. Donors may also have feature phones. USSD works on any mobile network with no data required.

### 8.2 Hospital USSD Flow

Dial: `*384*DAMULINK#` (example shortcode via Africa's Talking)

```
Welcome to DamuLink
1. Search for blood donor
2. Search for organ donor
3. Post urgent need
4. Check my subscription
5. Exit
```

Selecting "1. Search for blood donor":
```
Enter blood type:
1. O+   2. O-
3. A+   4. A-
5. B+   6. B-
7. AB+  8. AB-
```

After selection:
```
Found 3 donors within 10km
Donor 1: James M. | O+ | 4.2km
Press 1 to contact, 2 for next
```

Contact triggers an automated SMS to the donor.

### 8.3 Donor USSD Flow

Donors can also use USSD to:
- Check their credit balance
- Update their availability status (on/off)
- Confirm a donation (if the hospital has a USSD-based confirmation code)

### 8.4 Implementation

- Provider: **Africa's Talking USSD API**
- Django handles USSD sessions via a dedicated endpoint: `POST /api/ussd/`
- Session state stored in Redis (USSD sessions are stateful per phone number)
- USSD gateway sends POST requests with `sessionId`, `phoneNumber`, `serviceCode`, `text`
- Response must be returned within **1 second** (use async where needed)

```python
# Example Django USSD view
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import redis

@csrf_exempt
def ussd_callback(request):
    session_id = request.POST.get('sessionId')
    phone = request.POST.get('phoneNumber')
    text = request.POST.get('text', '')
    
    # Parse menu navigation from `text` (e.g., "1*2*O+")
    # Return CON (continue) or END (terminate session)
    response = process_ussd_menu(session_id, phone, text)
    return HttpResponse(response, content_type='text/plain')
```

---

## 9. Security & Data Access Control

### 9.1 Core Principles

- **Least privilege**: Every actor gets only what they need, no more
- **Audit everything**: Every access to donor PII is logged with who, what, when, why
- **Encryption at rest and in transit**: All donor documents and PII encrypted
- **Zero trust by default**: External systems must authenticate on every request

### 9.2 Data Classification

| Data Class | Examples | Access Level |
|---|---|---|
| **Public** | Total donors by county, blood type distribution stats | Anyone |
| **Restricted** | First name, blood type, distance, credit score | Subscribed hospitals only |
| **Confidential** | Full name, phone, address, workplace | Only after donor consent per request |
| **Sensitive** | ID documents, health conditions, insurance details | Hospital must log formal reason; admin-auditable |
| **Critical** | Biometric data (selfie), password hashes | Never exposed via API; internal only |

### 9.3 Authentication & Authorization

- **Donors**: Email/phone + password, with 2FA via OTP (SMS)
- **Hospitals**: Email + password + 2FA (mandatory for hospital accounts)
- **API**: JWT short-lived access tokens (15 min) + refresh tokens (7 days)
- **Hospital API access (Enterprise)**: API keys scoped to specific endpoints, rate-limited

### 9.4 Role-Based Access Control (RBAC)

| Role | Permissions |
|---|---|
| `donor` | Own profile CRUD, view own credits, update availability |
| `hospital_staff` | Search donors (restricted view), initiate contact requests |
| `hospital_admin` | All staff permissions + billing, add/remove staff, view audit logs |
| `damulink_admin` | Full platform access, approve hospitals, review third-party requests |
| `third_party_researcher` | View anonymized aggregate data only (post-approval) |

### 9.5 Document Security

- All uploaded documents (IDs, passports, facility licenses) stored in **private S3/R2 buckets**
- Documents never served via public URL; accessed via **signed time-limited URLs** (valid for 5 minutes)
- Documents are encrypted using **AES-256** before storage
- Only DamuLink admins and the document owner can view original files
- Hospitals can see whether a donor's identity is "Verified" but never the document itself

### 9.6 Audit Trail

Every sensitive action is logged to an append-only `AuditLog` table:

```python
class AuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    actor_role = models.CharField(max_length=50)
    action = models.CharField(max_length=100)  # e.g., "donor_search", "contact_initiated"
    target_donor = models.ForeignKey(DonorProfile, null=True, on_delete=models.SET_NULL)
    target_hospital = models.ForeignKey(HospitalProfile, null=True, on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)  # additional context
```

Audit logs are **immutable** — no UPDATE or DELETE allowed on this table (enforced at DB level via triggers).

### 9.7 Rate Limiting

- Donor search: max 60 searches/hour per hospital account
- Contact initiation: max 20/hour per hospital (prevent spam)
- USSD: max 10 sessions/hour per phone number
- Login attempts: locked after 5 failed attempts; CAPTCHA on 3rd

---

## 10. Third-Party Data Access (Non-Hospital)

Any entity that is **not a registered, subscribed hospital** and wishes to access donor data (e.g., researchers, NGOs, government health agencies, insurance companies, journalists) must go through a formal application process.

### 10.1 Application Process

**Step 1 — Organization Registration**
- Organization name, type, country
- Registration certificate / proof of incorporation
- Physical address and contacts

**Step 2 — Purpose Declaration**
- Describe the specific data needed
- State the purpose (academic research, public health study, insurance actuarial, etc.)
- Duration of access needed
- Who within the organization will access the data

**Step 3 — Legal Documents Required**
- Signed **Data Processing Agreement (DPA)** with DamuLink
- Signed **Non-Disclosure Agreement (NDA)**
- Ethics approval certificate (for academic/research applicants)
- Authorization letter from organization's board/CEO
- Data Protection Officer's (DPO) details (required under Kenya Data Protection Act 2019)

**Step 4 — Personal Vetting**
- Each named individual who will access data must submit:
  - National ID or Passport copy
  - Staff/employee ID
  - Letter of employment/affiliation
  - Personal NDA

**Step 5 — DamuLink Review**
- Legal team reviews all documents (SLA: 5–10 business days)
- May request a video call for clarification
- Approved or rejected with written reasons

**Step 6 — Access Granted**
- Approved researchers get access to **anonymized, aggregate data only** (no PII)
- All fields that could identify a donor are stripped or generalized (e.g., sub-county level instead of street address)
- Access is time-limited (max 6 months, renewable)
- Every query is logged
- Access can be revoked at any time for breach of terms

**Note:** No third party ever gets raw, identifiable donor data. Not even government agencies unless compelled by a court order — in which case, DamuLink will notify the donor where legally permissible.

---

## 11. Monetization Model

### 11.1 Primary Revenue: Hospital Subscriptions

As detailed in Section 5.2. This is the core revenue stream.

### 11.2 Secondary Revenue Streams

**Transaction Fee on Credit Redemptions**
- When a donor redeems credits at a hospital, DamuLink charges the hospital a small processing fee (e.g., 5% of credit value redeemed)
- This is offset by the value hospitals get from having engaged, regular donors

**Hospital-to-Hospital Facilitation Fee**
- When blood stock is transferred between hospitals via DamuLink's network, a small logistics facilitation fee can be charged

**Premium Donor Features (Future Phase)**
- "DamuLink Plus" donor subscription: KES 99/month for priority urgent-request notifications, detailed impact reports, premium badges, and a physical donor card
- Entirely optional — core donation features always free

**Third-Party Data Access Fees**
- Research/NGO access to anonymized aggregate data: tiered fee based on dataset size and duration
- Insurance actuary access: custom enterprise pricing

**Sponsored Urgent Campaigns**
- Hospitals or health organizations can pay to pin an urgent blood need to the top of the donor notification feed
- Donors always see this as a "Sponsored Urgent Need" (transparent labeling)

---

## 12. API Stack & Integrations

### 12.1 Africa's Talking

**Purpose:** USSD sessions + SMS notifications

```python
# Install: pip install africastalking
import africastalking

africastalking.initialize(username='damulink', api_key=settings.AT_API_KEY)
sms = africastalking.SMS
sms.send("Your blood is urgently needed at Kenyatta Hospital. Reply YES to share your contacts.", ["+254712345678"])
```

**Endpoints used:**
- USSD callback handler (webhook)
- SMS (outbound to donors)
- Airtime API (future: small airtime reward for responding to urgent calls)

---

### 12.2 Smile Identity (or Jumio)

**Purpose:** ID document verification + liveness check for donors

```python
# Smile Identity Web SDK for frontend liveness + ID capture
# Backend validates via REST API:
import requests

def verify_identity(id_image_base64, selfie_base64, id_type, country):
    payload = {
        "partner_id": settings.SMILE_PARTNER_ID,
        "id_type": id_type,  # NATIONAL_ID, PASSPORT, etc.
        "country": "KE",
        "id_number": "...",
        "selfie_image": selfie_base64,
        "id_image": id_image_base64,
    }
    response = requests.post("https://api.smileidentity.com/v1/id_verification", json=payload, 
                              headers={"Authorization": f"Bearer {settings.SMILE_API_KEY}"})
    return response.json()
```

---

### 12.3 M-Pesa Daraja API (Safaricom)

**Purpose:** Hospital subscription payments via M-Pesa STK Push

```python
# Install: pip install mpesa-daraja (or implement directly)
def initiate_stk_push(phone, amount, account_ref, description):
    token = get_mpesa_access_token()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": generate_password(timestamp),
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": "https://damulink.co.ke/api/payments/mpesa/callback/",
        "AccountReference": account_ref,
        "TransactionDesc": description
    }
    response = requests.post(settings.MPESA_STK_URL, json=payload,
                              headers={"Authorization": f"Bearer {token}"})
    return response.json()
```

---

### 12.4 Stripe

**Purpose:** Card payments for hospitals (credit/debit cards)

```python
# Install: pip install stripe
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_subscription(customer_id, price_id):
    return stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": price_id}],
    )
```

---

### 12.5 Google Maps Platform

**Purpose:** Donor location display, distance calculation, hospital finder

```python
# Distance Matrix for proximity search
def get_distance_km(origin_lat, origin_lng, dest_lat, dest_lng):
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{origin_lat},{origin_lng}",
        "destinations": f"{dest_lat},{dest_lng}",
        "key": settings.GOOGLE_MAPS_API_KEY
    }
    response = requests.get(url, params=params)
    # Parse distance from response
    return response.json()
```

For privacy: **donor GPS is never exposed to hospitals**. Distance is calculated server-side and only the result (e.g., "4.2km away") is shown.

---

### 12.6 SendGrid / AWS SES

**Purpose:** Transactional emails (registration confirmation, subscription invoices, urgent alerts, approval notifications)

```python
# Django settings
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = settings.SENDGRID_API_KEY
```

---

### 12.7 AWS S3 / Cloudflare R2

**Purpose:** Secure document storage

```python
# django-storages + boto3
# settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'damulink-secure-docs'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = 'private'  # CRITICAL: never public
AWS_S3_OBJECT_PARAMETERS = {'ServerSideEncryption': 'AES256'}
```

---

## 13. Django Backend Structure

```
damulink/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/          # User model, auth (JWT), roles
│   ├── donors/            # DonorProfile, organ/blood specifics, credits
│   ├── hospitals/         # HospitalProfile, subscriptions, staff
│   ├── matching/          # Search engine, contact request workflow
│   ├── gamification/      # Badges, milestones, credit ledger
│   ├── ussd/              # USSD session handler, menu trees
│   ├── payments/          # M-Pesa, Stripe, invoices
│   ├── notifications/     # SMS, email, push notification dispatch
│   ├── verification/      # ID verification webhook handlers
│   ├── audit/             # AuditLog model + middleware
│   └── third_party/       # Third-party access application workflow
├── utils/
│   ├── encryption.py
│   ├── geo.py
│   └── sms.py
└── manage.py
```

---


# 13.1 API Architecture Overview

All backend communication is handled through a versioned REST API.

Base URL:

```bash
https://api.damulink.co.ke/api/v1/
```

### API Standards

| Standard        | Implementation                   |
| --------------- | -------------------------------- |
| Response Format | JSON                             |
| Authentication  | JWT Bearer Tokens                |
| Rate Limiting   | DRF Throttling                   |
| API Versioning  | URI-based (`/api/v1/`)           |
| Pagination      | Limit/Offset                     |
| Permissions     | Role-Based Access Control (RBAC) |
| Validation      | DRF Serializers                  |
| Async Jobs      | Celery + Redis                   |
| File Uploads    | Multipart/Form-Data              |
| Audit Logging   | Middleware + Model Hooks         |

---

# 13.2 Authentication Endpoints

## Register Donor

### Endpoint

```http
POST /api/v1/auth/register/donor/
```

### Request

```json
{
  "full_name": "James Mwangi",
  "phone": "+254712345678",
  "email": "james@example.com",
  "password": "StrongPassword123",
  "national_id": "34567890",
  "date_of_birth": "1998-03-12"
}
```

### Response

```json
{
  "message": "Donor account created successfully",
  "user_id": 41,
  "otp_sent": true
}
```

---

## Register Hospital

### Endpoint

```http
POST /api/v1/auth/register/hospital/
```

### Request

```json
{
  "facility_name": "Nairobi West Hospital",
  "facility_type": "private",
  "email": "admin@nairobiwesthospital.com",
  "phone": "+254700000001",
  "password": "SecurePass123",
  "license_number": "KMPDC-9087"
}
```

### Response

```json
{
  "message": "Hospital registration submitted for review",
  "hospital_id": 18,
  "status": "pending_review"
}
```

---

## Login

### Endpoint

```http
POST /api/v1/auth/login/
```

### Request

```json
{
  "phone": "+254712345678",
  "password": "StrongPassword123"
}
```

### Response

```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": 41,
    "role": "donor",
    "is_verified": true
  }
}
```

---

## Refresh Token

### Endpoint

```http
POST /api/v1/auth/token/refresh/
```

### Request

```json
{
  "refresh": "jwt_refresh_token"
}
```

### Response

```json
{
  "access": "new_access_token"
}
```

---

## Logout

### Endpoint

```http
POST /api/v1/auth/logout/
```

### Headers

```http
Authorization: Bearer <access_token>
```

### Request

```json
{
  "refresh": "jwt_refresh_token"
}
```

### Response

```json
{
  "message": "Logged out successfully"
}
```

---

# 13.3 Donor CRUD Endpoints

## Create Donor Profile

### Endpoint

```http
POST /api/v1/donors/profile/
```

### Headers

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Request

```json
{
  "blood_type": "O+",
  "donor_type": "both",
  "organs_pledged": ["kidney", "cornea"],
  "county": "Nairobi",
  "town": "Westlands",
  "lat": -1.2676,
  "lng": 36.8108,
  "preferred_contact_method": "sms",
  "insurance_provider": "SHA"
}
```

### Response

```json
{
  "message": "Donor profile created successfully",
  "profile_id": 93
}
```

---

## Retrieve Donor Profile

### Endpoint

```http
GET /api/v1/donors/profile/
```

### Response

```json
{
  "id": 93,
  "full_name": "James Mwangi",
  "blood_type": "O+",
  "credits": 450,
  "badge": "Silver Lifesaver",
  "availability_status": true,
  "cooldown_until": null
}
```

---

## Update Donor Profile

### Endpoint

```http
PATCH /api/v1/donors/profile/
```

### Request

```json
{
  "town": "Kilimani",
  "preferred_contact_method": "whatsapp"
}
```

### Response

```json
{
  "message": "Profile updated successfully"
}
```

---

## Delete Donor Account

### Endpoint

```http
DELETE /api/v1/donors/profile/
```

### Response

```json
{
  "message": "Donor account scheduled for deletion"
}
```

---

# 13.4 Hospital CRUD Endpoints

## Create Hospital Profile

### Endpoint

```http
POST /api/v1/hospitals/profile/
```

### Request

```json
{
  "facility_name": "Aga Khan Hospital",
  "facility_type": "private",
  "address": "Parklands, Nairobi",
  "license_number": "AGK-0090",
  "lat": -1.259,
  "lng": 36.804
}
```

### Response

```json
{
  "message": "Hospital profile created successfully"
}
```

---

## Retrieve Hospital Profile

### Endpoint

```http
GET /api/v1/hospitals/profile/
```

### Response

```json
{
  "facility_name": "Aga Khan Hospital",
  "subscription_tier": "professional",
  "subscription_status": "active",
  "expires_at": "2026-09-12"
}
```

---

## Update Hospital Profile

### Endpoint

```http
PATCH /api/v1/hospitals/profile/
```

### Request

```json
{
  "facility_type": "ngo"
}
```

### Response

```json
{
  "message": "Hospital profile updated"
}
```

---

## Delete Hospital Profile

### Endpoint

```http
DELETE /api/v1/hospitals/profile/
```

### Response

```json
{
  "message": "Hospital profile deactivated"
}
```

---

# 13.5 Donor Search & Matching Endpoints

## Search Blood Donors

### Endpoint

```http
GET /api/v1/matching/search/blood/?blood_type=O+&radius=10
```

### Response

```json
{
  "count": 2,
  "results": [
    {
      "donor_id": 93,
      "name": "James M.",
      "blood_type": "O+",
      "distance_km": 4.2,
      "last_donation_date": "2026-02-10",
      "contact_preference": "sms"
    },
    {
      "donor_id": 102,
      "name": "Faith K.",
      "blood_type": "O+",
      "distance_km": 6.1,
      "last_donation_date": "2026-01-21",
      "contact_preference": "call"
    }
  ]
}
```

---

## Search Organ Donors

### Endpoint

```http
GET /api/v1/matching/search/organs/?organ=kidney&radius=50
```

### Response

```json
{
  "count": 1,
  "results": [
    {
      "donor_id": 201,
      "name": "Samuel O.",
      "organ": "kidney",
      "distance_km": 13.7
    }
  ]
}
```

---

## Initiate Contact Request

### Endpoint

```http
POST /api/v1/matching/contact-request/
```

### Request

```json
{
  "donor_id": 93,
  "reason": "Urgent O+ blood requirement"
}
```

### Response

```json
{
  "message": "Contact request initiated",
  "status": "pending_donor_response"
}
```

---

## Retrieve Contact Requests

### Endpoint

```http
GET /api/v1/matching/contact-requests/
```

### Response

```json
{
  "results": [
    {
      "request_id": 19,
      "donor": "James M.",
      "status": "accepted",
      "requested_at": "2026-05-12T11:22:00Z"
    }
  ]
}
```

---

# 13.6 Donation Records CRUD

## Create Donation Record

### Endpoint

```http
POST /api/v1/donations/
```

### Request

```json
{
  "donor_id": 93,
  "hospital_id": 18,
  "donation_type": "whole_blood",
  "donation_date": "2026-05-01"
}
```

### Response

```json
{
  "message": "Donation recorded successfully",
  "credits_awarded": 100
}
```

---

## Retrieve Donation History

### Endpoint

```http
GET /api/v1/donations/history/
```

### Response

```json
{
  "results": [
    {
      "donation_id": 11,
      "type": "whole_blood",
      "hospital": "Nairobi Hospital",
      "date": "2026-05-01",
      "credits_awarded": 100
    }
  ]
}
```

---

## Update Donation Record

### Endpoint

```http
PATCH /api/v1/donations/11/
```

### Request

```json
{
  "donation_type": "platelet"
}
```

### Response

```json
{
  "message": "Donation record updated"
}
```

---

## Delete Donation Record

### Endpoint

```http
DELETE /api/v1/donations/11/
```

### Response

```json
{
  "message": "Donation record removed"
}
```

---

# 13.7 Credits & Gamification Endpoints

## Retrieve Credit Balance

### Endpoint

```http
GET /api/v1/credits/balance/
```

### Response

```json
{
  "credits": 850,
  "cash_equivalent": 850
}
```

---

## Retrieve Credit Ledger

### Endpoint

```http
GET /api/v1/credits/ledger/
```

### Response

```json
{
  "results": [
    {
      "transaction_type": "earn",
      "amount": 100,
      "reason": "Whole blood donation",
      "created_at": "2026-05-01T09:00:00Z"
    }
  ]
}
```

---

## Retrieve Badges

### Endpoint

```http
GET /api/v1/gamification/badges/
```

### Response

```json
{
  "results": [
    {
      "badge": "Silver Lifesaver",
      "earned_at": "2026-04-12"
    }
  ]
}
```

---

# 13.8 Subscription & Payment Endpoints

## Initiate M-Pesa STK Push

### Endpoint

```http
POST /api/v1/payments/mpesa/stk-push/
```

### Request

```json
{
  "phone": "+254700000001",
  "amount": 15000,
  "tier": "professional"
}
```

### Response

```json
{
  "message": "STK push initiated",
  "checkout_request_id": "ws_CO_123456789"
}
```

---

## Stripe Subscription

### Endpoint

```http
POST /api/v1/payments/stripe/subscribe/
```

### Request

```json
{
  "payment_method_id": "pm_123456",
  "tier": "enterprise"
}
```

### Response

```json
{
  "message": "Subscription created",
  "subscription_id": "sub_98765"
}
```

---

## Retrieve Subscription Details

### Endpoint

```http
GET /api/v1/subscriptions/current/
```

### Response

```json
{
  "tier": "professional",
  "status": "active",
  "expires_at": "2026-12-01"
}
```

---

# 13.9 USSD Backend Endpoints

## USSD Callback Endpoint

### Endpoint

```http
POST /api/v1/ussd/
```

### Request Payload (Africa's Talking)

```json
{
  "sessionId": "ATUid_001",
  "serviceCode": "*384*123#",
  "phoneNumber": "+254712345678",
  "text": "1*2"
}
```

### Response

```text
CON Select donor type
1. Blood
2. Organ
```

---

## Confirm Donation via USSD

### Endpoint

```http
POST /api/v1/ussd/confirm-donation/
```

### Request

```json
{
  "phone": "+254712345678",
  "confirmation_code": "DML-0091"
}
```

### Response

```json
{
  "message": "Donation confirmed",
  "credits_awarded": 100
}
```

---

# 13.10 Notification Endpoints

## Send SMS Alert

### Endpoint

```http
POST /api/v1/notifications/sms/
```

### Request

```json
{
  "recipient": "+254712345678",
  "message": "Urgent O+ blood needed at Nairobi Hospital"
}
```

### Response

```json
{
  "message": "SMS queued successfully"
}
```

---

## Send Email Notification

### Endpoint

```http
POST /api/v1/notifications/email/
```

### Request

```json
{
  "email": "james@example.com",
  "subject": "Urgent Donation Request",
  "message": "A hospital near you needs O+ blood urgently."
}
```

### Response

```json
{
  "message": "Email queued"
}
```

---

# 13.11 Admin Management Endpoints

## Approve Hospital Registration

### Endpoint

```http
POST /api/v1/admin/hospitals/18/approve/
```

### Response

```json
{
  "message": "Hospital approved successfully"
}
```

---

## Reject Hospital Registration

### Endpoint

```http
POST /api/v1/admin/hospitals/18/reject/
```

### Request

```json
{
  "reason": "Operating license expired"
}
```

### Response

```json
{
  "message": "Hospital rejected"
}
```

---

## Retrieve Audit Logs

### Endpoint

```http
GET /api/v1/admin/audit-logs/
```

### Response

```json
{
  "results": [
    {
      "actor": "hospital_admin",
      "action": "donor_search",
      "timestamp": "2026-05-12T10:00:00Z",
      "ip_address": "102.89.22.1"
    }
  ]
}
```

---

# 13.12 File Upload Endpoints

## Upload Donor ID Document

### Endpoint

```http
POST /api/v1/verification/upload-id/
```

### Headers

```http
Content-Type: multipart/form-data
```

### Form Fields

```text
front_image
back_image
selfie_image
```

### Response

```json
{
  "message": "Documents uploaded successfully",
  "verification_status": "pending"
}
```

---

## Upload Hospital License

### Endpoint

```http
POST /api/v1/hospitals/upload-license/
```

### Response

```json
{
  "message": "License uploaded successfully"
}
```

---

# 13.13 Error Response Format

All API errors follow a standardized structure.

## Validation Error

```json
{
  "error": true,
  "message": "Validation failed",
  "details": {
    "blood_type": ["This field is required"]
  }
}
```

---

## Unauthorized Error

```json
{
  "error": true,
  "message": "Authentication credentials were not provided"
}
```

---

## Permission Denied

```json
{
  "error": true,
  "message": "You do not have permission to perform this action"
}
```

---

# 13.14 Django REST Framework Structure

## Example Router Configuration

```python
from rest_framework.routers import DefaultRouter
from apps.donors.views import DonorProfileViewSet
from apps.hospitals.views import HospitalProfileViewSet

router = DefaultRouter()
router.register(r'donors', DonorProfileViewSet, basename='donors')
router.register(r'hospitals', HospitalProfileViewSet, basename='hospitals')

urlpatterns = router.urls
```

---

## Example Serializer

```python
from rest_framework import serializers
from .models import DonorProfile

class DonorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonorProfile
        fields = '__all__'
```

---

## Example ViewSet

```python
from rest_framework import viewsets
from .models import DonorProfile
from .serializers import DonorProfileSerializer

class DonorProfileViewSet(viewsets.ModelViewSet):
    queryset = DonorProfile.objects.all()
    serializer_class = DonorProfileSerializer
```

---

# 13.15 Celery Async Tasks

## Example SMS Task

```python
from celery import shared_task
from utils.sms import send_sms

@shared_task
def send_urgent_sms(phone, message):
    send_sms(phone, message)
```

---

## Example Expired Contact Request Task

```python
@shared_task
def expire_contact_requests():
    # Mark requests older than 2 hours as expired
    pass
```

---

# 13.16 Suggested API Permissions Matrix

| Endpoint                     | donor    | hospital_staff | hospital_admin | damulink_admin |
| ---------------------------- | -------- | -------------- | -------------- | -------------- |
| `/auth/register/`            | ✅        | ✅              | ✅              | ✅              |
| `/donors/profile/`           | Own Only | ❌              | ❌              | ✅              |
| `/matching/search/`          | ❌        | ✅              | ✅              | ✅              |
| `/matching/contact-request/` | ❌        | ✅              | ✅              | ✅              |
| `/admin/audit-logs/`         | ❌        | ❌              | ❌              | ✅              |
| `/subscriptions/current/`    | ❌        | ✅              | ✅              | ✅              |
| `/credits/balance/`          | ✅        | ❌              | ❌              | ✅              |

---

# 13.17 Recommended Production Middleware

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'audit.middleware.AuditMiddleware',
]
```

---

# 13.18 Recommended Environment Variables

```env
SECRET_KEY=django-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:password@localhost/damulink
REDIS_URL=redis://localhost:6379/0
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AT_API_KEY=xxx
STRIPE_SECRET_KEY=xxx
MPESA_CONSUMER_KEY=xxx
MPESA_CONSUMER_SECRET=xxx
```

---

# 13.19 API Response Status Codes

| Status Code | Meaning               |
| ----------- | --------------------- |
| 200         | Success               |
| 201         | Resource Created      |
| 400         | Bad Request           |
| 401         | Unauthorized          |
| 403         | Forbidden             |
| 404         | Resource Not Found    |
| 429         | Too Many Requests     |
| 500         | Internal Server Error |

---

# 13.20 Future Backend Enhancements

* GraphQL gateway for enterprise hospitals
* Real-time donor alerts using WebSockets
* AI-powered donor matching prioritization
* Mobile push notifications via Firebase Cloud Messaging (FCM)
* National blood demand forecasting engine
* Multi-country deployment architecture
* Offline-first hospital sync client
* HL7/FHIR interoperability for hospital systems

---

*End of Extended Backend API Documentation*


## 14. Database Schema Overview

### Core Tables

**`users`** — Base auth table (AbstractBaseUser)
- id, phone, email, password_hash, role, is_verified, 2fa_secret, created_at

**`donor_profiles`**
- user_id (FK), blood_type, donor_type, organs_pledged (JSONField), health_conditions (encrypted), insurance_provider, insurance_number (encrypted), lat, lng, address (encrypted), availability_status, cooldown_until, verification_status

**`hospital_profiles`**
- user_id (FK), facility_name, facility_type, license_number, lat, lng, address, subscription_tier, subscription_expires, is_approved

**`donation_records`**
- donor_id (FK), hospital_id (FK), donation_type, donation_date, confirmed_by, credits_awarded

**`credit_ledger`**
- donor_id (FK), transaction_type (earn/redeem), amount, balance_after, related_donation_id, created_at

**`contact_requests`**
- hospital_id (FK), donor_id (FK), reason, status (pending/accepted/declined/expired), requested_at, responded_at

**`subscriptions`**
- hospital_id (FK), tier, amount, payment_method, payment_ref, started_at, expires_at, status

**`audit_logs`**
- actor_id, actor_role, action, target_donor_id, target_hospital_id, ip_address, timestamp, metadata (JSONField)

**`badges`** & **`donor_badges`**
- Badge definitions + many-to-many with donors

---

## 15. Compliance & Legal Considerations

### Kenya Data Protection Act (2019)

DamuLink must comply fully. Key obligations:
- Appoint a **Data Protection Officer (DPO)**
- Register as a **Data Controller** with the Office of the Data Protection Commissioner (ODPC)
- Maintain a **Record of Processing Activities (ROPA)**
- Implement **Privacy by Design** (minimal data collection, purpose limitation)
- Honor **data subject rights**: access, correction, deletion, portability
- 72-hour **breach notification** to ODPC

### Health Data (Sensitive Personal Data)

Blood type, organ pledge, and health conditions are **sensitive personal data** under the Act and require:
- Explicit consent at collection
- Extra security measures (additional encryption layer)
- Separate, distinct consent for any sharing

### Medical Standards

- Blood donation eligibility rules should align with **Kenya National Blood Transfusion Service (KNBTS)** guidelines
- Organ donation should reference **Kenya Transplant Society** and the **Human Tissue Act (Cap. 252)**

### Terms of Service for Hospitals

Hospitals that access donor data are contractually bound to:
- Use data only for the stated medical purpose
- Not store donor PII beyond the immediate need
- Report any breach immediately to DamuLink
- Submit to random audits of their DamuLink usage

Violations result in immediate subscription termination and potential legal action.

---

*Document version: 1.0 | Last updated: May 2026 | DamuLink Internal*