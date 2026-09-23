from rest_framework import serializers

from accounts.serializers import (
    PublicUserSerializer,
)

from .models import (
    Category,
    Listing,
    ListingImage,
    SavedListing,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category

        fields = (
            "id",
            "name",
            "slug",
        )


class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage

        fields = (
            "id",
            "listing",
            "image",
            "created_at",
        )

        read_only_fields = (
            "id",
            "created_at",
        )


class ListingSerializer(serializers.ModelSerializer):
    seller = PublicUserSerializer(
        read_only=True,
    )

    images = ListingImageSerializer(
        many=True,
        read_only=True,
    )

    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    class Meta:
        model = Listing

        fields = (
            "id",
            "seller",
            "category",
            "category_name",
            "title",
            "description",
            "price",
            "condition",
            "status",
            "images",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "seller",
            "status",
            "created_at",
            "updated_at",
        )


class SavedListingSerializer(serializers.ModelSerializer):
    listing_detail = ListingSerializer(source="listing", read_only=True)

    class Meta:
        model = SavedListing
        fields = ("id", "user", "listing", "listing_detail", "created_at")
        read_only_fields = ("id", "user", "listing_detail", "created_at")

    def validate_listing(self, listing):
        user = self.context["request"].user
        if listing.seller_id == user.id:
            raise serializers.ValidationError("You cannot save your own listing.")
        if listing.status != Listing.Status.AVAILABLE:
            raise serializers.ValidationError("Only available listings can be saved.")
        if SavedListing.objects.filter(user=user, listing=listing).exists():
            raise serializers.ValidationError("This listing is already saved.")
        return listing
