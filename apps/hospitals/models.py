from django.db import models
from apps.accounts.models import User

class HospitalProfile(models.Model):
    FACILITY_TYPES = (
        ('public', 'Public'),
        ('private', 'Private'),
        ('ngo', 'NGO'),
        ('blood_bank', 'Blood Bank'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    facility_name = models.CharField(max_length=255)
    facility_type = models.CharField(max_length=30, choices=FACILITY_TYPES)
    license_number = models.CharField(max_length=100)
    address = models.TextField()
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.facility_name