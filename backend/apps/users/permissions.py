from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminUser(BasePermission):
    """Allows access only to Facility Administrators (role ADMIN)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsProfessional(BasePermission):
    """Allows access only to Healthcare Professionals (role PROFESSIONAL)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "PROFESSIONAL"
        )


class IsAdminOrReadOnly(BasePermission):
    """Full access to ADMIN users, read-only access to everyone else."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )
