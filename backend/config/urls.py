from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_nested import routers
from rest_framework_simplejwt.views import TokenRefreshView

from donations.api.views import DonationCenterViewSet
from inventory.api.views import (
    BloodRequestViewSet,
    BloodUnitViewSet,
    DashboardAPIView,
    DistrictInventoryView,
    InventorySummaryViewSet,
)
from notifications.api.views import NotificationRecordViewSet
from users.api.views import (
    ChangePasswordView,
    EmailOrPhoneTokenView,
    FacilityViewSet,
    LogoutView,
    MeView,
    UserViewSet,
)

# --- 1. Top-Level Router ---
router = routers.DefaultRouter()
router.register(r"facilities", FacilityViewSet, basename="facility")
router.register(r"users", UserViewSet, basename="user")
router.register(r"blood-requests", BloodRequestViewSet, basename="bloodrequest")
router.register(r"notifications", NotificationRecordViewSet, basename="notification")
router.register(r"donation-centers", DonationCenterViewSet, basename="donationcenter")


# --- 2. Nested Router (under /facilities/{facility_pk}/) ---
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


# --- 3. Auth (JWT) ---
auth_patterns = [
    path("login/", EmailOrPhoneTokenView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
]

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="login-page"),
    path("healthz/", healthz, name="healthz"),
    path("admin/", admin.site.urls),
    # AllAuth URLS (account management, social, email password reset)
    path("accounts/", include("allauth.urls")),
    path("_allauth/", include("allauth.headless.urls")),
    # --- API URLS ---
    # OpenAPI schema + interactive docs. Unauthenticated on purpose: the
    # schema is not sensitive and the mobile/web teams consume it directly
    # (permissions come from SPECTACULAR_SETTINGS SERVE_PERMISSIONS).
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/v1/auth/", include(auth_patterns)),
    path("api/v1/", include(router.urls + facilities_router.urls)),
    path("api/v1/dashboard/", DashboardAPIView.as_view(), name="dashboard"),
    path(
        "api/v1/district-inventory/",
        DistrictInventoryView.as_view(),
        name="district-inventory",
    ),
]
