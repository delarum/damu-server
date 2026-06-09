from django.urls import path
from . import views

urlpatterns = [
    # Donations
    path("donations/",              views.create_donation,  name="donation-create"),
    path("donations/history/",      views.donation_history, name="donation-history"),
    path("donations/<int:donation_id>/", views.manage_donation, name="donation-manage"),

    # Credits
    path("credits/balance/",        views.credit_balance,      name="credit-balance"),
    path("credits/ledger/",         views.credit_ledger,       name="credit-ledger"),
    path("credits/redeem/",         views.redeem_credits_view, name="credit-redeem"),

    # Badges
    path("badges/",                 views.donor_badges,        name="donor-badges"),
]