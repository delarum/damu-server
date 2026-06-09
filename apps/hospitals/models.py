from django.db import models
from apps.accounts.models import User


class HospitalProfile(models.Model):

    class FacilityType(models.TextChoices):
        PUBLIC     = "public",     "Public"
        PRIVATE    = "private",    "Private"
        NGO        = "ngo",        "NGO"
        BLOOD_BANK = "blood_bank", "Blood Bank"

    class ApprovalStatus(models.TextChoices):
        PENDING  = "pending",  "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        SUSPENDED = "suspended", "Suspended"

    class SubscriptionTier(models.TextChoices):
        STARTER      = "starter",      "Starter"
        PROFESSIONAL = "professional", "Professional"
        ENTERPRISE   = "enterprise",   "Enterprise"
        PUBLIC       = "public",       "Public Hospital"

    # Core
    admin            = models.OneToOneField(User, on_delete=models.CASCADE, related_name="hospital_profile")
    facility_name    = models.CharField(max_length=255)
    facility_type    = models.CharField(max_length=20, choices=FacilityType.choices)
    license_number   = models.CharField(max_length=100, unique=True)
    year_established = models.PositiveIntegerField(blank=True, null=True)

    # Location
    address          = models.TextField()
    county           = models.CharField(max_length=100)
    lat              = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    lng              = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    # Contact
    phone            = models.CharField(max_length=20, blank=True)
    email            = models.EmailField(blank=True)
    website          = models.URLField(blank=True)

    # Approval
    approval_status  = models.CharField(
        max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING
    )
    rejection_reason = models.TextField(blank=True)
    approved_at      = models.DateTimeField(blank=True, null=True)
    approved_by      = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_hospitals"
    )

    # Subscription
    subscription_tier    = models.CharField(
        max_length=20, choices=SubscriptionTier.choices, default=SubscriptionTier.STARTER
    )
    subscription_status  = models.CharField(max_length=20, default="inactive")
    subscription_expires = models.DateTimeField(blank=True, null=True)
    search_quota         = models.PositiveIntegerField(default=0)   # searches used this month
    search_limit         = models.PositiveIntegerField(default=100) # based on tier

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "hospital_profiles"

    def __str__(self):
        return f"{self.facility_name} ({self.approval_status})"

    @property
    def is_active_subscriber(self):
        from django.utils import timezone
        return (
            self.approval_status == self.ApprovalStatus.APPROVED
            and self.subscription_status == "active"
            and self.subscription_expires
            and self.subscription_expires > timezone.now()
        )

    @property
    def searches_remaining(self):
        return max(0, self.search_limit - self.search_quota)

    TIER_LIMITS = {
        "starter":      100,
        "professional": 500,
        "enterprise":   999999,
        "public":       300,
    }

    TIER_PRICES = {
        "starter":      5000,
        "professional": 15000,
        "enterprise":   40000,
        "public":       1500,
    }


class HospitalDocument(models.Model):
    """Stores uploaded verification documents for a hospital."""

    class DocType(models.TextChoices):
        REGISTRATION  = "registration",  "Registration Certificate"
        LICENSE       = "license",       "Operating License"
        TAX           = "tax",           "Tax Compliance Certificate"
        REPRESENTATIVE = "representative", "Representative ID"

    hospital   = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name="documents")
    doc_type   = models.CharField(max_length=20, choices=DocType.choices)
    file       = models.FileField(upload_to="hospital_docs/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hospital_documents"

    def __str__(self):
        return f"{self.hospital.facility_name} — {self.doc_type}"


class HospitalStaff(models.Model):
    """Additional staff members linked to a hospital."""
    hospital   = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name="staff")
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name="hospital_staff")
    added_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hospital_staff"

    def __str__(self):
        return f"{self.user.full_name} @ {self.hospital.facility_name}"