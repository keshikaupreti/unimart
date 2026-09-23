from django.db.models import (
    Avg,
    Count,
)

from rest_framework import (
    mixins,
    permissions,
    viewsets,
)

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import serializers

from .models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ReviewSerializer

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]

    filterset_fields = [
        "reviewed_user",
        "reviewer",
        "transaction",
        "rating",
    ]

    search_fields = [
        "comment",
        "reviewer__username",
        "reviewed_user__username",
    ]

    ordering_fields = [
        "rating",
        "created_at",
    ]

    ordering = [
        "-created_at",
    ]

    def get_queryset(self):
        return (
            Review.objects
            .select_related(
                "transaction",
                "reviewer",
                "reviewed_user",
            )
        )

    def perform_create(
        self,
        serializer,
    ):
        transaction = serializer.validated_data[
            "transaction"
        ]

        user = self.request.user

        if user.id == transaction.buyer_id:
            reviewed_user = transaction.seller

        else:
            reviewed_user = transaction.buyer

        serializer.save(
            reviewer=user,
            reviewed_user=reviewed_user,
        )

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[
            permissions.AllowAny,
        ],
    )
    def summary(
        self,
        request,
    ):
        user_id = request.query_params.get(
            "user"
        )

        if not user_id:
            raise ValidationError(
                {
                    "user": (
                        "User ID is required."
                    )
                }
            )

        user_id = serializers.UUIDField().run_validation(user_id)

        stats = (
            Review.objects
            .filter(
                reviewed_user_id=user_id
            )
            .aggregate(
                average_rating=Avg(
                    "rating"
                ),
                review_count=Count(
                    "id"
                ),
            )
        )

        return Response(
            {
                "user": user_id,
                "average_rating": (
                    round(
                        stats[
                            "average_rating"
                        ],
                        2,
                    )
                    if stats[
                        "average_rating"
                    ]
                    is not None
                    else None
                ),
                "review_count": stats[
                    "review_count"
                ],
            }
        )
