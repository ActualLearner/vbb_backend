from rest_framework.permissions import BasePermission

# Paths a user with a pending forced password change may still reach.
_ALLOWED_WHILE_LOCKED = (
    "/api/v1/auth/change-password/",
    "/api/v1/auth/me/",
    "/api/v1/auth/login/",
    "/api/v1/auth/refresh/",
)


class PasswordChangeNotRequired(BasePermission):
    """Block API access until a forced temporary-password change is done.

    Enforces SRS VBB-FUN-UM-002 server-side: a freshly provisioned user must
    rotate their temporary password before using other endpoints.
    """

    message = "You must change your temporary password before continuing."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return True  # let authentication handle anonymous access
        if not getattr(user, "must_change_password", False):
            return True
        return request.path in _ALLOWED_WHILE_LOCKED
