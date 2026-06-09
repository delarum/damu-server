from django.db import models
from apps.accounts.models import User


class IdentityVerification(models.Model):

    class Status(models.TextChoices):
        PENDING  = "pending",  "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        MANUAL   = "manual_review", "Manual Review"

    class IDType(models.TextChoices):
        NATIONAL_ID = "national_id", "National ID"
        PASSPORT    = "passport",    "Passport"
        ALIEN_ID    = "alien_id",    "Alien ID"

    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name="verification")
    id_type         = models.CharField(max_length=20, choices=IDType.choices)
    id_number       = models.CharField(max_length=50)

    # Uploaded documents (stored in private S3/R2)
    front_image     = models.FileField(upload_to="verification/%Y/%m/", blank=True, null=True)
    back_image      = models.FileField(upload_to="verification/%Y/%m/", blank=True, null=True)
    selfie_image    = models.FileField(upload_to="verification/%Y/%m/", blank=True, null=True)

    # Smile Identity / Jumio response
    provider        = models.CharField(max_length=50, default="smile_identity")
    provider_ref    = models.CharField(max_length=100, blank=True)
    provider_result = models.JSONField(default=dict)

    status          = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField(blank=True)

    submitted_at    = models.DateTimeField(auto_now_add=True)
    reviewed_at     = models.DateTimeField(blank=True, null=True)
    reviewed_by     = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_verifications"
    )

    class Meta:
        db_table = "identity_verifications"

    def __str__(self):
        return f"{self.user.full_name} — {self.id_type} ({self.status})"