from rest_framework import serializers

from accounts.serializers import PublicUserSerializer
from transactions.models import Transaction

from .models import (
    Dispute,
    Report,
)


class ReportSerializer(serializers.ModelSerializer):

    reporter = PublicUserSerializer(
        read_only=True,
    )

    resolved_by = PublicUserSerializer(
        read_only=True,
    )

    class Meta:
        model = Report

        fields = (
            "id",
            "reporter",
            "listing",
            "reported_user",
            "reason",
            "description",
            "status",
            "admin_note",
            "resolved_by",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "reporter",
            "status",
            "admin_note",
            "resolved_by",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):

        listing = attrs.get("listing")

        reported_user = attrs.get(
            "reported_user"
        )

        if bool(listing) == bool(reported_user):
            raise serializers.ValidationError(
                "Report either a listing or a user."
            )

        request = self.context["request"]

        if (
            reported_user
            and reported_user.id
            == request.user.id
        ):
            raise serializers.ValidationError(
                "You cannot report yourself."
            )

        return attrs


class DisputeSerializer(serializers.ModelSerializer):

    opened_by = PublicUserSerializer(
        read_only=True,
    )

    resolved_by = PublicUserSerializer(
        read_only=True,
    )

    listing_title = serializers.CharField(
        source="transaction.listing.title",
        read_only=True,
    )

    class Meta:
        model = Dispute

        fields = (
            "id",
            "transaction",
            "listing_title",
            "opened_by",
            "reason",
            "description",
            "status",
            "admin_note",
            "resolved_by",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "opened_by",
            "status",
            "admin_note",
            "resolved_by",
            "created_at",
            "updated_at",
        )

    def validate_transaction(
        self,
        transaction,
    ):

        request = self.context["request"]

        if request.user.id not in (
            transaction.buyer_id,
            transaction.seller_id,
        ):
            raise serializers.ValidationError(
                "You are not part of this transaction."
            )

        if transaction.status not in (
            Transaction.Status.ACCEPTED,
            Transaction.Status.COMPLETED,
        ):
            raise serializers.ValidationError(
                "A dispute can only be opened "
                "for an accepted or completed "
                "transaction."
            )

        if Dispute.objects.filter(
            transaction=transaction,
            status__in=[Dispute.Status.OPEN, Dispute.Status.UNDER_REVIEW],
        ).exists():
            raise serializers.ValidationError(
                "This transaction already has an active dispute."
            )

        return transaction
