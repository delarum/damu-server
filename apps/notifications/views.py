from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.accounts.models import User
from .models import Notification
from .services import send_sms, send_email


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.ADMIN:
            return Response(
                {"error": True, "message": "Admin access required."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@admin_required
def send_sms_view(request):
    """Admin sends a manual SMS to a user."""
    phone   = request.data.get("recipient")
    message = request.data.get("message")

    if not phone or not message:
        return Response(
            {"error": True, "message": "recipient and message are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        recipient = User.objects.get(phone=phone)
    except User.DoesNotExist:
        return Response({"error": True, "message": "User not found."}, status=404)

    success = send_sms(recipient, message)
    if success:
        return Response({"message": "SMS queued successfully"})
    return Response({"error": True, "message": "SMS failed to send."}, status=502)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@admin_required
def send_email_view(request):
    """Admin sends a manual email to a user."""
    email   = request.data.get("email")
    subject = request.data.get("subject")
    message = request.data.get("message")

    if not all([email, subject, message]):
        return Response(
            {"error": True, "message": "email, subject, and message are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        recipient = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": True, "message": "User not found."}, status=404)

    success = send_email(recipient, subject, message)
    if success:
        return Response({"message": "Email queued"})
    return Response({"error": True, "message": "Email failed to send."}, status=502)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_notifications(request):
    """User views their own notification history."""
    notifs = Notification.objects.filter(recipient=request.user)[:50]
    data = [
        {
            "id":         n.id,
            "channel":    n.channel,
            "subject":    n.subject,
            "message":    n.message,
            "status":     n.status,
            "created_at": n.created_at,
        }
        for n in notifs
    ]
    return Response({"count": len(data), "results": data})