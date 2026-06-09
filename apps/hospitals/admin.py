from django.contrib import admin
from .models import HospitalProfile, HospitalDocument, HospitalStaff


@admin.register(HospitalProfile)
class HospitalProfileAdmin(admin.ModelAdmin):
    list_display  = ["facility_name", "facility_type", "county", "approval_status", "subscription_tier", "subscription_status"]
    list_filter   = ["facility_type", "approval_status", "subscription_tier"]
    search_fields = ["facility_name", "license_number", "county"]
    readonly_fields = ["created_at", "updated_at", "approved_at"]

    actions = ["approve_hospitals", "reject_hospitals"]

    def approve_hospitals(self, request, queryset):
        from django.utils import timezone
        queryset.update(approval_status="approved", approved_at=timezone.now(), approved_by=request.user)
    approve_hospitals.short_description = "Approve selected hospitals"

    def reject_hospitals(self, request, queryset):
        queryset.update(approval_status="rejected")
    reject_hospitals.short_description = "Reject selected hospitals"


@admin.register(HospitalDocument)
class HospitalDocumentAdmin(admin.ModelAdmin):
    list_display  = ["hospital", "doc_type", "uploaded_at"]
    list_filter   = ["doc_type"]


@admin.register(HospitalStaff)
class HospitalStaffAdmin(admin.ModelAdmin):
    list_display  = ["user", "hospital", "added_at"]
    search_fields = ["user__full_name", "hospital__facility_name"]