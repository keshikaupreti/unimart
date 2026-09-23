from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from listings.models import Listing
from transactions.models import Transaction


class Report(TimeStampedModel):

    class Reason(models.TextChoices):
        ILLEGAL = "illegal", "Illegal item"
        SCAM = "scam", "Scam"
        SPAM = "spam", "Spam"
        HARASSMENT = "harassment", "Harassment"
        MISLEADING = "misleading", "Misleading information"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        UNDER_REVIEW = "under_review", "Under Review"
        RESOLVED = "resolved", "Resolved"
        REJECTED = "rejected", "Rejected"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_created",
    )

    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="reports",
        blank=True,
        null=True,
    )

    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_received",
        blank=True,
        null=True,
    )

    reason = models.CharField(
        max_length=30,
        choices=Reason,
    )

    description = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.OPEN,
    )

    admin_note = models.TextField(
        blank=True,
    )

    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reports_resolved",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Report #{self.pk} - {self.reason}"

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        listing__isnull=False,
                        reported_user__isnull=True,
                    )
                    |
                    models.Q(
                        listing__isnull=True,
                        reported_user__isnull=False,
                    )
                ),
                name="report_exactly_one_target",
            )
        ]


class Dispute(TimeStampedModel):

    class Reason(models.TextChoices):
        ITEM_NOT_AS_DESCRIBED = (
            "item_not_as_described",
            "Item not as described",
        )

        BUYER_NO_SHOW = (
            "buyer_no_show",
            "Buyer did not arrive",
        )

        SELLER_NO_SHOW = (
            "seller_no_show",
            "Seller did not arrive",
        )

        DAMAGED_ITEM = (
            "damaged_item",
            "Damaged item",
        )

        PAYMENT = (
            "payment",
            "Payment disagreement",
        )

        HARASSMENT = (
            "harassment",
            "Harassment",
        )

        OTHER = (
            "other",
            "Other",
        )

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        UNDER_REVIEW = "under_review", "Under Review"
        RESOLVED = "resolved", "Resolved"
        REJECTED = "rejected", "Rejected"

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name="disputes",
    )

    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="disputes_opened",
    )

    reason = models.CharField(
        max_length=40,
        choices=Reason,
    )

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.OPEN,
    )

    admin_note = models.TextField(
        blank=True,
    )

    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="disputes_resolved",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Dispute #{self.pk}"

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["transaction"],
                condition=models.Q(
                    status__in=[
                        "open",
                        "under_review",
                    ]
                ),
                name="one_active_dispute_per_transaction",
            )
        ]