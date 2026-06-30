"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="DamuLink API",
        default_version="v1",
        description=(
            "API documentation for the DamuLink platform. "
            "Provides endpoints for donor and hospital management, matching, "
            "payments, notifications, audit logs, and USSD integration."
        ),
        terms_of_service="https://damulink.co.ke/terms/",
        contact=openapi.Contact(email="support@damulink.co.ke"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/donors/', include('apps.donors.urls')),
    path('api/v1/hospitals/', include('apps.hospitals.urls')),
    path('api/v1/matching/', include('apps.matching.urls')),
    path('api/v1/', include('apps.gamification.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/audit/', include('apps.audit.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/third-party/', include('apps.third_party.urls')),
    path('api/v1/ussd/', include('apps.ussd.urls')),
    path('api/v1/verification/', include('apps.verification.urls')),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
