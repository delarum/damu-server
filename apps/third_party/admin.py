from django.contrib import admin
from .models import ThirdPartyApplication


@admin.register(ThirdPartyApplication)
class ThirdPartyApplicationAdmin(admin.ModelAdmin):
    list_display  = ["org_name", "org_type", "contact_email", "status", "dpa_signed", "nda_signed", "created_at"]
    list_filter   = ["status", "org_type", "dpa_signed", "nda_signed"]
    search_fields = ["org_name", "contact_email", "contact_name"]
    readonly_fields = ["created_at", "updated_at", "approved_at"]