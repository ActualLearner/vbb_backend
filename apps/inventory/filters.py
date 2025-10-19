from django_filters import rest_framework as filters
from users.models import Facility
from .models import BloodUnit, BloodRequest


class BloodUnitFilter(filters.FilterSet):
    """
    Simplified FilterSet for the BloodUnit model for use with the
    nested /facilities/{id}/inventory/ endpoint.
    """

    # The blood_type filter is still very useful.
    blood_type = filters.ChoiceFilter(choices=BloodUnit.BloodType.choices)

    class Meta:
        model = BloodUnit
        # The 'facility' field is removed because the URL handles facility filtering.
        fields = ["blood_type"]


class BloodRequestFilter(filters.FilterSet):
    """
    FilterSet for the BloodRequest model.
    """

    # Allows filtering by multiple statuses, e.g., ?status=PENDING&status=ACCEPTED
    status = filters.MultipleChoiceFilter(choices=BloodRequest.RequestStatus.choices)

    # A custom filter field to easily get 'incoming' or 'outgoing' requests
    # based on the logged-in user's facility.
    type = filters.CharFilter(method="filter_by_type")

    class Meta:
        model = BloodRequest
        fields = ["status", "blood_type"]

    def filter_by_type(self, queryset, name, value):
        """
        Custom filter method to filter requests by 'incoming' or 'outgoing'
        relative to the user's facility.
        """
        user = self.request.user
        if not user.facility:
            return queryset.none()

        if value.lower() == "incoming":
            return queryset.filter(fulfilling_facility=user.facility)
        elif value.lower() == "outgoing":
            return queryset.filter(requesting_facility=user.facility)

        return queryset
