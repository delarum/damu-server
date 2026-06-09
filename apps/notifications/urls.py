from django.urls import path
from . import views

urlpatterns = [
    path("sms/",   views.send_sms_view,   name="send-sms"),
    path("email/", views.send_email_view, name="send-email"),
    path("mine/",  views.my_notifications, name="my-notifications"),
]