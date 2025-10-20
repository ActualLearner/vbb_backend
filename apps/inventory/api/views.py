from dataclasses import asdict

from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.permissions import IsAdminUser

from ..config import LOW_STOCK_THRESHOLD
from ..domain.dashboard import FacilityDashboardService
from ..domain.transitions import BloodRequestTransitionService
from ..filters import BloodRequestFilter, BloodUnitFilter
from ..models import BloodRequest, BloodUnit, Facility
from ..permissions import IsFulfillingFacilityUser, IsRequestingFacilityUser
from .serializers import (
    BloodRequestSerializer,
    BloodUnitSerializer,
    DashboardSerializer,
    InventorySummarySerializer,
)


class BloodUnitViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing blood units FOR A SPECIFIC FACILITY.
    Accessed via /api/v1/facilities/{facility_pk}/inventory/
    """

    serializer_class = BloodUnitSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BloodUnitFilter

    def get_queryset(self):
        """
        This view should only return blood units for the facility
        specified in the URL.
        """
        facility_pk = self.kwargs.get("facility_pk")
        try:
            facility = Facility.objects.get(pk=facility_pk)
            return BloodUnit.objects.filter(facility=facility).order_by("-donated_at")
        except Facility.DoesNotExist:
            return BloodUnit.objects.none()

    def perform_create(self, serializer):
        """
        Automatically associate the blood unit with the facility from the URL.
        """
        facility_pk = self.kwargs.get("facility_pk")
        try:
            facility = Facility.objects.get(pk=facility_pk)
            # Only allow a facility rep to add to their own facility's inventory
            if (
                self.request.user.facility != facility
                and not self.request.user.is_staff
            ):
                raise ValidationError(
                    "You can only add blood units to your own facility."
                )
            serializer.save(facility=facility)
        except Facility.DoesNotExist:
            raise ValidationError("Facility not found.")


class BloodRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and managing blood requests.
    Includes custom actions for the request lifecycle.
    """

    queryset = (
        BloodRequest.objects.all()
        .select_related("requesting_facility", "fulfilling_facility", "requested_by")
        .order_by("-created_at")
    )
    serializer_class = BloodRequestSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BloodRequestFilter

    def get_permissions(self):
        """
        Assign permissions based on the action.
        """
        if self.action in ["accept", "reject", "ship"]:
            # Only the fulfilling facility can perform these actions
            permission_classes = [IsFulfillingFacilityUser | IsAdminUser]
        elif self.action in ["receive", "cancel"]:
            # Only the requesting facility can perform these actions
            permission_classes = [IsRequestingFacilityUser | IsAdminUser]
        else:
            # Default permissions for list, retrieve, create
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Set the 'requested_by' field to the current user and ensure the
        'requesting_facility' is the user's facility.
        """
        serializer.save(
            requested_by=self.request.user,
            requesting_facility=self.request.user.facility,
        )

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """
        Accept a blood request. This deducts units from the fulfilling facility.
        """
        request_obj = self.get_object()
        result = BloodRequestTransitionService(
            low_stock_threshold=LOW_STOCK_THRESHOLD
        ).accept(request.user, request_obj)

        if result.error:
            return Response({"error": result.error}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(result.request)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def ship(self, request, pk=None):
        """Mark the accepted request as in transit."""
        request_obj = self.get_object()
        result = BloodRequestTransitionService().ship(request.user, request_obj)
        if result.error:
            return Response({"error": result.error}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(result.request)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        """
        Confirm receipt of the blood units. This adds units to the requesting facility.
        """
        request_obj = self.get_object()
        result = BloodRequestTransitionService().receive(request.user, request_obj)
        if result.error:
            return Response({"error": result.error}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(result.request)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a pending request."""
        request_obj = self.get_object()
        result = BloodRequestTransitionService().cancel(request.user, request_obj)
        if result.error:
            return Response({"error": result.error}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(result.request)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """Reject a pending request."""
        request_obj = self.get_object()
        result = BloodRequestTransitionService().reject(request.user, request_obj)
        if result.error:
            return Response({"error": result.error}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(result.request)
        return Response(serializer.data)


# The InventorySummaryViewSet remains mostly the same, but we will adapt its
# queryset logic to handle nesting, similar to the BloodUnitViewSet.


class InventorySummaryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = InventorySummarySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = []

    def get_queryset(self):
        """
        If accessed via a nested URL, returns the summary for that specific facility.
        Otherwise, returns a summary for all facilities.
        """
        queryset = (
            BloodUnit.objects.values("facility__id", "facility__name", "blood_type")
            .annotate(total_units=models.Count("id"))
            .order_by("facility__name", "blood_type")
        )

        # Check if we're in a nested route
        if "facility_pk" in self.kwargs:
            facility_pk = self.kwargs["facility_pk"]
            return queryset.filter(facility__id=facility_pk)

        return queryset


class DashboardAPIView(APIView):
    """
    Provides a single endpoint for all data required for the user's dashboard.
    Fulfills SRS requirements 3.1.1.3.2 through 3.1.1.3.5.
    """

    permission_classes = [IsAuthenticated]

    # This can be adjusted later based on clinical requirements
    LOW_STOCK_THRESHOLD = LOW_STOCK_THRESHOLD

    def get(self, request, *args, **kwargs):
        user = self.request.user
        facility = user.facility

        if not facility:
            # Handle cases where a superuser or unassigned user hits the endpoint
            return Response(
                {"error": "User is not associated with a facility."}, status=400
            )

        dashboard_data = FacilityDashboardService(
            low_stock_threshold=self.LOW_STOCK_THRESHOLD
        ).get_dashboard(facility)

        # 5. Serialize and return the final, structured response
        serializer = DashboardSerializer(data=asdict(dashboard_data))
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
