from django.db import models
from apps.accounts.models import User
from apps.donors.models import DonorProfile
from apps.hospitals.models import HospitalProfile


class ContactRequest(models.Model):

    class Status(models.TextChoices):
        PENDING  = "pending",  "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        EXPIRED  = "expired",  "Expired"

    hospital     = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name="contact_requests")
    donor        = models.ForeignKey(DonorProfile, on_delete=models.CASCADE, related_name="contact_requests")
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="initiated_requests")

    reason       = models.TextField()
    status       = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)
    expires_at   = models.DateTimeField()

    class Meta:
        db_table = "contact_requests"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.hospital.facility_name} → {self.donor.user.full_name} ({self.status})"

    @property
    def is_expired(self):
        from django.utils import timezone
        return self.status == self.Status.PENDING and timezone.now() > self.expires_at