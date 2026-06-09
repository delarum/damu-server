"""
USSD Menu tree for DamuLink.
Each function returns a string starting with:
  CON  — continue (show next menu)
  END  — terminate session
"""
from apps.accounts.models import User
from apps.donors.models import DonorProfile
from apps.gamification.services import get_credit_balance


# ---------------------------------------------------------------------------
# Menu router
# ---------------------------------------------------------------------------

def process_menu(session, phone, text):
    """
    Route to the correct menu handler based on current session state and input.
    `text` is the full concatenated input string e.g. "1*2*1"
    """
    parts = [p for p in text.split("*") if p] if text else []
    depth = len(parts)

    # Identify the user
    user = User.objects.filter(phone=phone).first()

    if depth == 0:
        return menu_main(user)

    top = parts[0]

    # ---- Hospital flows ----
    if top == "1":
        return hospital_flow(parts[1:], session, user)

    # ---- Donor flows ----
    if top == "2":
        return donor_flow(parts[1:], session, user)

    if top == "3":
        return END("Thank you for using DamuLink. Goodbye!")

    return END("Invalid option. Please try again.")


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

def menu_main(user):
    role = getattr(user, "role", None)

    if role in [User.Role.HOSPITAL_ADMIN, User.Role.HOSPITAL_STAFF]:
        return CON(
            "Welcome to DamuLink\n"
            "1. Search blood donor\n"
            "2. Search organ donor\n"
            "3. Post urgent need\n"
            "4. Check subscription\n"
            "5. Exit"
        )

    if role == User.Role.DONOR:
        return CON(
            "Welcome to DamuLink\n"
            "1. Check my credits\n"
            "2. Update availability\n"
            "3. View contact requests\n"
            "4. Exit"
        )

    # Unknown / unregistered
    return CON(
        "Welcome to DamuLink\n"
        "Kenya's blood & organ donor network\n"
        "1. I am a hospital\n"
        "2. I am a donor\n"
        "3. Exit"
    )


# ---------------------------------------------------------------------------
# Hospital flows
# ---------------------------------------------------------------------------

def hospital_flow(parts, session, user):
    depth = len(parts)

    if depth == 0:
        return CON(
            "Select search type:\n"
            "1. Blood donor\n"
            "2. Organ donor\n"
            "3. Check subscription\n"
            "4. Back"
        )

    choice = parts[0]

    # Blood donor search
    if choice == "1":
        if depth == 1:
            return CON(
                "Select blood type:\n"
                "1. O+  2. O-\n"
                "3. A+  4. A-\n"
                "5. B+  6. B-\n"
                "7. AB+ 8. AB-"
            )
        blood_map = {"1":"O+","2":"O-","3":"A+","4":"A-","5":"B+","6":"B-","7":"AB+","8":"AB-"}
        blood_type = blood_map.get(parts[1])
        if not blood_type:
            return END("Invalid blood type selected.")

        # Store selection in session
        session.data["blood_type"] = blood_type
        session.save()

        if depth == 2:
            return CON(
                f"Searching for {blood_type} donors...\n"
                "Select radius:\n"
                "1. 5km\n"
                "2. 10km\n"
                "3. 25km\n"
                "4. 50km"
            )

        radius_map = {"1": 5, "2": 10, "3": 25, "4": 50}
        radius = radius_map.get(parts[2], 10)

        return _ussd_blood_search(user, blood_type, radius)

    # Organ donor search
    if choice == "2":
        if depth == 1:
            return CON(
                "Select organ:\n"
                "1. Kidney\n"
                "2. Liver\n"
                "3. Cornea\n"
                "4. Heart\n"
                "5. Bone Marrow"
            )
        organ_map = {"1":"kidney","2":"liver","3":"cornea","4":"heart","5":"bone_marrow"}
        organ = organ_map.get(parts[1])
        if not organ:
            return END("Invalid organ selected.")
        return _ussd_organ_search(user, organ)

    # Subscription check
    if choice == "3":
        return _ussd_subscription_check(user)

    return END("Invalid option.")


def _ussd_blood_search(user, blood_type, radius_km):
    try:
        from apps.hospitals.models import HospitalProfile
        from apps.donors.models import DonorProfile
        from utils.geo import donors_within_radius
        from django.utils import timezone

        hospital = user.hospital_profile
        if not hospital.is_active_subscriber:
            return END("No active subscription. Visit damulink.co.ke to subscribe.")

        donors_qs = DonorProfile.objects.filter(
            blood_type=blood_type,
            donor_type__in=["blood", "both"],
            availability_status=True,
            verification_status="verified",
        ).filter(cooldown_until__isnull=True) | DonorProfile.objects.filter(
            blood_type=blood_type,
            donor_type__in=["blood", "both"],
            availability_status=True,
            verification_status="verified",
            cooldown_until__lt=timezone.now(),
        )

        nearby = donors_within_radius(donors_qs, hospital.lat, hospital.lng, radius_km)

        if not nearby:
            return END(f"No {blood_type} donors found within {radius_km}km.")

        top3   = nearby[:3]
        result = f"Found {len(nearby)} {blood_type} donors within {radius_km}km\n"
        for i, (donor, dist) in enumerate(top3, 1):
            parts_name = donor.user.full_name.strip().split()
            name = f"{parts_name[0]} {parts_name[-1][0]}." if len(parts_name) >= 2 else parts_name[0]
            result += f"{i}. {name} | {dist}km\n"

        result += "Visit app to initiate contact."
        return END(result)

    except Exception as e:
        return END(f"Search failed. Please try the app. ({str(e)[:30]})")


def _ussd_organ_search(user, organ):
    try:
        from apps.hospitals.models import HospitalProfile
        from apps.donors.models import DonorProfile
        from utils.geo import donors_within_radius

        hospital = user.hospital_profile
        if not hospital.is_active_subscriber:
            return END("No active subscription. Visit damulink.co.ke to subscribe.")

        donors_qs = list(DonorProfile.objects.filter(
            donor_type__in=["organ", "both"],
            availability_status=True,
            verification_status="verified",
        ).select_related("user"))
        donors_qs = [d for d in donors_qs if organ in (d.organs_pledged or [])]

        nearby = donors_within_radius(donors_qs, hospital.lat, hospital.lng, 100)

        if not nearby:
            return END(f"No {organ} donors found within 100km.")

        return END(f"Found {len(nearby)} {organ} donor(s) within 100km. Visit app to contact.")

    except Exception as e:
        return END(f"Search failed. Please try the app.")


def _ussd_subscription_check(user):
    try:
        hospital = user.hospital_profile
        if hospital.is_active_subscriber:
            expires = hospital.subscription_expires.strftime("%d %b %Y")
            remaining = hospital.searches_remaining
            return END(
                f"Subscription: {hospital.subscription_tier.title()}\n"
                f"Status: Active\n"
                f"Expires: {expires}\n"
                f"Searches left: {remaining}"
            )
        return END("No active subscription.\nVisit damulink.co.ke to subscribe.")
    except Exception:
        return END("Could not retrieve subscription info.")


# ---------------------------------------------------------------------------
# Donor flows
# ---------------------------------------------------------------------------

def donor_flow(parts, session, user):
    depth = len(parts)

    if depth == 0:
        return CON(
            "Donor menu:\n"
            "1. Check my credits\n"
            "2. Toggle availability\n"
            "3. View contact requests\n"
            "4. Back"
        )

    choice = parts[0]

    if choice == "1":
        return _ussd_credit_balance(user)

    if choice == "2":
        return _ussd_toggle_availability(user)

    if choice == "3":
        return _ussd_contact_requests(user)

    return END("Invalid option.")


def _ussd_credit_balance(user):
    try:
        donor   = user.donor_profile
        balance = get_credit_balance(donor)
        return END(
            f"DamuLink Credits\n"
            f"Balance: {balance} credits\n"
            f"= KES {balance} equivalent\n"
            f"Redeem at any partner hospital."
        )
    except Exception:
        return END("Could not retrieve credits. Please log in to the app.")


def _ussd_toggle_availability(user):
    try:
        donor = user.donor_profile
        donor.availability_status = not donor.availability_status
        donor.save(update_fields=["availability_status"])
        state = "AVAILABLE" if donor.availability_status else "UNAVAILABLE"
        return END(f"Your status is now: {state}\nThank you for being part of DamuLink.")
    except Exception:
        return END("Could not update status. Please use the app.")


def _ussd_contact_requests(user):
    try:
        from apps.matching.models import ContactRequest
        donor    = user.donor_profile
        pending  = ContactRequest.objects.filter(
            donor=donor, status=ContactRequest.Status.PENDING
        ).select_related("hospital")[:3]

        if not pending:
            return END("No pending contact requests.")

        result = f"Pending requests ({pending.count()}):\n"
        for i, cr in enumerate(pending, 1):
            result += f"{i}. {cr.hospital.facility_name}\n"
        result += "Open app to accept/decline."
        return END(result)
    except Exception:
        return END("Could not load requests. Please use the app.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def CON(text):
    return f"CON {text}"


def END(text):
    return f"END {text}"