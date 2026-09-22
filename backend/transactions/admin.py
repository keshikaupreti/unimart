from django.contrib import admin

from .models import (
    MeetupLocation,
    Transaction,
)


@admin.register(MeetupLocation)
class MeetupLocationAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "name",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
    )


@admin.register(Transaction)
class TransactionAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "listing",
        "buyer",
        "seller",
        "meetup_location",
        "meetup_time",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "meetup_location",
    )

    search_fields = (
        "listing__title",
        "buyer__username",
        "seller__username",
    )

    autocomplete_fields = (
        "buyer",
        "seller",
    )