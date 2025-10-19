from django_filters import rest_framework as filters

from .models import BloodUnit, Facility


class BloodUnitFilter(filters.FilterSet):
    """
    FilterSet for the BloodUnit model.
    """

    # This creates a filter for the 'blood_type' field that uses the
    # choices defined in the BloodUnit model.
    blood_type = filters.ChoiceFilter(choices=BloodUnit.BloodType.choices)

    # This creates a filter for the 'facility' ForeignKey. It allows you
    # to filter by the facility's ID (e.g., ?facility=1).
    facility = filters.ModelChoiceFilter(
        queryset=Facility.objects.all(), field_name="facility", to_field_name="id"
    )

    class Meta:
        model = BloodUnit
        # The 'fields' list defines which fields we can filter on.
        fields = ["blood_type", "facility"]
