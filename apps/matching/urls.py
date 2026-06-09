from django.urls import path
from . import views

urlpatterns = [
    # Hospital — search
    path("search/blood/",  views.search_blood_donors,  name="search-blood"),
    path("search/organs/", views.search_organ_donors,  name="search-organs"),

    # Hospital — contact requests
    path("contact-request/",          views.initiate_contact_request, name="contact-request-create"),
    path("contact-requests/",         views.list_contact_requests,    name="contact-request-list"),

    # Donor — respond & view
    path("contact-requests/mine/",                      views.donor_contact_requests,      name="donor-requests"),
    path("contact-requests/<int:request_id>/respond/",  views.respond_to_contact_request,  name="contact-request-respond"),
]