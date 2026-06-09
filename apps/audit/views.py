from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.accounts.models import User
from .models import AuditLog


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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@admin_required
def list_audit_logs(request):
    logs = AuditLog.objects.select_related("actor", "target_user")

    # Optional filters
    action     = request.query_params.get("action")
    actor_role = request.query_params.get("role")
    limit      = int(request.query_params.get("limit", 50))

    if action:
        logs = logs.filter(action=action)
    if actor_role:
        logs = logs.filter(actor_role=actor_role)

    logs = logs[:limit]

    data = [
        {
            "id":         log.id,
            "actor":      log.actor.full_name if log.actor else "System",
            "actor_role": log.actor_role,
            "action":     log.action,
            "endpoint":   log.endpoint,
            "ip_address": log.ip_address,
            "timestamp":  log.timestamp,
            "metadata":   log.metadata,
        }
        for log in logs
    ]

    return Response({"count": len(data), "results": data})