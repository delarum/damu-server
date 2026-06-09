def get_client_ip(request):
    """Extract real client IP, accounting for proxies."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(actor, action, target_user=None, metadata=None, request=None):
    """
    Explicitly log an action from within a view.
    Use this for GET requests that need auditing (e.g. donor searches).
    """
    from .models import AuditLog

    ip         = get_client_ip(request) if request else None
    user_agent = request.META.get("HTTP_USER_AGENT", "")[:500] if request else ""
    endpoint   = request.path if request else ""
    method     = request.method if request else ""

    AuditLog.objects.create(
        actor=actor,
        actor_role=getattr(actor, "role", ""),
        action=action,
        target_user=target_user,
        ip_address=ip,
        user_agent=user_agent,
        endpoint=endpoint,
        method=method,
        metadata=metadata or {},
    )
