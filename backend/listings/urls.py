from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    ListingImageViewSet,
    ListingViewSet,
    SavedListingViewSet,
)


router = DefaultRouter()


router.register(
    "categories",
    CategoryViewSet,
    basename="category",
)


router.register(
    "listings",
    ListingViewSet,
    basename="listing",
)


router.register(
    "listing-images",
    ListingImageViewSet,
    basename="listing-image",
)

router.register(
    "saved-listings",
    SavedListingViewSet,
    basename="saved-listing",
)


urlpatterns = router.urls
