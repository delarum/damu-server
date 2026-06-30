from django.db import models
from django.utils import timezone
from apps.accounts.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class DonorProfile(models.Model):

    class BloodType(models.TextChoices):
        A_POS  = "A+",  "A+"
        A_NEG  = "A-",  "A-"
        B_POS  = "B+",  "B+"
        B_NEG  = "B-",  "B-"
        AB_POS = "AB+", "AB+"
        AB_NEG = "AB-", "AB-"
        O_POS  = "O+",  "O+"
        O_NEG  = "O-",  "O-"

    class Gender(models.TextChoices):
       MALE   = "male",   "Male"
       FEMALE = "female", "Female"
       OTHER  = "other",  "Prefer not to say"    

    class DonorType(models.TextChoices):
        BLOOD  = "blood",  "Blood Only"
        ORGAN  = "organ",  "Organ Only"
        BOTH   = "both",   "Blood & Organ"

    class ContactMethod(models.TextChoices):
        CALL     = "call",     "Call"
        SMS      = "sms",      "SMS"
        WHATSAPP = "whatsapp", "WhatsApp"

    class VerificationStatus(models.TextChoices):
        PENDING  = "pending",  "Pending"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    ORGAN_CHOICES = [
        "kidney", "liver", "cornea", "heart",
        "bone_marrow", "lung", "pancreas",
    ]

    # Core
    user               = models.OneToOneField(User, on_delete=models.CASCADE, related_name="donor_profile")
    blood_type         = models.CharField(max_length=5, choices=BloodType.choices)
    donor_type         = models.CharField(max_length=10, choices=DonorType.choices, default=DonorType.BLOOD)
    organs_pledged     = models.JSONField(default=list, blank=True)  # e.g. ["kidney", "cornea"]

    # Medical
    health_conditions  = models.TextField(blank=True, null=True)  # encrypted in production
    last_donation_date = models.DateField(blank=True, null=True)
    cooldown_until     = models.DateTimeField(blank=True, null=True)

    gender    = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    height_cm = models.PositiveSmallIntegerField(
        blank=True, null=True,
        validators=[MinValueValidator(100), MaxValueValidator(250)],
        help_text="Height in centimetres",
    )
    weight_kg = models.PositiveSmallIntegerField(
        blank=True, null=True,
        validators=[MinValueValidator(30), MaxValueValidator(250)],
        help_text="Weight in kilograms",
    )

    # Location
    county             = models.CharField(max_length=100, blank=True)
    sub_county         = models.CharField(max_length=100, blank=True)
    town               = models.CharField(max_length=100, blank=True)
    address            = models.TextField(blank=True)       # encrypted in production
    lat                = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    lng                = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    # Contact
    preferred_contact_method = models.CharField(
        max_length=10, choices=ContactMethod.choices, default=ContactMethod.SMS
    )
    emergency_contact_name  = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    # Insurance
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_number   = models.CharField(max_length=100, blank=True)  # encrypted in production

    # Status
    availability_status   = models.BooleanField(default=True)
    verification_status   = models.CharField(
        max_length=10, choices=VerificationStatus.choices, default=VerificationStatus.PENDING
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "donor_profiles"

    def __str__(self):
        return f"{self.user.full_name} | {self.blood_type} | {self.donor_type}"

    @property
    def is_available(self):
        if not self.availability_status:
            return False
        if self.cooldown_until and timezone.now() < self.cooldown_until:
            return False
        return True

    def set_cooldown(self, donation_type="whole_blood"):
        from datetime import timedelta
        cooldowns = {
            "whole_blood": timedelta(days=56),
            "platelet":    timedelta(days=7),
            "plasma":      timedelta(days=14),
        }
        delta = cooldowns.get(donation_type, timedelta(days=56))
        self.cooldown_until = timezone.now() + delta
        self.save(update_fields=["cooldown_until"])