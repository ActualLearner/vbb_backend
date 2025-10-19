from django.db import models, transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.permissions import IsAdminUser

from .models import BloodRequest, BloodUnit, Facility

# Import our new permissions and Django's admin permission
from .permissions import IsFulfillingFacilityUser, IsRequestingFacilityUser
from .serializers import (
    BloodRequestSerializer,
    BloodUnitSerializer,
    InventorySummarySerializer,
)


class BloodUnitViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing blood units FOR A SPECIFIC FACILITY.
    Accessed via /api/v1/facilities/{facility_pk}/inventory/
    """

    serializer_class = BloodUnitSerializer
    permission_classes = [IsAuthenticated]

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
        if request_obj.status != BloodRequest.RequestStatus.PENDING:
            return Response(
                {"error": "Request is not in PENDING state."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                # Lock the blood units table for this facility and
                # blood type to prevent race conditions
                available_units = BloodUnit.objects.select_for_update().filter(
                    facility=request_obj.fulfilling_facility,
                    blood_type=request_obj.blood_type,
                )

                if available_units.count() < request_obj.units_requested:
                    request_obj.status = BloodRequest.RequestStatus.REJECTED
                    request_obj.save()
                    return Response(
                        {
                            "error": (
                                "Insufficient stock to accept this request. "
                                "Request has been rejected."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Deduct the oldest units first
                units_to_remove = available_units.order_by("expires_at")[
                    : request_obj.units_requested
                ]
                BloodUnit.objects.filter(
                    pk__in=[unit.pk for unit in units_to_remove]
                ).delete()

                request_obj.status = BloodRequest.RequestStatus.ACCEPTED
                request_obj.save()

                # TODO: Implement push notification logic here

                serializer = self.get_serializer(request_obj)
                return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def ship(self, request, pk=None):
        """Mark the accepted request as in transit."""
        request_obj = self.get_object()
        if request_obj.status != BloodRequest.RequestStatus.ACCEPTED:
            return Response(
                {"error": "Request must be ACCEPTED before shipping."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_obj.status = BloodRequest.RequestStatus.IN_TRANSIT
        request_obj.save()
        # TODO: Implement push notification logic here
        serializer = self.get_serializer(request_obj)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        """
        Confirm receipt of the blood units. This adds units to the requesting facility.
        """
        request_obj = self.get_object()
        if request_obj.status != BloodRequest.RequestStatus.IN_TRANSIT:
            return Response(
                {"error": "Request is not IN_TRANSIT."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # NOTE: In a real system, you'd transfer the exact expiry dates.
            # For simplicity, we create new units here.
            from datetime import date, timedelta

            new_units = [
                BloodUnit(
                    facility=request_obj.requesting_facility,
                    blood_type=request_obj.blood_type,
                    expires_at=date.today() + timedelta(days=42),  # Standard expiry
                )
                for _ in range(request_obj.units_requested)
            ]
            BloodUnit.objects.bulk_create(new_units)

            request_obj.status = BloodRequest.RequestStatus.FULFILLED
            request_obj.save()

            # TODO: Implement push notification logic here

            serializer = self.get_serializer(request_obj)
            return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a pending request."""
        request_obj = self.get_object()
        if request_obj.status != BloodRequest.RequestStatus.PENDING:
            return Response(
                {"error": "Only PENDING requests can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_obj.status = BloodRequest.RequestStatus.CANCELLED
        request_obj.save()
        serializer = self.get_serializer(request_obj)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """Reject a pending request."""
        request_obj = self.get_object()
        if request_obj.status != BloodRequest.RequestStatus.PENDING:
            return Response(
                {"error": "Only PENDING requests can be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_obj.status = BloodRequest.RequestStatus.REJECTED
        request_obj.save()
        serializer = self.get_serializer(request_obj)
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
