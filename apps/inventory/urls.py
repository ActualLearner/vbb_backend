from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BloodRequestViewSet, BloodUnitViewSet, InventorySummaryViewSet

router = DefaultRouter()
router.register(r"blood-units", BloodUnitViewSet, basename="bloodunit")
router.register(r"blood-requests", BloodRequestViewSet, basename="bloodrequest")
router.register(
    r"inventory-summary", InventorySummaryViewSet, basename="inventory-summary"
)
urlpatterns = [
    path("", include(router.urls)),
]
