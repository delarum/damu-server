"""
Audit Middleware — logs every authenticated write request to AuditLog.
Read requests (GET, HEAD, OPTIONS) are not logged at middleware level
but can be logged explicitly in views (e.g. donor searches).
"""
from django.utils.deprecation import MiddlewareMixin


WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Endpoints we always skip (noise with no audit value)
SKIP_PATHS = {
    "/admin/jsi18n/",
    "/api/v1/payments/mpesa/callback/",
    "/api/v1/payments/stripe/webhook/",
    "/api/v1/ussd/",
}


class AuditMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        try:
            if request.method not in WRITE_METHODS:
                return response
            if request.path in SKIP_PATHS:
                return response
            if not hasattr(request, "user") or not request.user.is_authenticated:
                return response
            if response.status_code >= 500:
                return response

            from .models import AuditLog
            from .utils import get_client_ip

            AuditLog.objects.create(
                actor=request.user,
                actor_role=getattr(request.user, "role", ""),
                action=_infer_action(request),
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                endpoint=request.path,
                method=request.method,
                metadata={"status_code": response.status_code},
            )
        except Exception:
            pass  # Never let audit logging crash the app

        return response


def _infer_action(request):
    """Best-effort mapping of endpoint + method to an action label."""
    from .models import AuditLog
    path   = request.path
    method = request.method

    mapping = {
        ("/api/v1/auth/login/",              "POST"): AuditLog.Action.LOGIN,
        ("/api/v1/auth/logout/",             "POST"): AuditLog.Action.LOGOUT,
        ("/api/v1/auth/change-password/",    "POST"): AuditLog.Action.PASSWORD_CHANGE,
        ("/api/v1/auth/register/donor/",     "POST"): AuditLog.Action.DONOR_REGISTER,
        ("/api/v1/auth/register/hospital/",  "POST"): AuditLog.Action.HOSPITAL_REGISTER,
        ("/api/v1/donors/profile/update/",   "PATCH"): AuditLog.Action.DONOR_PROFILE_UPDATE,
        ("/api/v1/donors/profile/delete/",   "DELETE"): AuditLog.Action.DONOR_DELETE,
        ("/api/v1/matching/contact-request/","POST"): AuditLog.Action.CONTACT_INITIATED,
        ("/api/v1/donations/",               "POST"): AuditLog.Action.DONATION_RECORDED,
        ("/api/v1/credits/redeem/",          "POST"): AuditLog.Action.CREDITS_REDEEMED,
        ("/api/v1/payments/mpesa/stk-push/", "POST"): AuditLog.Action.PAYMENT_INITIATED,
        ("/api/v1/payments/stripe/subscribe/","POST"): AuditLog.Action.PAYMENT_INITIATED,
    }

    return mapping.get((path, method), AuditLog.Action.ADMIN_ACTION)