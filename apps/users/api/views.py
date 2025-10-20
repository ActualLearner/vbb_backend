from rest_framework import permissions, viewsets

from ..models import Facility, User
from ..permissions import IsAdminUser
from .serializers import FacilitySerializer, UserSerializer


class FacilityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows facilities to be viewed or edited.
    """

    queryset = Facility.objects.all().order_by("name")
    serializer_class = FacilitySerializer
    permission_classes = [permissions.IsAuthenticated]


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


# TODO: REMOVE THIS TEST VIEW LATER
# Legacy signup HTML view removed — signup is handled by API/auth endpoints.
