"""
M-Pesa Daraja API integration.
Handles STK Push initiation and callback processing.
"""
import base64
import requests
from datetime import datetime
from django.conf import settings


def get_mpesa_access_token():
    """Fetch OAuth token from Safaricom."""
    consumer_key    = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    credentials     = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()

    response = requests.get(
        settings.MPESA_TOKEN_URL,
        headers={"Authorization": f"Basic {credentials}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def generate_password(timestamp):
    """Generate the Base64-encoded password for STK push."""
    shortcode = settings.MPESA_SHORTCODE
    passkey   = settings.MPESA_PASSKEY
    raw       = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode()).decode()


def initiate_stk_push(phone, amount, account_ref, description):
    """
    Initiate an M-Pesa STK Push payment.
    Returns the full Safaricom response dict.
    """
    token     = get_mpesa_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Normalize phone: strip + and leading zeros, add 254
    phone = phone.replace("+", "").replace(" ", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password":          generate_password(timestamp),
        "Timestamp":         timestamp,
        "TransactionType":   "CustomerPayBillOnline",
        "Amount":            int(amount),
        "PartyA":            phone,
        "PartyB":            settings.MPESA_SHORTCODE,
        "PhoneNumber":       phone,
        "CallBackURL":       settings.MPESA_CALLBACK_URL,
        "AccountReference":  account_ref,
        "TransactionDesc":   description,
    }

    response = requests.post(
        settings.MPESA_STK_URL,
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def process_stk_callback(callback_data):
    """
    Parse the STK Push callback from Safaricom.
    Returns dict with keys: success, checkout_request_id, receipt_number, amount, phone
    """
    body      = callback_data.get("Body", {})
    stk_callback = body.get("stkCallback", {})
    result_code  = stk_callback.get("ResultCode")
    checkout_id  = stk_callback.get("CheckoutRequestID")

    if result_code != 0:
        return {
            "success":             False,
            "checkout_request_id": checkout_id,
            "result_code":         result_code,
            "result_desc":         stk_callback.get("ResultDesc"),
        }

    # Extract metadata items
    metadata = {}
    items = stk_callback.get("CallbackMetadata", {}).get("Item", [])
    for item in items:
        metadata[item["Name"]] = item.get("Value")

    return {
        "success":             True,
        "checkout_request_id": checkout_id,
        "receipt_number":      metadata.get("MpesaReceiptNumber"),
        "amount":              metadata.get("Amount"),
        "phone":               metadata.get("PhoneNumber"),
    }