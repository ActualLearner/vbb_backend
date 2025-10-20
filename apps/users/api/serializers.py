from rest_framework import serializers

from ..models import Facility, User


class FacilitySerializer(serializers.ModelSerializer):
    """
    Serializer for the Facility model.
    """

    class Meta:
        model = Facility
        fields = [
            "id",
            "name",
            "region",
            "zone",
            "woreda",
            "latitude",
            "longitude",
        ]


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the custom User model.
    """

    # This makes the 'facility' field in the JSON response show the
    # facility's primary key (its ID). We'll make it more descriptive later.
    facility = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), allow_null=True
    )

    class Meta:
        model = User
        # It's best practice to explicitly list fields and exclude sensitive
        # data like 'password'.
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "facility",
        ]
