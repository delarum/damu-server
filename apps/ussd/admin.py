from django.contrib import admin
from .models import USSDSession


@admin.register(USSDSession)
class USSDSessionAdmin(admin.ModelAdmin):
    list_display  = ["session_id", "phone", "current_menu", "created_at", "updated_at"]
    search_fields = ["phone", "session_id"]
    readonly_fields = ["created_at", "updated_at"]