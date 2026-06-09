from django.urls import path
from . import views

urlpatterns = [
    path("",                  views.ussd_callback,         name="ussd-callback"),
    path("confirm-donation/", views.confirm_donation_ussd, name="ussd-confirm-donation"),
]