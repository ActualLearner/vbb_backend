from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from inventory.views import (
    BloodRequestViewSet,
    BloodUnitViewSet,
    InventorySummaryViewSet,
)
from rest_framework_nested import routers

# --- Import all the necessary ViewSets from your apps ---
from users.views import FacilityViewSet, SignupPageView, UserViewSet

# --- 1. Define the Top-Level Router ---
# This router handles /facilities/, /users/, and /blood-requests/
router = routers.DefaultRouter()
router.register(r"facilities", FacilityViewSet, basename="facility")
router.register(r"users", UserViewSet, basename="user")
router.register(r"blood-requests", BloodRequestViewSet, basename="bloodrequest")


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


# --- 3. Main URL Patterns ---
# The final list of all URLs for your project.
urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="login-page"),
    path("signup/", SignupPageView.as_view(), name="signup-page"),
    path("admin/", admin.site.urls),
    # Your existing allauth URLs
    path("accounts/", include("allauth.urls")),
    path("_allauth/", include("allauth.headless.urls")),
    # --- API URLS ---
    # Combine the URL patterns from both routers into a single list.
    # Then, include that list under the "api/v1/" prefix ONE TIME.
    # This is the correct way to handle this.
    path("api/v1/", include(router.urls + facilities_router.urls)),
]
