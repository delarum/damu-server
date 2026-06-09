from django.db import models
from apps.accounts.models import User


class Notification(models.Model):

    class Channel(models.TextChoices):
        SMS      = "sms",      "SMS"
        EMAIL    = "email",    "Email"
        WHATSAPP = "whatsapp", "WhatsApp"

    class Status(models.TextChoices):
        QUEUED  = "queued",   "Queued"
        SENT    = "sent",     "Sent"
        FAILED  = "failed",   "Failed"

    recipient    = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    channel      = models.CharField(max_length=10, choices=Channel.choices)
    subject      = models.CharField(max_length=255, blank=True)  # for email
    message      = models.TextField()
    status       = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    error        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    sent_at      = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.channel} → {self.recipient.phone} ({self.status})"