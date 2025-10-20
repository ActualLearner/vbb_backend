from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import TemplateView
from inventory.api.views import (
    BloodRequestViewSet,
    BloodUnitViewSet,
    DashboardAPIView,
    InventorySummaryViewSet,
)
from notifications.api.views import NotificationRecordViewSet
from rest_framework_nested import routers
from users.api.views import FacilityViewSet, UserViewSet

# --- 1. Define the Top-Level Router ---
# This router handles /facilities/, /users/, and /blood-requests/
router = routers.DefaultRouter()
router.register(r"facilities", FacilityViewSet, basename="facility")
router.register(r"users", UserViewSet, basename="user")
router.register(r"blood-requests", BloodRequestViewSet, basename="bloodrequest")
router.register(r"notifications", NotificationRecordViewSet, basename="notification")


# --- 2. Define the Nested Router ---
# This router is dependent on the main 'router' and handles URLs
# nested under /facilities/{facility_pk}/
facilities_router = routers.NestedDefaultRouter(
    router, r"facilities", lookup="facility"
)
facilities_router.register(
    r"inventory", BloodUnitViewSet, basename="facility-inventory"
)
facilities_router.register(
    r"inventory-summary", InventorySummaryViewSet, basename="facility-inventory-summary"
)
facilities_router.register(r"staff", UserViewSet, basename="facility-staff")


def healthz(request):
    """Liveness probe for the platform health check. No auth, no DB access."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="login-page"),
    path("healthz/", healthz, name="healthz"),
    # signup handled by API/auth endpoints; legacy HTML signup removed
    path("admin/", admin.site.urls),
    # AllAuth URLS
    path("accounts/", include("allauth.urls")),
    path("_allauth/", include("allauth.headless.urls")),
    # --- API URLS ---
    path("api/v1/", include(router.urls + facilities_router.urls)),
    path("api/v1/dashboard/", DashboardAPIView.as_view(), name="dashboard"),
]
