"""
Smile Identity integration for ID document verification + liveness check.
In dev/sandbox mode this always returns a mock approved result.
"""
import requests
from django.conf import settings


def verify_identity(id_image_base64, selfie_base64, id_type, id_number, country="KE"):
    """
    Submit ID + selfie to Smile Identity for automated verification.
    Returns the full API response dict.
    """
    if settings.DEBUG:
        # Return a mock approved result in development
        return {
            "ResultCode":    "1020",
            "ResultText":    "Verified",
            "Actions":       {"Verify_ID_Number": "Verified", "Return_Personal_Info": "Returned"},
            "SmileJobID":    "dev-mock-job-id",
            "PartnerParams": {"job_type": 5},
        }

    payload = {
        "partner_id":   settings.SMILE_PARTNER_ID,
        "id_type":      id_type,
        "country":      country,
        "id_number":    id_number,
        "selfie_image": selfie_base64,
        "id_image":     id_image_base64,
    }

    response = requests.post(
        "https://api.smileidentity.com/v1/id_verification",
        json=payload,
        headers={"Authorization": f"Bearer {settings.SMILE_API_KEY}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def is_verified(provider_result):
    """Check if a Smile Identity result indicates successful verification."""
    actions = provider_result.get("Actions", {})
    return (
        provider_result.get("ResultCode") in ["1020", "1021"]
        and actions.get("Verify_ID_Number") == "Verified"
    )