"""
Stripe integration for card payments.
"""
import stripe
from django.conf import settings


def get_stripe():
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def create_stripe_customer(hospital):
    """Create or retrieve a Stripe customer for a hospital."""
    s = get_stripe()
    customer = s.Customer.create(
        name=hospital.facility_name,
        email=hospital.email or hospital.admin.email,
        metadata={"hospital_id": hospital.id},
    )
    return customer


def create_payment_intent(amount_kes, customer_id, metadata=None):
    """
    Create a Stripe PaymentIntent.
    Amount is in KES — Stripe requires smallest currency unit (cents/pence),
    but KES is a zero-decimal currency so we pass as-is.
    """
    s = get_stripe()
    intent = s.PaymentIntent.create(
        amount=int(amount_kes),
        currency="kes",
        customer=customer_id,
        metadata=metadata or {},
        automatic_payment_methods={"enabled": True},
    )
    return intent


def create_subscription(customer_id, price_id):
    """Create a Stripe subscription."""
    s = get_stripe()
    subscription = s.Subscription.create(
        customer=customer_id,
        items=[{"price": price_id}],
    )
    return subscription


def construct_webhook_event(payload, sig_header):
    """Verify and parse a Stripe webhook."""
    s = get_stripe()
    return s.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )