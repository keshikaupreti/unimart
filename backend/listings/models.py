from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from core.models import TimeStampedModel


class Category(TimeStampedModel):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    slug = models.SlugField(
        unique=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]


class Listing(TimeStampedModel):

    class Condition(models.TextChoices):
        NEW = "new", "New"
        LIKE_NEW = "like_new", "Like New"
        GOOD = "good", "Good"
        FAIR = "fair", "Fair"
        POOR = "poor", "Poor"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"
        SOLD = "sold", "Sold"
        REMOVED = "removed", "Removed"

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="listings",
    )

    title = models.CharField(
        max_length=150,
    )

    description = models.TextField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    condition = models.CharField(
        max_length=20,
        choices=Condition,
        default=Condition.GOOD,
    )

    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.AVAILABLE,
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = [
            "-created_at",
        ]


class ListingImage(TimeStampedModel):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ImageField(
        upload_to="listings/",
    )

    def __str__(self):
        return f"Image for {self.listing.title}"


class SavedListing(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_listings",
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="saved_by",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "listing"],
                name="unique_saved_listing_per_user",
            ),
        ]
