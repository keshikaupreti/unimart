from rest_framework.routers import DefaultRouter

from .views import (
    DisputeViewSet,
    ReportViewSet,
)


router = DefaultRouter()


router.register(
    "reports",
    ReportViewSet,
    basename="report",
)


router.register(
    "disputes",
    DisputeViewSet,
    basename="dispute",
)


urlpatterns = router.urls