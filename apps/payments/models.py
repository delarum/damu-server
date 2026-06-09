from django.db import models
from apps.hospitals.models import HospitalProfile


class Payment(models.Model):

    class Method(models.TextChoices):
        MPESA  = "mpesa",  "M-Pesa"
        STRIPE = "stripe", "Stripe"

    class Status(models.TextChoices):
        PENDING   = "pending",   "Pending"
        SUCCESS   = "success",   "Success"
        FAILED    = "failed",    "Failed"
        CANCELLED = "cancelled", "Cancelled"

    hospital        = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name="payments")
    method          = models.CharField(max_length=10, choices=Method.choices)
    tier            = models.CharField(max_length=20)
    amount          = models.PositiveIntegerField()  # KES
    currency        = models.CharField(max_length=5, default="KES")
    status          = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    # M-Pesa fields
    mpesa_checkout_request_id = models.CharField(max_length=100, blank=True)
    mpesa_merchant_request_id = models.CharField(max_length=100, blank=True)
    mpesa_receipt_number      = models.CharField(max_length=50, blank=True)
    phone                     = models.CharField(max_length=20, blank=True)

    # Stripe fields
    stripe_payment_intent_id  = models.CharField(max_length=100, blank=True)
    stripe_subscription_id    = models.CharField(max_length=100, blank=True)

    # Timestamps
    initiated_at  = models.DateTimeField(auto_now_add=True)
    completed_at  = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "payments"
        ordering = ["-initiated_at"]

    def __str__(self):
        return f"{self.hospital.facility_name} | {self.method} | {self.amount} KES | {self.status}"