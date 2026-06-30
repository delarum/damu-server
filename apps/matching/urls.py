from django.urls import path
from . import views

urlpatterns = [
    path("search/blood/",  views.search_blood_donors,  name="search-blood"),
    path("search/organs/", views.search_organ_donors,  name="search-organs"),
    path("donors/map/",    views.donor_map,            name="donor-map"),
    path("contact-request/",          views.initiate_contact_request, name="contact-request-create"),
    path("contact-requests/",         views.list_contact_requests,    name="contact-request-list"),
    path("contact-requests/mine/",                      views.donor_contact_requests,      name="donor-requests"),
    path("contact-requests/<int:request_id>/respond/",  views.respond_to_contact_request,  name="contact-request-respond"),
]
