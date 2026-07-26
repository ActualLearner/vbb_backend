from datetime import date, timedelta

from rest_framework import serializers

from users.models import Facility
from users.serializers import FacilitySerializer  # This import now works!

from ..config import EXPIRING_SOON_DAYS
from ..models import BloodRequest, BloodRequestStatusEvent, BloodUnit


class BloodUnitSerializer(serializers.ModelSerializer):
    facility = FacilitySerializer(read_only=True)
    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), source="facility", write_only=True
    )
    is_expiring_soon = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = BloodUnit
        fields = [
            "id",
            "blood_type",
            "facility",
            "facility_id",
            "donated_at",
            "expires_at",
            "is_expiring_soon",
            "is_expired",
        ]
        read_only_fields = ["donated_at"]

    def get_is_expired(self, obj) -> bool:
        return obj.expires_at < date.today()

    def get_is_expiring_soon(self, obj) -> bool:
        # Within the expiring-soon window and not already expired (PROC-BIM-006).
        today = date.today()
        return today <= obj.expires_at <= today + timedelta(days=EXPIRING_SOON_DAYS)


class BloodRequestStatusEventSerializer(serializers.ModelSerializer):
    actor = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = BloodRequestStatusEvent
        fields = ["id", "from_status", "to_status", "actor", "created_at"]


class BloodRequestSerializer(serializers.ModelSerializer):
    # These provide rich, nested data in GET responses
    requesting_facility = FacilitySerializer(read_only=True)
    fulfilling_facility = FacilitySerializer(read_only=True)
    requested_by = serializers.StringRelatedField(read_only=True)
    status_events = BloodRequestStatusEventSerializer(many=True, read_only=True)

    # This is for creating/writing a request (POST)
    fulfilling_facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), source="fulfilling_facility", write_only=True
    )

    class Meta:
        model = BloodRequest
        fields = [
            "id",
            "requesting_facility",
            "fulfilling_facility",
            "fulfilling_facility_id",  # Only for writing
            "requested_by",
            "blood_type",
            "units_requested",
            "notes",
            "rejection_reason",
            "status",
            "created_at",
            "updated_at",
            "acceptance_timestamp",
            "dispatch_timestamp",
            "fulfillment_timestamp",
            "status_events",
        ]
        # Status & requesting_facility are now controlled entirely by the backend logic
        read_only_fields = [
            "created_at",
            "updated_at",
            "requested_by",
            "status",
            "rejection_reason",
            "requesting_facility",
            "acceptance_timestamp",
            "dispatch_timestamp",
            "fulfillment_timestamp",
        ]

    def validate(self, data):
        """
        Check that the fulfilling facility has enough blood units
        at the time of the request.

        A second check is performed at the time of acceptance.
        """
        fulfilling_facility = data.get("fulfilling_facility")
        blood_type = data.get("blood_type")
        units_requested = data.get("units_requested")

        # Ensure a user isn't requesting from their own facility.
        requesting_user = self.context["request"].user
        if fulfilling_facility == requesting_user.facility:
            raise serializers.ValidationError(
                "Cannot request blood from your own facility."
            )

        available_units = BloodUnit.objects.filter(
            facility=fulfilling_facility, blood_type=blood_type
        ).count()

        if available_units < units_requested:
            raise serializers.ValidationError(
                f"Not enough blood units. Facility has {available_units} "
                f"unit(s) of {blood_type}, but {units_requested} were requested."
            )

        return data


class RejectRequestSerializer(serializers.Serializer):
    """Request body for the reject action (optional free-text reason)."""

    reason = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )


class InventorySummarySerializer(serializers.Serializer):
    """
    A read-only serializer for displaying aggregated blood unit counts.
    """

    facility_id = serializers.CharField(source="facility__id")
    facility_name = serializers.CharField(source="facility__name")
    blood_type = serializers.CharField()
    total_units = serializers.IntegerField()

    class Meta:
        read_only_fields = ["facility_id", "facility_name", "blood_type", "total_units"]


class DashboardInventorySummarySerializer(serializers.Serializer):
    """A simple nested serializer for the inventory summary within the dashboard."""

    blood_type = serializers.CharField()
    total_units = serializers.IntegerField()


class DashboardSerializer(serializers.Serializer):
    """
    Serializes the aggregated data needed for the main user dashboard.
    This is a read-only serializer that structures the data from the DashboardAPIView.
    """

    inventory_summary = DashboardInventorySummarySerializer(many=True)
    low_stock_alerts = serializers.ListField(child=serializers.CharField())
    expiring_soon_alerts = serializers.ListField(child=serializers.CharField())
    incoming_requests_count = serializers.IntegerField()
    incoming_requests_ids = serializers.ListField(child=serializers.CharField())
    outgoing_requests_count = serializers.IntegerField()
    outgoing_requests_ids = serializers.ListField(child=serializers.CharField())
