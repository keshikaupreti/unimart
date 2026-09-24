from rest_framework import serializers

from accounts.serializers import PublicUserSerializer
from listings.models import Listing

from .models import Conversation, Message


class ConversationSerializer(serializers.ModelSerializer):
    archived = serializers.SerializerMethodField()

    def get_archived(self, obj):
        user = self.context["request"].user
        return obj.buyer_archived if user.id == obj.buyer_id else obj.seller_archived

    buyer = PublicUserSerializer(read_only=True)
    seller = PublicUserSerializer(read_only=True)
    listing_title = serializers.CharField(source="listing.title", read_only=True)

    class Meta:
        model = Conversation
        fields = (
            "id", "listing", "listing_title", "buyer", "seller", "archived",
            "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "buyer", "seller", "created_at", "updated_at",
        )

    def validate_listing(self, listing):
        user = self.context["request"].user
        if listing.seller_id == user.id:
            raise serializers.ValidationError(
                "You cannot start a conversation about your own listing."
            )
        if listing.status != Listing.Status.AVAILABLE:
            raise serializers.ValidationError(
                "Conversations can only start on available listings."
            )
        if Conversation.objects.filter(listing=listing, buyer=user).exists():
            raise serializers.ValidationError(
                "You already have a conversation for this listing."
            )
        return listing


class MessageSerializer(serializers.ModelSerializer):
    sender = PublicUserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "sender", "content", "created_at")
        read_only_fields = ("id", "sender", "created_at")

    def validate_content(self, content):
        content = content.strip()
        if not content:
            raise serializers.ValidationError("Message cannot be empty.")
        return content
