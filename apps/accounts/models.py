from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Phone number is required")
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "damulink_admin")
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        DONOR          = "donor",                 "Donor"
        HOSPITAL_STAFF = "hospital_staff",        "Hospital Staff"
        HOSPITAL_ADMIN = "hospital_admin",        "Hospital Admin"
        ADMIN          = "damulink_admin",        "DamuLink Admin"
        THIRD_PARTY    = "third_party_researcher","Third Party Researcher"

    phone          = models.CharField(max_length=20, unique=True)
    email          = models.EmailField(blank=True, null=True)
    full_name      = models.CharField(max_length=255)
    national_id    = models.CharField(max_length=50, blank=True, null=True)
    date_of_birth  = models.DateField(blank=True, null=True)

    role           = models.CharField(max_length=30, choices=Role.choices, default=Role.DONOR)
    is_verified    = models.BooleanField(default=False)
    is_active      = models.BooleanField(default=True)
    is_staff       = models.BooleanField(default=False)

    otp_secret     = models.CharField(max_length=64, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD  = "phone"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.full_name} ({self.phone})"

    @property
    def is_donor(self):
        return self.role == self.Role.DONOR

    @property
    def is_hospital_member(self):
        return self.role in [self.Role.HOSPITAL_STAFF, self.Role.HOSPITAL_ADMIN]

    @property
    def is_damulink_admin(self):
        return self.role == self.Role.ADMIN


class OTPVerification(models.Model):
    class Purpose(models.TextChoices):
        REGISTRATION   = "registration",   "Registration"
        LOGIN          = "login",          "Login 2FA"
        PASSWORD_RESET = "password_reset", "Password Reset"

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    code       = models.CharField(max_length=6)
    purpose    = models.CharField(max_length=20, choices=Purpose.choices)
    is_used    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "otp_verifications"

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP({self.user.phone}, {self.purpose})"