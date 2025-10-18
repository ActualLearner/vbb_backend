from rest_framework import viewsets, permissions
from .models import Facility, User
from .serializers import FacilitySerializer, UserSerializer


class FacilityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows facilities to be viewed or edited.
    """

    queryset = Facility.objects.all().order_by("name")
    serializer_class = FacilitySerializer
    # For now, we allow anyone to access. We will add permissions later.
    # permission_classes = [permissions.IsAuthenticated]


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    # permission_classes = [permissions.IsAuthenticated]
