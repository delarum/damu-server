from django.contrib import admin
from .models import IdentityVerification


@admin.register(IdentityVerification)
class IdentityVerificationAdmin(admin.ModelAdmin):
    list_display  = ["user", "id_type", "status", "submitted_at", "reviewed_at"]
    list_filter   = ["status", "id_type"]
    search_fields = ["user__full_name", "user__phone", "id_number"]
    readonly_fields = ["submitted_at", "provider_result", "provider_ref"]

    actions = ["approve_verifications", "send_to_manual_review"]

    def approve_verifications(self, request, queryset):
        from django.utils import timezone
        for v in queryset:
            v.status      = IdentityVerification.Status.APPROVED
            v.reviewed_at = timezone.now()
            v.reviewed_by = request.user
            v.save()
            v.user.is_verified = True
            v.user.save(update_fields=["is_verified"])
    approve_verifications.short_description = "Approve selected verifications"

    def send_to_manual_review(self, request, queryset):
        queryset.update(status=IdentityVerification.Status.MANUAL)
    send_to_manual_review.short_description = "Send to manual review"