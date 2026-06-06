from django.contrib import admin
from .models import DonorProfile


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display  = ["user", "blood_type", "donor_type", "county", "availability_status", "verification_status"]
    list_filter   = ["blood_type", "donor_type", "availability_status", "verification_status"]
    search_fields = ["user__full_name", "user__phone", "county", "town"]
    readonly_fields = ["created_at", "updated_at", "cooldown_until"]