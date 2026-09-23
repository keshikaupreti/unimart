from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from listings.models import Listing


class MeetupLocation(TimeStampedModel):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Transaction(TimeStampedModel):

    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    listing = models.ForeignKey(
        Listing,
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="purchases",
    )

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sales",
    )

    meetup_location = models.ForeignKey(
        MeetupLocation,
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    meetup_time = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.REQUESTED,
    )

    def __str__(self):
        return (
            f"{self.listing.title} - "
            f"{self.buyer.username}"
        )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["status"],
            ),
            models.Index(
                fields=["listing", "status"],
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "listing",
                    "buyer",
                ],
                condition=models.Q(
                    status__in=[
                        "requested",
                        "accepted",
                    ]
                ),
                name="unique_active_buyer_request",
            ),

            models.UniqueConstraint(
                fields=[
                    "listing",
                ],
                condition=models.Q(
                    status="accepted",
                ),
                name="one_accepted_transaction_per_listing",
            ),
        ]