from django.db import models
from apps.accounts.models import User


class ThirdPartyApplication(models.Model):

    class OrgType(models.TextChoices):
        ACADEMIC   = "academic",   "Academic / Research"
        NGO        = "ngo",        "NGO"
        GOVERNMENT = "government", "Government Agency"
        INSURANCE  = "insurance",  "Insurance Company"
        OTHER      = "other",      "Other"

    class Status(models.TextChoices):
        PENDING  = "pending",  "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        REVOKED  = "revoked",  "Revoked"

    # Organisation details
    org_name        = models.CharField(max_length=255)
    org_type        = models.CharField(max_length=20, choices=OrgType.choices)
    country         = models.CharField(max_length=100, default="Kenya")
    website         = models.URLField(blank=True)
    registration_no = models.CharField(max_length=100, blank=True)

    # Access details
    purpose         = models.TextField()
    data_requested  = models.TextField()
    duration_months = models.PositiveIntegerField(default=6)

    # Legal documents
    dpa_signed      = models.BooleanField(default=False)
    nda_signed      = models.BooleanField(default=False)
    ethics_approved = models.BooleanField(default=False)

    # Contact / DPO
    contact_name    = models.CharField(max_length=255)
    contact_email   = models.EmailField()
    contact_phone   = models.CharField(max_length=20, blank=True)
    dpo_name        = models.CharField(max_length=255, blank=True)
    dpo_email       = models.EmailField(blank=True)

    # Account
    user            = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="third_party_profile"
    )

    # Review
    status          = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField(blank=True)
    reviewed_by     = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_third_party"
    )
    approved_at     = models.DateTimeField(blank=True, null=True)
    access_expires  = models.DateTimeField(blank=True, null=True)

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "third_party_applications"

    def __str__(self):
        return f"{self.org_name} ({self.status})"