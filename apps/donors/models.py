from django.db import models
from apps.accounts.models import User

class DonorProfile(models.Model):
    BLOOD_TYPES = (
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    )

    DONOR_TYPES = (
        ('blood', 'Blood'),
        ('organ', 'Organ'),
        ('both', 'Both'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    blood_type = models.CharField(max_length=5, choices=BLOOD_TYPES)
    donor_type = models.CharField(max_length=20, choices=DONOR_TYPES)
    county = models.CharField(max_length=100)
    town = models.CharField(max_length=100)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    availability_status = models.BooleanField(default=True)
    credits = models.IntegerField(default=0)

    def __str__(self):
        return self.user.phone