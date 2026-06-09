from django.urls import path
from . import views

urlpatterns = [
    path("apply/",                          views.submit_application,  name="third-party-apply"),
    path("applications/",                   views.list_applications,   name="third-party-list"),
    path("applications/<int:app_id>/review/", views.review_application, name="third-party-review"),
    path("data/",                           views.aggregate_data,      name="third-party-data"),
]