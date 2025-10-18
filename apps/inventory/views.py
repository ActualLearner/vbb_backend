from rest_framework import viewsets, permissions
from .models import BloodUnit, BloodRequest
from .serializers import BloodUnitSerializer, BloodRequestSerializer


class BloodUnitViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing blood units.
    Supports filtering by `facility` ID and `blood_type`.
    Example: /api/v1/blood-units/?facility=1&blood_type=A-
    """

    serializer_class = BloodUnitSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = BloodUnit.objects.all().order_by("-donated_at")
        facility = self.request.query_params.get("facility")
        blood_type = self.request.query_params.get("blood_type")

        if facility:
            queryset = queryset.filter(facility__id=facility)
        if blood_type:
            queryset = queryset.filter(blood_type=blood_type)

        return queryset


class BloodRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and managing blood requests.
    """

    queryset = BloodRequest.objects.all().order_by("-created_at")
    serializer_class = BloodRequestSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically set the 'requested_by' field to the current user.
        serializer.save(requested_by=self.request.user)
