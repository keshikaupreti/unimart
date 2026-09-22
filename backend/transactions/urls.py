from rest_framework.routers import DefaultRouter

from .views import (
    MeetupLocationViewSet,
    TransactionViewSet,
)


router = DefaultRouter()


router.register(
    "meetup-locations",
    MeetupLocationViewSet,
    basename="meetup-location",
)


router.register(
    "transactions",
    TransactionViewSet,
    basename="transaction",
)


urlpatterns = router.urls