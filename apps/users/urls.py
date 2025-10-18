from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FacilityViewSet, UserViewSet

# A Router automatically generates the URL patterns for a ViewSet.
router = DefaultRouter()
router.register(r"facilities", FacilityViewSet, basename="facility")
router.register(r"users", UserViewSet, basename="user")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("users", include(router.urls)),
]
