from django.views.generic import TemplateView
from rest_framework import viewsets, permissions
from .models import Facility, User
from .serializers import FacilitySerializer, UserSerializer
from .permissions import IsAdminUser


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
class SignupPageView(TemplateView):
    template_name = "signup.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # This line is crucial for populating the dropdown
        context["facilities"] = Facility.objects.all().order_by("name")
        return context
