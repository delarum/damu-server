"""
Credit and badge service layer.
All credit mutations go through here to keep the ledger consistent.
"""
from django.db import transaction
from .models import CreditLedger, DonationRecord, Badge, DonorBadge, CREDIT_RULES, BADGE_MILESTONES


def get_credit_balance(donor_profile):
    """Sum of all credit transactions for a donor."""
    from django.db.models import Sum
    result = CreditLedger.objects.filter(donor=donor_profile).aggregate(total=Sum("amount"))
    return result["total"] or 0


@transaction.atomic
def award_credits(donor_profile, amount, reason, transaction_type="earn", related_donation=None):
    """
    Award (or deduct) credits and append to the ledger.
    Returns the new balance.
    """
    current_balance = get_credit_balance(donor_profile)
    new_balance = current_balance + amount

    CreditLedger.objects.create(
        donor=donor_profile,
        transaction_type=transaction_type,
        amount=amount,
        balance_after=new_balance,
        reason=reason,
        related_donation=related_donation,
    )
    return new_balance


@transaction.atomic
def record_donation(donor_profile, hospital_profile, donation_type, donation_date, confirmed_by=None):
    """
    Record a donation, award credits, update cooldown, and check badge milestones.
    Returns the DonationRecord instance.
    """
    # Determine credits
    is_first = not DonationRecord.objects.filter(donor=donor_profile).exists()
    base_credits = CREDIT_RULES.get(donation_type, 100)
    total_credits = base_credits + (CREDIT_RULES["first_donation"] if is_first else 0)

    # Create donation record
    record = DonationRecord.objects.create(
        donor=donor_profile,
        hospital=hospital_profile,
        donation_type=donation_type,
        donation_date=donation_date,
        confirmed_by=confirmed_by,
        credits_awarded=total_credits,
    )

    # Award credits
    reason = f"{donation_type.replace('_', ' ').title()} donation"
    if is_first:
        reason += " + first donation bonus"
    award_credits(donor_profile, total_credits, reason, related_donation=record)

    # Update donor cooldown and last donation date
    donor_profile.last_donation_date = donation_date
    donor_profile.save(update_fields=["last_donation_date"])
    if donation_type != "organ":
        donor_profile.set_cooldown(donation_type)

    # Check badge milestones
    _check_and_award_badges(donor_profile)

    return record


def _check_and_award_badges(donor_profile):
    """Award badges based on total donation count."""
    total_donations = DonationRecord.objects.filter(donor=donor_profile).count()

    for milestone in BADGE_MILESTONES:
        if total_donations >= milestone["donations"]:
            badge, _ = Badge.objects.get_or_create(
                name=milestone["name"],
                defaults={
                    "title":               milestone["title"],
                    "icon":                milestone["icon"],
                    "required_donations":  milestone["donations"],
                },
            )
            DonorBadge.objects.get_or_create(donor=donor_profile, badge=badge)


def redeem_credits(donor_profile, amount, reason):
    """
    Redeem credits. Returns (success, message, new_balance).
    """
    balance = get_credit_balance(donor_profile)
    if amount > balance:
        return False, f"Insufficient credits. Balance: {balance}", balance

    new_balance = award_credits(
        donor_profile, -amount, reason, transaction_type="redeem"
    )
    return True, "Credits redeemed successfully", new_balance