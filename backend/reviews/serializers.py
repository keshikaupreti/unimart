from rest_framework import serializers

from accounts.serializers import (
    PublicUserSerializer,
)

from transactions.models import Transaction

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    reviewer = PublicUserSerializer(
        read_only=True,
    )

    reviewed_user = PublicUserSerializer(
        read_only=True,
    )

    class Meta:
        model = Review

        fields = (
            "id",
            "transaction",
            "reviewer",
            "reviewed_user",
            "rating",
            "comment",
            "created_at",
        )

        read_only_fields = (
            "id",
            "reviewer",
            "reviewed_user",
            "created_at",
        )

    def validate(self, attrs):
        request = self.context["request"]

        transaction = attrs.get(
            "transaction"
        )

        if (
            transaction.status
            != Transaction.Status.COMPLETED
        ):
            raise serializers.ValidationError(
                "Reviews are only allowed "
                "after the transaction is completed."
            )

        user_id = request.user.id

        participants = (
            transaction.buyer_id,
            transaction.seller_id,
        )

        if user_id not in participants:
            raise serializers.ValidationError(
                "You are not part of this transaction."
            )

        already_reviewed = (
            Review.objects.filter(
                transaction=transaction,
                reviewer=request.user,
            ).exists()
        )

        if already_reviewed:
            raise serializers.ValidationError(
                "You already reviewed this transaction."
            )

        return attrs