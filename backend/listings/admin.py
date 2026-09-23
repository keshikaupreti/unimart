from django.contrib import admin

from .models import (
    Category,
    Listing,
    ListingImage,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "slug",
    )

    prepopulated_fields = {
        "slug": (
            "name",
        )
    }


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 0


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "seller",
        "category",
        "price",
        "condition",
        "status",
        "created_at",
    )

    list_filter = (
        "category",
        "condition",
        "status",
    )

    search_fields = (
        "title",
        "seller__username",
    )

    inlines = [
        ListingImageInline,
    ]


@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "listing",
        "created_at",
    )