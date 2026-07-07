from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .admin_urls import urlpatterns as admin_urlpatterns

urlpatterns = [
    # Registration
    path("register/donor/",    views.register_donor,    name="register-donor"),
    path("register/hospital/", views.register_hospital, name="register-hospital"),

    # OTP
    path("verify-otp/",        views.verify_otp,        name="verify-otp"),
    path("resend-otp/",        views.resend_otp,        name="resend-otp"),

    # Auth
    path("login/",             views.LoginView.as_view(), name="login"),
    path("token/refresh/",     TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/",            views.logout,            name="logout"),

    # Account
    path("me/",                views.me,                name="me"),
    path("change-password/",   views.change_password,   name="change-password"),
    
    # Admin endpoints
    path("", include(admin_urlpatterns)),
]
