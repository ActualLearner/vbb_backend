from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminUser(BasePermission):
    """Allows access only to Facility Administrators (role ADMIN)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsSupply(BasePermission):
    """Allows access only to Supply / Inventory staff (role SUPPLY)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "SUPPLY"
        )


class IsClinician(BasePermission):
    """Allows access only to Clinicians (role CLINICIAN)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "CLINICIAN"
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
