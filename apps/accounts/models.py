from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('donor', 'Donor'),
        ('hospital_staff', 'Hospital Staff'),
        ('hospital_admin', 'Hospital Admin'),
        ('damulink_admin', 'DamuLink Admin'),
    )

    username = None

    phone = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone