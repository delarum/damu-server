from django.urls import path
from . import views

urlpatterns = [
    path("upload-id/",                              views.upload_id_documents,    name="upload-id"),
    path("status/",                                 views.verification_status,    name="verification-status"),
    path("manual-review/",                          views.manual_review_queue,    name="manual-review-queue"),
    path("manual-review/<int:verification_id>/",    views.manual_review_decision, name="manual-review-decision"),
]