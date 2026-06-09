from rest_framework import serializers
from .models import DonationRecord, CreditLedger, Badge, DonorBadge


class DonationRecordSerializer(serializers.ModelSerializer):
    hospital_name = serializers.CharField(source="hospital.facility_name", read_only=True)

    class Meta:
        model  = DonationRecord
        fields = [
            "id", "donation_type", "hospital_name",
            "donation_date", "credits_awarded", "created_at",
        ]
        read_only_fields = ["id", "credits_awarded", "created_at"]


class DonationRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DonationRecord
        fields = ["donor_id", "hospital_id", "donation_type", "donation_date"]


class CreditLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CreditLedger
        fields = ["id", "transaction_type", "amount", "balance_after", "reason", "created_at"]


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Badge
        fields = ["id", "name", "title", "icon", "required_donations"]


class DonorBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model  = DonorBadge
        fields = ["badge", "earned_at"]


class RedeemCreditsSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=255)