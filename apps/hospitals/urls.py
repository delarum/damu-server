from django.urls import path
from . import views

urlpatterns = [
    # Profile
    path("profile/",         views.create_profile,      name="hospital-profile-create"),
    path("profile/me/",      views.get_profile,         name="hospital-profile-get"),
    path("profile/update/",  views.update_profile,      name="hospital-profile-update"),
    path("profile/delete/",  views.delete_profile,      name="hospital-profile-delete"),

    # Documents
    path("documents/upload/", views.upload_document,    name="hospital-upload-doc"),

    # Staff
    path("staff/",            views.list_staff,          name="hospital-staff-list"),
    path("staff/add/",        views.add_staff,           name="hospital-staff-add"),
    path("staff/<int:staff_id>/remove/", views.remove_staff, name="hospital-staff-remove"),

    # Subscription
    path("subscription/",          views.get_subscription,      name="hospital-subscription"),
    path("subscription/activate/", views.activate_subscription, name="hospital-subscription-activate"),
]