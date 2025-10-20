from rest_framework import permissions

from .domain.authorizers import BloodRequestAuthorizer

authorizer = BloodRequestAuthorizer()


class IsRequestingFacilityUser(permissions.BasePermission):
    """
    Allows access only to users who belong to the requesting facility.
    """

    def has_object_permission(self, request, view, obj):
        # Allow read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the user from the requesting facility.
        return authorizer.can_receive_request(request.user, obj)


class IsFulfillingFacilityUser(permissions.BasePermission):
    """
    Allows access only to users who belong to the fulfilling facility.
    """

    def has_object_permission(self, request, view, obj):
        # Allow read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the user from the fulfilling facility.
        return authorizer.can_accept_request(request.user, obj)
