from django.db import models
from apps.accounts.models import User
from apps.donors.models import DonorProfile
from apps.hospitals.models import HospitalProfile


class Badge(models.Model):
    """Badge definitions — seeded once."""
    name        = models.CharField(max_length=100, unique=True)
    title       = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon        = models.CharField(max_length=10, blank=True)  # emoji
    required_donations = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "badges"
        ordering = ["required_donations"]

    def __str__(self):
        return f"{self.icon} {self.name} — {self.title}"


class DonorBadge(models.Model):
    """Many-to-many: which badges a donor has earned."""
    donor     = models.ForeignKey(DonorProfile, on_delete=models.CASCADE, related_name="earned_badges")
    badge     = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "donor_badges"
        unique_together = ["donor", "badge"]

    def __str__(self):
        return f"{self.donor.user.full_name} — {self.badge.name}"


class DonationRecord(models.Model):
    """Every confirmed donation event."""

    class DonationType(models.TextChoices):
        WHOLE_BLOOD = "whole_blood", "Whole Blood"
        PLATELET    = "platelet",    "Platelet"
        PLASMA      = "plasma",      "Plasma"
        ORGAN       = "organ",       "Organ"

    donor          = models.ForeignKey(DonorProfile, on_delete=models.CASCADE, related_name="donations")
    hospital       = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name="donations")
    donation_type  = models.CharField(max_length=20, choices=DonationType.choices)
    donation_date  = models.DateField()
    confirmed_by   = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="confirmed_donations"
    )
    credits_awarded = models.PositiveIntegerField(default=0)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "donation_records"
        ordering = ["-donation_date"]

    def __str__(self):
        return f"{self.donor.user.full_name} | {self.donation_type} | {self.donation_date}"


class CreditLedger(models.Model):
    """Immutable ledger of every credit transaction."""

    class TransactionType(models.TextChoices):
        EARN   = "earn",   "Earned"
        REDEEM = "redeem", "Redeemed"
        EXPIRE = "expire", "Expired"
        BONUS  = "bonus",  "Bonus"

    donor            = models.ForeignKey(DonorProfile, on_delete=models.CASCADE, related_name="credit_ledger")
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    amount           = models.IntegerField()   # positive = earn, negative = redeem
    balance_after    = models.IntegerField()
    reason           = models.CharField(max_length=255)
    related_donation = models.ForeignKey(
        DonationRecord, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "credit_ledger"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.donor.user.full_name} | {self.transaction_type} {self.amount} → {self.balance_after}"


# ---------------------------------------------------------------------------
# Credit rules — centralised so they're easy to change
# ---------------------------------------------------------------------------

CREDIT_RULES = {
    "first_donation":        200,
    "whole_blood":           100,
    "platelet":              150,
    "plasma":                120,
    "organ":                 5000,
    "referral":              50,
    "complete_profile":      30,
    "urgent_response_bonus": 75,
}

BADGE_MILESTONES = [
    {"donations": 1,  "name": "First Drop",    "title": "Rookie Lifesaver",  "icon": "🩸"},
    {"donations": 3,  "name": "Triple Pulse",  "title": "Bronze Donor",      "icon": "🥉"},
    {"donations": 5,  "name": "High Five",     "title": "Silver Lifesaver",  "icon": "🥈"},
    {"donations": 10, "name": "Decade Donor",  "title": "Gold Guardian",     "icon": "🥇"},
    {"donations": 20, "name": "Legend",        "title": "Platinum Hero",     "icon": "💎"},
    {"donations": 50, "name": "Immortal",      "title": "Damu Legend",       "icon": "👑"},
]