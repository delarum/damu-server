"""
Notification dispatch service.
Handles SMS via Africa's Talking and email via SendGrid.
In dev, messages are printed to the console.
"""
from django.conf import settings
from django.utils import timezone


def send_sms(recipient_user, message):
    """Send SMS via Africa's Talking. Falls back to console in dev."""
    from .models import Notification

    notif = Notification.objects.create(
        recipient=recipient_user,
        channel=Notification.Channel.SMS,
        message=message,
    )

    try:
        if settings.DEBUG:
            print(f"[DEV SMS] To: {recipient_user.phone}\n{message}\n")
            notif.status  = Notification.Status.SENT
            notif.sent_at = timezone.now()
            notif.save(update_fields=["status", "sent_at"])
            return True

        import africastalking
        africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
        sms      = africastalking.SMS
        response = sms.send(message, [recipient_user.phone], sender_id=settings.AT_SENDER_ID)

        recipients = response.get("SMSMessageData", {}).get("Recipients", [])
        if recipients and recipients[0].get("status") == "Success":
            notif.status  = Notification.Status.SENT
            notif.sent_at = timezone.now()
        else:
            notif.status = Notification.Status.FAILED
            notif.error  = str(response)

        notif.save(update_fields=["status", "sent_at", "error"])
        return notif.status == Notification.Status.SENT

    except Exception as e:
        notif.status = Notification.Status.FAILED
        notif.error  = str(e)
        notif.save(update_fields=["status", "error"])
        return False


def send_email(recipient_user, subject, message):
    from .models import Notification
    from django.conf import settings

    notif = Notification.objects.create(
        recipient=recipient_user,
        channel=Notification.Channel.EMAIL,
        subject=subject,
        message=message,
    )

    use_console = not getattr(settings, "SENDGRID_API_KEY", None)

    try:
        if use_console:
            print(f"[DEV EMAIL] To: {recipient_user.email}\nSubject: {subject}\n{message}\n")
            notif.status  = Notification.Status.SENT
            notif.sent_at = timezone.now()
            notif.save(update_fields=["status", "sent_at"])
            return True

        from django.core.mail import send_mail
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_user.email],
            fail_silently=False,
        )
        notif.status  = Notification.Status.SENT
        notif.sent_at = timezone.now()
        notif.save(update_fields=["status", "sent_at"])
        return True

    except Exception as e:
        notif.status = Notification.Status.FAILED
        notif.error  = str(e)
        notif.save(update_fields=["status", "error"])
        return False


# ---------------------------------------------------------------------------
# Domain-specific notification helpers
# ---------------------------------------------------------------------------

def notify_donor_contact_request(donor_user, hospital_name, blood_type, request_id):
    message = (
        f"DamuLink: {hospital_name} urgently needs {blood_type} blood. "
        f"Reply to request #{request_id} on the app to accept or decline. "
        f"Your help saves lives."
    )
    send_sms(donor_user, message)


def notify_hospital_donor_accepted(hospital_admin_user, donor_name, donor_phone, donor_blood_type):
    message = (
        f"DamuLink: Good news! {donor_name} ({donor_blood_type}) has accepted your contact request. "
        f"You can reach them at {donor_phone}."
    )
    send_sms(hospital_admin_user, message)


def notify_hospital_approved(hospital_admin_user, facility_name):
    subject = "Your DamuLink registration has been approved"
    message = (
        f"Congratulations! {facility_name} has been approved on DamuLink. "
        f"You can now subscribe and access our national donor database. "
        f"Log in at damulink.co.ke to get started."
    )
    send_email(hospital_admin_user, subject, message)
    send_sms(hospital_admin_user, f"DamuLink: {facility_name} approved! Log in to subscribe and access donors.")


def notify_subscription_expiring(hospital_admin_user, facility_name, days_remaining):
    message = (
        f"DamuLink: Your {facility_name} subscription expires in {days_remaining} day(s). "
        f"Renew now to keep accessing donors."
    )
    send_sms(hospital_admin_user, message)


def notify_donation_confirmed(donor_user, hospital_name, credits_awarded):
    message = (
        f"DamuLink: Your donation at {hospital_name} has been confirmed. "
        f"You earned {credits_awarded} credits. Thank you for saving lives!"
    )
    send_sms(donor_user, message)