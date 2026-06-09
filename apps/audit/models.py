from django.db import models
from apps.accounts.models import User


class AuditLog(models.Model):
    """
    Append-only audit trail for every sensitive action on the platform.
    Never updated or deleted — enforced at the application layer.
    """

    class Action(models.TextChoices):
        # Auth
        LOGIN             = "login",              "Login"
        LOGOUT            = "logout",             "Logout"
        PASSWORD_CHANGE   = "password_change",    "Password Change"
        # Donors
        DONOR_REGISTER    = "donor_register",     "Donor Registered"
        DONOR_PROFILE_UPDATE = "donor_profile_update", "Donor Profile Updated"
        DONOR_DELETE      = "donor_delete",       "Donor Account Deleted"
        # Hospitals
        HOSPITAL_REGISTER = "hospital_register",  "Hospital Registered"
        HOSPITAL_APPROVE  = "hospital_approve",   "Hospital Approved"
        HOSPITAL_REJECT   = "hospital_reject",    "Hospital Rejected"
        # Matching
        DONOR_SEARCH      = "donor_search",       "Donor Search"
        CONTACT_INITIATED = "contact_initiated",  "Contact Request Initiated"
        CONTACT_ACCEPTED  = "contact_accepted",   "Contact Request Accepted"
        CONTACT_DECLINED  = "contact_declined",   "Contact Request Declined"
        # Donations
        DONATION_RECORDED = "donation_recorded",  "Donation Recorded"
        CREDITS_REDEEMED  = "credits_redeemed",   "Credits Redeemed"
        # Payments
        PAYMENT_INITIATED = "payment_initiated",  "Payment Initiated"
        PAYMENT_SUCCESS   = "payment_success",    "Payment Successful"
        # Admin
        ADMIN_ACTION      = "admin_action",       "Admin Action"

    actor          = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="audit_logs"
    )
    actor_role     = models.CharField(max_length=30, blank=True)
    action         = models.CharField(max_length=50, choices=Action.choices)
    target_user    = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="targeted_in_logs"
    )
    ip_address     = models.GenericIPAddressField(null=True, blank=True)
    user_agent     = models.TextField(blank=True)
    endpoint       = models.CharField(max_length=255, blank=True)
    method         = models.CharField(max_length=10, blank=True)
    metadata       = models.JSONField(default=dict)
    timestamp      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-timestamp"]

    def __str__(self):
        actor = self.actor.full_name if self.actor else "System"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {actor} — {self.action}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("AuditLog records are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("AuditLog records cannot be deleted.")