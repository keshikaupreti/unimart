from django.db.models import Q
from django.db import transaction

from rest_framework import (
    mixins,
    permissions,
    viewsets,
)

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from transactions.models import Transaction

from .models import (
    Dispute,
    Report,
)

from .serializers import (
    DisputeSerializer,
    ReportSerializer,
)


class ReportViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):

    serializer_class = ReportSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filterset_fields = [
        "status",
        "reason",
        "listing",
        "reported_user",
    ]

    def get_queryset(self):

        queryset = (
            Report.objects
            .select_related(
                "reporter",
                "listing",
                "reported_user",
                "resolved_by",
            )
        )

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(
            reporter=self.request.user
        )

    def perform_create(
        self,
        serializer,
    ):
        serializer.save(
            reporter=self.request.user
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            permissions.IsAdminUser,
        ],
    )
    def review(
        self,
        request,
        pk=None,
    ):
        obj = self.get_object()

        obj.status = (
            Report.Status.UNDER_REVIEW
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
        permission_classes=[
            permissions.IsAdminUser,
        ],
    )
    def resolve(
        self,
        request,
        pk=None,
    ):
        obj = self.get_object()

        obj.status = Report.Status.RESOLVED

        obj.admin_note = request.data.get(
            "admin_note",
            "",
        )

        obj.resolved_by = request.user

        obj.save(
            update_fields=[
                "status",
                "admin_note",
                "resolved_by",
                "updated_at",
            ]
        )

        return Response(
            self.get_serializer(obj).data
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            permissions.IsAdminUser,
        ],
    )
    def reject(
        self,
        request,
        pk=None,
    ):
        obj = self.get_object()

        obj.status = Report.Status.REJECTED

        obj.admin_note = request.data.get(
            "admin_note",
            "",
        )

        obj.resolved_by = request.user

        obj.save(
            update_fields=[
                "status",
                "admin_note",
                "resolved_by",
                "updated_at",
            ]
        )

        return Response(
            self.get_serializer(obj).data
        )


class DisputeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):

    serializer_class = DisputeSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filterset_fields = [
        "status",
        "reason",
        "transaction",
    ]

    def get_queryset(self):

        queryset = (
            Dispute.objects
            .select_related(
                "transaction",
                "transaction__listing",
                "transaction__buyer",
                "transaction__seller",
                "opened_by",
                "resolved_by",
            )
        )

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(
            Q(
                transaction__buyer=
                self.request.user
            )
            |
            Q(
                transaction__seller=
                self.request.user
            )
        )

    def perform_create(
        self,
        serializer,
    ):
        with transaction.atomic():
            sale = Transaction.objects.select_for_update().get(
                pk=serializer.validated_data["transaction"].pk
            )
            serializer.validate_transaction(sale)
            serializer.save(opened_by=self.request.user)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            permissions.IsAdminUser,
        ],
    )
    def review(
        self,
        request,
        pk=None,
    ):
        obj = self.get_object()

        if obj.status not in (Dispute.Status.OPEN, Dispute.Status.UNDER_REVIEW):
            raise ValidationError("A closed dispute cannot be reopened.")

        obj.status = (
            Dispute.Status.UNDER_REVIEW
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
        permission_classes=[
            permissions.IsAdminUser,
        ],
    )
    def resolve(
        self,
        request,
        pk=None,
    ):
        obj = self.get_object()

        obj.status = Dispute.Status.RESOLVED

        obj.admin_note = request.data.get(
            "admin_note",
            "",
        )

        obj.resolved_by = request.user

        obj.save(
            update_fields=[
                "status",
                "admin_note",
                "resolved_by",
                "updated_at",
            ]
        )

        return Response(
            self.get_serializer(obj).data
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            permissions.IsAdminUser,
        ],
    )
    def reject(
        self,
        request,
        pk=None,
    ):
        obj = self.get_object()

        obj.status = Dispute.Status.REJECTED

        obj.admin_note = request.data.get(
            "admin_note",
            "",
        )

        obj.resolved_by = request.user

        obj.save(
            update_fields=[
                "status",
                "admin_note",
                "resolved_by",
                "updated_at",
            ]
        )

        return Response(
            self.get_serializer(obj).data
        )
