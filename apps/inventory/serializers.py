from rest_framework import serializers
from users.models import Facility
from users.serializers import FacilitySerializer  # This import now works!

from .models import BloodRequest, BloodUnit


class BloodUnitSerializer(serializers.ModelSerializer):
    facility = FacilitySerializer(read_only=True)
    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), source="facility", write_only=True
    )

    class Meta:
        model = BloodUnit
        fields = [
            "id",
            "blood_type",
            "facility",
            "facility_id",
            "donated_at",
            "expires_at",
        ]
        read_only_fields = ["donated_at"]


class BloodRequestSerializer(serializers.ModelSerializer):
    # These provide rich, nested data in GET responses
    requesting_facility = FacilitySerializer(read_only=True)
    fulfilling_facility = FacilitySerializer(read_only=True)
    requested_by = serializers.StringRelatedField(read_only=True)

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
            "status",
            "created_at",
        ]
        # Status & requesting_facility are now controlled entirely by the backend logic
        read_only_fields = [
            "created_at",
            "updated_at",
            "requested_by",
            "status",
            "requesting_facility",
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

        # Ensure a user isn't requesting from their own facility
        # The view's perform_create sets the requesting_facility
        # from the logged-in user.
        # We can access that user via the context that DRF passes to the serializer.
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


class InventorySummarySerializer(serializers.Serializer):
    """
    A read-only serializer for displaying aggregated blood unit counts.
    """

    # Tell DRF that the data for this field comes from the 'facility__id' key
    facility_id = serializers.IntegerField(source="facility__id")

    # Tell DRF that the data for this field comes from the 'facility__name' key
    facility_name = serializers.CharField(source="facility__name")

    # These two already match, so no 'source' argument is needed
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
    incoming_requests_count = serializers.IntegerField()
    incoming_requests_ids = serializers.ListField(child=serializers.IntegerField())
    outgoing_requests_count = serializers.IntegerField()
    outgoing_requests_ids = serializers.ListField(child=serializers.IntegerField())
