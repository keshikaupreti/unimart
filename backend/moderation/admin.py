from django.contrib import admin

from .models import (
    Dispute,
    Report,
)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "reporter",
        "reason",
        "status",
        "listing",
        "reported_user",
        "created_at",
    )

    list_filter = (
        "status",
        "reason",
    )

    search_fields = (
        "reporter__username",
        "description",
        "listing__title",
        "reported_user__username",
    )


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "transaction",
        "opened_by",
        "reason",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "reason",
    )

    search_fields = (
        "opened_by__username",
        "description",
        "transaction__listing__title",
    )