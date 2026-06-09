from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ["recipient", "channel", "status", "subject", "created_at"]
    list_filter   = ["channel", "status"]
    search_fields = ["recipient__phone", "recipient__email", "message"]
    readonly_fields = ["created_at", "sent_at"]