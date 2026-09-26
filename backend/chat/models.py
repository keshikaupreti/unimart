from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from listings.models import Listing


class Conversation(TimeStampedModel):
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="conversations"
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="buying_conversations",
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="selling_conversations",
    )

    buyer_archived = models.BooleanField(default=False)
    seller_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["listing", "buyer"],
                name="one_conversation_per_buyer_per_listing",
            ),
        ]

    def __str__(self):
        return f"{self.listing.title}: {self.buyer} and {self.seller}"


class Message(TimeStampedModel):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    content = models.CharField(max_length=2000)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.sender} in {self.conversation_id}"
