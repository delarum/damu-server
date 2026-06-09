import json
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.accounts.models import User
from apps.hospitals.models import HospitalProfile, HospitalStaff
from .models import Payment
from .mpesa import initiate_stk_push, process_stk_callback


def get_hospital(user):
    try:
        if user.role == User.Role.HOSPITAL_ADMIN:
            return user.hospital_profile
        elif user.role == User.Role.HOSPITAL_STAFF:
            return user.hospital_staff.hospital
    except Exception:
        return None


def hospital_admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.HOSPITAL_ADMIN:
            return Response(
                {"error": True, "message": "Only hospital admins can perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ---------------------------------------------------------------------------
# M-Pesa
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@hospital_admin_required
def mpesa_stk_push(request):
    hospital = get_hospital(request.user)
    if not hospital:
        return Response({"error": True, "message": "Hospital not found."}, status=404)

    phone = request.data.get("phone")
    tier  = request.data.get("tier")

    if not phone or not tier:
        return Response(
            {"error": True, "message": "phone and tier are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    amount = HospitalProfile.TIER_PRICES.get(tier)
    if not amount:
        return Response(
            {"error": True, "message": f"Invalid tier. Choose from: {list(HospitalProfile.TIER_PRICES.keys())}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Create a pending payment record
    payment = Payment.objects.create(
        hospital=hospital,
        method=Payment.Method.MPESA,
        tier=tier,
        amount=amount,
        phone=phone,
        status=Payment.Status.PENDING,
    )

    try:
        response = initiate_stk_push(
            phone=phone,
            amount=amount,
            account_ref=f"DAMULINK-{hospital.id}",
            description=f"DamuLink {tier.title()} subscription",
        )

        checkout_id = response.get("CheckoutRequestID")
        merchant_id = response.get("MerchantRequestID")

        payment.mpesa_checkout_request_id = checkout_id or ""
        payment.mpesa_merchant_request_id = merchant_id or ""
        payment.save(update_fields=["mpesa_checkout_request_id", "mpesa_merchant_request_id"])

        return Response(
            {
                "message":             "STK push initiated. Check your phone.",
                "checkout_request_id": checkout_id,
                "payment_id":          payment.id,
            }
        )

    except Exception as e:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status"])
        return Response(
            {"error": True, "message": f"M-Pesa error: {str(e)}"},
            status=status.HTTP_502_BAD_GATEWAY,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def mpesa_callback(request):
    """
    Safaricom calls this URL after the user completes (or cancels) the STK push.
    Must return 200 quickly.
    """
    try:
        data   = request.data
        result = process_stk_callback(data)

        payment = Payment.objects.filter(
            mpesa_checkout_request_id=result["checkout_request_id"]
        ).first()

        if not payment:
            return Response({"ResultCode": 0, "ResultDesc": "Accepted"})

        if result["success"]:
            payment.status               = Payment.Status.SUCCESS
            payment.mpesa_receipt_number = result.get("receipt_number", "")
            payment.completed_at         = timezone.now()
            payment.save()

            # Activate subscription
            hospital = payment.hospital
            hospital.subscription_tier    = payment.tier
            hospital.subscription_status  = "active"
            hospital.subscription_expires = timezone.now() + timedelta(days=30)
            hospital.search_limit         = HospitalProfile.TIER_LIMITS.get(payment.tier, 100)
            hospital.search_quota         = 0
            hospital.save()

        else:
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status"])

    except Exception as e:
        print(f"[M-Pesa callback error] {e}")

    # Always return 200 to Safaricom
    return Response({"ResultCode": 0, "ResultDesc": "Accepted"})


# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@hospital_admin_required
def stripe_subscribe(request):
    hospital = get_hospital(request.user)
    if not hospital:
        return Response({"error": True, "message": "Hospital not found."}, status=404)

    payment_method_id = request.data.get("payment_method_id")
    tier              = request.data.get("tier")

    if not payment_method_id or not tier:
        return Response(
            {"error": True, "message": "payment_method_id and tier are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    amount = HospitalProfile.TIER_PRICES.get(tier)
    if not amount:
        return Response(
            {"error": True, "message": "Invalid tier."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from .stripe_service import create_stripe_customer, create_payment_intent

        customer = create_stripe_customer(hospital)
        intent   = create_payment_intent(
            amount_kes=amount,
            customer_id=customer["id"],
            metadata={"hospital_id": hospital.id, "tier": tier},
        )

        payment = Payment.objects.create(
            hospital=hospital,
            method=Payment.Method.STRIPE,
            tier=tier,
            amount=amount,
            currency="KES",
            status=Payment.Status.PENDING,
            stripe_payment_intent_id=intent["id"],
        )

        return Response(
            {
                "message":              "Payment intent created",
                "client_secret":        intent["client_secret"],
                "payment_intent_id":    intent["id"],
                "payment_id":           payment.id,
            }
        )

    except Exception as e:
        return Response(
            {"error": True, "message": f"Stripe error: {str(e)}"},
            status=status.HTTP_502_BAD_GATEWAY,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def stripe_webhook(request):
    """Stripe calls this after a successful payment."""
    payload    = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        from .stripe_service import construct_webhook_event
        event = construct_webhook_event(payload, sig_header)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    if event["type"] == "payment_intent.succeeded":
        intent  = event["data"]["object"]
        payment = Payment.objects.filter(stripe_payment_intent_id=intent["id"]).first()

        if payment:
            payment.status       = Payment.Status.SUCCESS
            payment.completed_at = timezone.now()
            payment.save()

            hospital = payment.hospital
            hospital.subscription_tier    = payment.tier
            hospital.subscription_status  = "active"
            hospital.subscription_expires = timezone.now() + timedelta(days=30)
            hospital.search_limit         = HospitalProfile.TIER_LIMITS.get(payment.tier, 100)
            hospital.search_quota         = 0
            hospital.save()

    return Response({"status": "ok"})


# ---------------------------------------------------------------------------
# Payment history
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@hospital_admin_required
def payment_history(request):
    hospital = get_hospital(request.user)
    if not hospital:
        return Response({"error": True, "message": "Hospital not found."}, status=404)

    payments = Payment.objects.filter(hospital=hospital)
    data = [
        {
            "id":          p.id,
            "method":      p.method,
            "tier":        p.tier,
            "amount":      p.amount,
            "status":      p.status,
            "initiated_at": p.initiated_at,
            "completed_at": p.completed_at,
        }
        for p in payments
    ]
    return Response({"count": len(data), "results": data})