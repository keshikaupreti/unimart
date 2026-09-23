from django.conf import settings
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models

from core.models import TimeStampedModel
from transactions.models import Transaction


class Review(TimeStampedModel):
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_written",
    )

    reviewed_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_received",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    )

    comment = models.TextField(
        blank=True,
    )

    def __str__(self):
        return (
            f"{self.reviewer.username} → "
            f"{self.reviewed_user.username}: "
            f"{self.rating}/5"
        )

    class Meta:
        ordering = [
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "transaction",
                    "reviewer",
                ],
                name="one_review_per_user_per_transaction",
            ),

            models.CheckConstraint(
                condition=(
                    models.Q(rating__gte=1)
                    & models.Q(rating__lte=5)
                ),
                name="review_rating_between_1_and_5",
            ),
        ]