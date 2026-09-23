from django.db import transaction
from django.db.models import Q

from rest_framework import (
    mixins,
    permissions,
    status,
    viewsets,
)

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from listings.models import Listing

from .models import (
    MeetupLocation,
    Transaction,
)

from .serializers import (
    MeetupLocationSerializer,
    TransactionSerializer,
)


class MeetupLocationViewSet(
    viewsets.ReadOnlyModelViewSet
):
    serializer_class = MeetupLocationSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        return MeetupLocation.objects.filter(
            is_active=True
        )


class TransactionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TransactionSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filterset_fields = [
        "status",
        "listing",
    ]

    ordering_fields = [
        "created_at",
        "meetup_time",
    ]

    ordering = [
        "-created_at",
    ]

    def get_queryset(self):
        queryset = (
            Transaction.objects
            .select_related(
                "listing",
                "buyer",
                "seller",
                "meetup_location",
            )
        )

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(
            Q(buyer=self.request.user)
            | Q(seller=self.request.user)
        )

    def perform_create(
        self,
        serializer,
    ):
        listing = serializer.validated_data[
            "listing"
        ]

        serializer.save(
            buyer=self.request.user,
            seller=listing.seller,
        )

    def _locked_transaction(
        self,
        pk,
    ):
        obj = get_object_or_404(
            self.get_queryset().select_for_update(), pk=pk
        )

        self.check_object_permissions(
            self.request,
            obj,
        )

        return obj

    @action(
        detail=True,
        methods=["post"],
    )
    def accept(
        self,
        request,
        pk=None,
    ):
        with transaction.atomic():

            obj = self._locked_transaction(pk)

            listing = (
                Listing.objects
                .select_for_update()
                .get(pk=obj.listing_id)
            )

            if (
                request.user.id != obj.seller_id
                and not request.user.is_staff
            ):
                raise ValidationError(
                    "Only the seller can "
                    "accept this request."
                )

            if (
                obj.status
                != Transaction.Status.REQUESTED
            ):
                raise ValidationError(
                    "Only requested transactions "
                    "can be accepted."
                )

            if (
                listing.status
                != Listing.Status.AVAILABLE
            ):
                raise ValidationError(
                    "This listing is no longer "
                    "available."
                )

            obj.status = (
                Transaction.Status.ACCEPTED
            )

            obj.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            listing.status = (
                Listing.Status.RESERVED
            )

            listing.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            Transaction.objects.filter(
                listing=listing,
                status=Transaction.Status.REQUESTED,
            ).exclude(
                pk=obj.pk
            ).update(
                status=Transaction.Status.REJECTED
            )

        return Response(
            self.get_serializer(obj).data
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def reject(
        self,
        request,
        pk=None,
    ):
        obj = self.get_object()

        if (
            request.user.id != obj.seller_id
            and not request.user.is_staff
        ):
            raise ValidationError(
                "Only the seller can "
                "reject this request."
            )

        if (
            obj.status
            != Transaction.Status.REQUESTED
        ):
            raise ValidationError(
                "Only requested transactions "
                "can be rejected."
            )

        obj.status = Transaction.Status.REJECTED

        obj.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            self.get_serializer(obj).data
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def cancel(
        self,
        request,
        pk=None,
    ):
        with transaction.atomic():

            obj = self._locked_transaction(pk)

            if obj.status not in [
                Transaction.Status.REQUESTED,
                Transaction.Status.ACCEPTED,
            ]:
                raise ValidationError(
                    "This transaction cannot "
                    "be cancelled."
                )

            if (
                obj.status
                == Transaction.Status.REQUESTED
                and request.user.id
                != obj.buyer_id
                and not request.user.is_staff
            ):
                raise ValidationError(
                    "The buyer should cancel "
                    "a request. Sellers can "
                    "reject it."
                )

            if (
                obj.status
                == Transaction.Status.ACCEPTED
            ):
                listing = (
                    Listing.objects
                    .select_for_update()
                    .get(pk=obj.listing_id)
                )

                listing.status = (
                    Listing.Status.AVAILABLE
                )

                listing.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

            obj.status = (
                Transaction.Status.CANCELLED
            )

            obj.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        return Response(
            self.get_serializer(obj).data
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def complete(
        self,
        request,
        pk=None,
    ):
        with transaction.atomic():

            obj = self._locked_transaction(pk)

            listing = (
                Listing.objects
                .select_for_update()
                .get(pk=obj.listing_id)
            )

            if (
                request.user.id != obj.seller_id
                and not request.user.is_staff
            ):
                raise ValidationError(
                    "Only the seller can "
                    "complete this transaction."
                )

            if (
                obj.status
                != Transaction.Status.ACCEPTED
            ):
                raise ValidationError(
                    "Only accepted transactions "
                    "can be completed."
                )

            obj.status = (
                Transaction.Status.COMPLETED
            )

            obj.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            listing.status = (
                Listing.Status.SOLD
            )

            listing.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        return Response(
            self.get_serializer(obj).data,
            status=status.HTTP_200_OK,
        )
