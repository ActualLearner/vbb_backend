from django.urls import include, path
from inventory.views import BloodUnitViewSet, InventorySummaryViewSet
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import FacilityViewSet, UserViewSet

# A Router automatically generates the URL patterns for a ViewSet.
router = DefaultRouter()
router.register(r"facilities", FacilityViewSet, basename="facility")
router.register(r"users", UserViewSet, basename="user")


facilities_router = routers.NestedDefaultRouter(
    router, r"facilities", lookup="facility"
)
facilities_router.register(
    r"inventory", BloodUnitViewSet, basename="facility-inventory"
)
facilities_router.register(
    r"inventory-summary", InventorySummaryViewSet, basename="facility-summary"
)
facilities_router.register(r"staff", UserViewSet, basename="facility-staff")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("users", include(router.urls)),
]
