from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse

from apps.accounts.models import User
from .models import USSDSession
from .menus import process_menu


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def ussd_callback(request):
    """
    Africa's Talking USSD callback endpoint.
    Must respond within 1 second with CON or END.
    """
    session_id   = request.data.get("sessionId", "")
    phone        = request.data.get("phoneNumber", "")
    text         = request.data.get("text", "")

    # Get or create session
    session, _ = USSDSession.objects.get_or_create(
        session_id=session_id,
        defaults={"phone": phone},
    )

    try:
        response_text = process_menu(session, phone, text)
    except Exception as e:
        response_text = f"END Service error. Please try again. ({str(e)[:40]})"

    # If session ended, clean it up
    if response_text.startswith("END"):
        session.delete()

    return HttpResponse(response_text, content_type="text/plain")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirm_donation_ussd(request):
    """
    Donor confirms a donation via USSD confirmation code issued by hospital.
    POST { "phone": "+254...", "confirmation_code": "DML-0091" }
    """
    phone = request.data.get("phone")
    code  = request.data.get("confirmation_code", "")

    if not phone or not code:
        return Response(
            {"error": True, "message": "phone and confirmation_code are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # In production: look up a DonationConfirmationCode model
    # For now we validate the format and return success
    if not code.startswith("DML-"):
        return Response(
            {"error": True, "message": "Invalid confirmation code format."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {"message": "Donation confirmed", "credits_awarded": 100}
    )