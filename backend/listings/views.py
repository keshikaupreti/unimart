from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from rest_framework import (
    mixins,
    permissions,
    status,
    viewsets,
)

from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError,
)

from rest_framework.parsers import (
    FormParser,
    MultiPartParser,
)
from rest_framework.response import Response

from transactions.models import Transaction

from .models import (
    Category,
    Listing,
    ListingImage,
    SavedListing,
)

from .permissions import (
    IsAdminOrReadOnly,
    IsListingImageOwner,
    IsSellerOrReadOnly,
)

from .serializers import (
    CategorySerializer,
    ListingImageSerializer,
    ListingSerializer,
    SavedListingSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()

    serializer_class = CategorySerializer

    permission_classes = [
        IsAdminOrReadOnly,
    ]

    search_fields = [
        "name",
    ]

    ordering_fields = [
        "name",
        "created_at",
    ]


class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsSellerOrReadOnly,
    ]

    filterset_fields = {
        "category": [
            "exact",
        ],

        "condition": [
            "exact",
        ],

        "status": [
            "exact",
        ],

        "price": [
            "gte",
            "lte",
        ],
    }

    search_fields = [
        "title",
        "description",
        "seller__username",
    ]

    ordering_fields = [
        "price",
        "created_at",
        "updated_at",
    ]

    ordering = [
        "-created_at",
    ]

    def get_queryset(self):
        queryset = (
            Listing.objects
            .select_related(
                "seller",
                "category",
            )
            .prefetch_related(
                "images",
            )
        )
        user = self.request.user
        if not user.is_staff:
            if user.is_authenticated:
                queryset = queryset.filter(
                    Q(seller=user) | ~Q(status=Listing.Status.REMOVED)
                )
            else:
                queryset = queryset.exclude(status=Listing.Status.REMOVED)
        if getattr(self, "action", None) in ("update", "partial_update", "destroy"):
            queryset = queryset.select_for_update()
        return queryset

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        listing = self.get_object()
        if listing.status == Listing.Status.RESERVED:
            raise ValidationError(
                "Cancel the accepted transaction before removing this listing."
            )

        listing.status = Listing.Status.REMOVED
        listing.save(update_fields=["status", "updated_at"])
        Transaction.objects.filter(
            listing=listing, status=Transaction.Status.REQUESTED
        ).update(
            status=Transaction.Status.REJECTED,
            updated_at=timezone.now(),
        )
        listing.saved_by.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(
        self,
        serializer,
    ):
        serializer.save(
            seller=self.request.user
        )


class ListingImageViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = (
        ListingImage.objects
        .select_related(
            "listing",
            "listing__seller",
        )
    )

    serializer_class = ListingImageSerializer

    permission_classes = [
        permissions.IsAuthenticated,
        IsListingImageOwner,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def perform_create(
        self,
        serializer,
    ):
        listing = serializer.validated_data[
            "listing"
        ]

        user = self.request.user

        if (
            listing.seller_id != user.id
            and not user.is_staff
        ):
            raise PermissionDenied(
                "You cannot add images "
                "to another user's listing."
            )

        if not user.is_staff and listing.status != Listing.Status.AVAILABLE:
            raise PermissionDenied(
                "Images cannot be changed after a listing is reserved."
            )

        serializer.save()


class SavedListingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SavedListingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            SavedListing.objects.filter(user=self.request.user)
            .select_related("listing", "listing__seller", "listing__category")
            .prefetch_related("listing__images")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
