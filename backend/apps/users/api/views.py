from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from audit.services import record_audit
from core.permissions import PasswordChangeNotRequired

from ..models import Facility, User
from ..permissions import IsAdminOrReadOnly, IsAdminUser
from .serializers import (
    AdminUserCreateSerializer,
    ChangePasswordSerializer,
    EmailOrPhoneTokenSerializer,
    FacilitySerializer,
    ProfileSerializer,
    RoleAssignmentSerializer,
    UserSerializer,
)


class EmailOrPhoneTokenView(TokenObtainPairView):
    """Obtain a JWT pair using email or phone + password (SDS 2.3.3)."""

    serializer_class = EmailOrPhoneTokenSerializer


class FacilityViewSet(viewsets.ModelViewSet):
    """Facilities are viewable by all; writable only by administrators
    (SRS 3.2.2, SDS matrix manageFacility = ADMIN)."""

    queryset = Facility.objects.all().order_by("name")
    serializer_class = FacilitySerializer
    permission_classes = [IsAdminOrReadOnly, PasswordChangeNotRequired]


class UserViewSet(viewsets.ModelViewSet):
    """Administer user accounts (SRS UC-006). ADMIN only."""

    queryset = User.objects.all().order_by("-date_joined")
    permission_classes = [IsAdminUser, PasswordChangeNotRequired]

    def get_serializer_class(self):
        if self.action == "create":
            return AdminUserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Nested under a facility -> only that facility's staff.
        facility_pk = self.kwargs.get("facility_pk")
        if facility_pk:
            qs = qs.filter(facility_id=facility_pk)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        record_audit(
            request.user, "user.create", target=user, metadata={"role": user.role}
        )
        data = UserSerializer(user).data
        # Return the generated temp password once for the admin to relay.
        data["temporary_password"] = getattr(user, "_temporary_password", None)
        return Response(data, status=status.HTTP_201_CREATED)

    def _set_active(self, request, pk, active):
        user = self.get_object()
        if user == request.user:
            raise ValidationError("Administrators cannot change their own status.")
        user.is_active = active
        user.save(update_fields=["is_active"])
        record_audit(
            request.user,
            "user.reactivate" if active else "user.deactivate",
            target=user,
        )
        return Response(UserSerializer(user).data)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        return self._set_active(request, pk, active=False)

    @action(detail=True, methods=["post"])
    def reactivate(self, request, pk=None):
        return self._set_active(request, pk, active=True)

    @action(detail=True, methods=["post"], url_path="assign-role")
    def assign_role(self, request, pk=None):
        user = self.get_object()
        serializer = RoleAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.role = serializer.validated_data["role"]
        user.save(update_fields=["role"])
        record_audit(
            request.user, "user.assign_role", target=user, metadata={"role": user.role}
        )
        return Response(UserSerializer(user).data)


class MeView(APIView):
    """View or update the authenticated user's own profile (UM-011/012)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(ProfileSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    """Change the authenticated user's password (SRS VBB-FUN-UM-008)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])
        record_audit(user, "user.change_password", target=user)
        return Response({"detail": "Password updated."})
