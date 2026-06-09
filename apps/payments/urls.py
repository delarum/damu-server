from django.urls import path
from . import views

urlpatterns = [
    # M-Pesa
    path("mpesa/stk-push/",  views.mpesa_stk_push,  name="mpesa-stk-push"),
    path("mpesa/callback/",  views.mpesa_callback,  name="mpesa-callback"),

    # Stripe
    path("stripe/subscribe/", views.stripe_subscribe, name="stripe-subscribe"),
    path("stripe/webhook/",   views.stripe_webhook,   name="stripe-webhook"),

    # History
    path("history/",          views.payment_history,  name="payment-history"),
]