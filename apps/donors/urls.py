from django.urls import path
from . import views

urlpatterns = [
    path("profile/",              views.create_profile,     name="donor-profile-create"),
    path("profile/me/",           views.get_profile,        name="donor-profile-get"),
    path("profile/update/",       views.update_profile,     name="donor-profile-update"),
    path("profile/delete/",       views.delete_profile,     name="donor-profile-delete"),
    path("profile/availability/", views.toggle_availability, name="donor-toggle-availability"),
    path("profile/<int:donor_id>/hospital-view/", views.hospital_view_donor, name="donor-hospital-view"),
]
