from django.db import models


class USSDSession(models.Model):
    """Tracks active USSD sessions (also stored in Redis for speed)."""
    session_id   = models.CharField(max_length=100, unique=True)
    phone        = models.CharField(max_length=20)
    current_menu = models.CharField(max_length=50, default="main")
    data         = models.JSONField(default=dict)  # stores selections mid-session
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ussd_sessions"

    def __str__(self):
        return f"USSD {self.session_id} — {self.phone}"