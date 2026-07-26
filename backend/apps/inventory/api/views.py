from dataclasses import asdict

from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.services import record_audit
from core.permissions import PasswordChangeNotRequired
from users.permissions import IsClinician, IsSupply

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
    RejectRequestSerializer,
)


@extend_schema(
    parameters=[
        OpenApiParameter(
            "facility_pk",
            OpenApiTypes.UUID,
            OpenApiParameter.PATH,
            description="Facility ID.",
        )
    ]
)
class BloodUnitViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing blood units FOR A SPECIFIC FACILITY.
    Accessed via /api/v1/facilities/{facility_pk}/inventory/

    Read access for any authenticated user (SRS 3.3.3). Write access only for
    SUPPLY staff updating their own facility (ADR-0008 permission matrix).
    """

    # Schema generation needs a model queryset; requests use get_queryset().
    queryset = BloodUnit.objects.none()
    serializer_class = BloodUnitSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BloodUnitFilter

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsSupply(), PasswordChangeNotRequired()]
        return [IsAuthenticated(), PasswordChangeNotRequired()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return BloodUnit.objects.none()
        facility_pk = self.kwargs.get("facility_pk")
        try:
            facility = Facility.objects.get(pk=facility_pk)
            return BloodUnit.objects.filter(facility=facility).order_by("-donated_at")
        except Facility.DoesNotExist:
            return BloodUnit.objects.none()

    def perform_create(self, serializer):
        facility_pk = self.kwargs.get("facility_pk")
        try:
            facility = Facility.objects.get(pk=facility_pk)
        except Facility.DoesNotExist:
            raise ValidationError("Facility not found.") from None
        # Supply staff may only add to their own facility's inventory.
        if self.request.user.facility_id != facility.id:
            raise PermissionDenied("You can only add blood units to your own facility.")
        unit = serializer.save(facility=facility)
        record_audit(
            self.request.user,
            "inventory.add_unit",
            target=facility,
            metadata={"blood_type": unit.blood_type},
        )


class BloodRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and managing blood requests.
    Includes custom actions for the request lifecycle.
    """

    queryset = (
        BloodRequest.objects.all()
        .select_related("requesting_facility", "fulfilling_facility", "requested_by")
        .prefetch_related("status_events")
        .order_by("-created_at")
    )
    serializer_class = BloodRequestSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BloodRequestFilter

    def get_permissions(self):
        if self.action in ["accept", "reject", "ship"]:
            permission_classes = [IsFulfillingFacilityUser]
        elif self.action in ["receive", "cancel"]:
            permission_classes = [IsRequestingFacilityUser]
        elif self.action == "create":
            # Only clinicians raise requests (ADR-0008).
            permission_classes = [IsClinician]
        else:
            permission_classes = [IsAuthenticated]
        permission_classes = permission_classes + [PasswordChangeNotRequired]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        request_obj = serializer.save(
            requested_by=self.request.user,
            requesting_facility=self.request.user.facility,
        )
        record_audit(
            self.request.user,
            "blood_request.create",
            target=request_obj,
            metadata={
                "fulfilling_facility": str(request_obj.fulfilling_facility_id),
                "blood_type": request_obj.blood_type,
                "units": request_obj.units_requested,
            },
        )

    def _respond(self, result):
        if result.error:
            # Raise so the response uses the standardized error envelope
            # (ADR-0010) instead of an ad-hoc {"error": ...} body.
            raise ValidationError(result.error)
        # The object was fetched with prefetched status_events before the
        # transition added a new one; drop the cache so the response reflects
        # the freshly recorded history.
        result.request._prefetched_objects_cache = {}
        return Response(self.get_serializer(result.request).data)

    @extend_schema(request=None, responses=BloodRequestSerializer)
    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        result = BloodRequestTransitionService(
            low_stock_threshold=LOW_STOCK_THRESHOLD
        ).accept(request.user, self.get_object())
        return self._respond(result)

    @extend_schema(request=None, responses=BloodRequestSerializer)
    @action(detail=True, methods=["post"])
    def ship(self, request, pk=None):
        result = BloodRequestTransitionService().ship(request.user, self.get_object())
        return self._respond(result)

    @extend_schema(request=None, responses=BloodRequestSerializer)
    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        result = BloodRequestTransitionService().receive(
            request.user, self.get_object()
        )
        return self._respond(result)

    @extend_schema(request=None, responses=BloodRequestSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        result = BloodRequestTransitionService().cancel(request.user, self.get_object())
        return self._respond(result)

    @extend_schema(request=RejectRequestSerializer, responses=BloodRequestSerializer)
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        reason = (
            request.data.get("reason", "") if isinstance(request.data, dict) else ""
        )
        result = BloodRequestTransitionService().reject(
            request.user, self.get_object(), reason=reason
        )
        return self._respond(result)


class InventorySummaryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = InventorySummarySerializer
    pagination_class = None
    filter_backends = []

    def get_queryset(self):
        queryset = (
            BloodUnit.objects.values("facility__id", "facility__name", "blood_type")
            .annotate(total_units=models.Count("id"))
            .order_by("facility__name", "blood_type")
        )
        if "facility_pk" in self.kwargs:
            return queryset.filter(facility__id=self.kwargs["facility_pk"])
        return queryset


class DistrictInventoryView(APIView):
    """District-wide inventory across cooperating facilities (SRS PROC-BIM-004).

    Returns aggregated unit counts for every active facility sharing the
    requesting user's woreda (district). Supports ``?search=`` over facility
    name and ``?blood_type=`` filtering (PROC-BIM-005).
    """

    permission_classes = [IsAuthenticated, PasswordChangeNotRequired]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "search",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Filter by facility name (case-insensitive contains).",
            ),
            OpenApiParameter(
                "blood_type",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Filter by blood type (e.g. A+, O-).",
            ),
        ],
        responses=InventorySummarySerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        facility = request.user.facility
        if not facility:
            raise ValidationError("User is not associated with a facility.")

        qs = BloodUnit.objects.filter(
            facility__woreda=facility.woreda, facility__is_active=True
        )
        search = request.query_params.get("search")
        if search:
            qs = qs.filter(facility__name__icontains=search)
        blood_type = request.query_params.get("blood_type")
        if blood_type:
            qs = qs.filter(blood_type=blood_type)

        rows = (
            qs.values("facility__id", "facility__name", "blood_type")
            .annotate(total_units=models.Count("id"))
            .order_by("facility__name", "blood_type")
        )
        return Response(InventorySummarySerializer(rows, many=True).data)


class DashboardAPIView(APIView):
    """
    Provides a single endpoint for all data required for the user's dashboard.
    Fulfills SRS requirements 3.6.
    """

    permission_classes = [IsAuthenticated, PasswordChangeNotRequired]

    LOW_STOCK_THRESHOLD = LOW_STOCK_THRESHOLD

    @extend_schema(responses=DashboardSerializer)
    def get(self, request, *args, **kwargs):
        facility = request.user.facility
        if not facility:
            raise ValidationError("User is not associated with a facility.")

        dashboard_data = FacilityDashboardService(
            low_stock_threshold=self.LOW_STOCK_THRESHOLD
        ).get_dashboard(facility)

        serializer = DashboardSerializer(data=asdict(dashboard_data))
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
