from django.utils import timezone
from rest_framework import serializers

from accounts.serializers import PublicUserSerializer
from listings.models import Listing

from .models import (
    MeetupLocation,
    Transaction,
)


class MeetupLocationSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = MeetupLocation

        fields = (
            "id",
            "name",
            "description",
        )


class TransactionSerializer(
    serializers.ModelSerializer
):
    buyer = PublicUserSerializer(
        read_only=True,
    )

    seller = PublicUserSerializer(
        read_only=True,
    )

    listing_title = serializers.CharField(
        source="listing.title",
        read_only=True,
    )

    meetup_location_detail = (
        MeetupLocationSerializer(
            source="meetup_location",
            read_only=True,
        )
    )

    class Meta:
        model = Transaction

        fields = (
            "id",

            "listing",
            "listing_title",

            "buyer",
            "seller",

            "meetup_location",
            "meetup_location_detail",
            "meetup_time",

            "status",

            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "buyer",
            "seller",
            "status",
            "created_at",
            "updated_at",
        )

    def validate_listing(self, listing):
        request = self.context["request"]

        if listing.seller_id == request.user.id:
            raise serializers.ValidationError(
                "You cannot buy your own listing."
            )

        if listing.status != Listing.Status.AVAILABLE:
            raise serializers.ValidationError(
                "This listing is not available."
            )

        return listing

    def validate_meetup_location(
        self,
        location,
    ):
        if not location.is_active:
            raise serializers.ValidationError(
                "This meetup location is unavailable."
            )

        return location

    def validate_meetup_time(
        self,
        meetup_time,
    ):
        if meetup_time <= timezone.now():
            raise serializers.ValidationError(
                "Meetup time must be in the future."
            )

        return meetup_time

    def validate(self, attrs):
        request = self.context["request"]

        listing = attrs.get("listing")

        existing = Transaction.objects.filter(
            listing=listing,
            buyer=request.user,
            status__in=[
                Transaction.Status.REQUESTED,
                Transaction.Status.ACCEPTED,
            ],
        ).exists()

        if existing:
            raise serializers.ValidationError(
                "You already have an active "
                "request for this listing."
            )

        return attrs