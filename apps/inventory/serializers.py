from rest_framework import serializers
from .models import BloodUnit, BloodRequest
from users.models import Facility, User
from users.serializers import FacilitySerializer  # This import now works!


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
    requesting_facility = FacilitySerializer(read_only=True)
    fulfilling_facility = FacilitySerializer(read_only=True)

    requesting_facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), source="requesting_facility", write_only=True
    )
    fulfilling_facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), source="fulfilling_facility", write_only=True
    )
    # The user who made the request will be set automatically based on the logged-in user.
    requested_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = BloodRequest
        fields = [
            "id",
            "requesting_facility",
            "fulfilling_facility",
            "requested_by",
            "blood_type",
            "units_requested",
            "status",
            "created_at",
            "requesting_facility_id",
            "fulfilling_facility_id",
        ]
        read_only_fields = ["created_at", "updated_at", "requested_by", "status"]
