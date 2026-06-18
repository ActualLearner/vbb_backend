from rest_framework import serializers

from ..models import DonationCenter


class DonationCenterSerializer(serializers.ModelSerializer):
    # Populated only by the `nearby` action; kilometres from the query point.
    distance_km = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = DonationCenter
        fields = [
            "id",
            "name",
            "street",
            "city",
            "latitude",
            "longitude",
            "operating_hours",
            "contact_info",
            "distance_km",
        ]
