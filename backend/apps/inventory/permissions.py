from rest_framework import permissions

from .domain.authorizers import BloodRequestAuthorizer

authorizer = BloodRequestAuthorizer()


class IsRequestingFacilityUser(permissions.BasePermission):
    """
    Allows access only to clinicians who belong to the requesting facility.
    """

    def has_object_permission(self, request, view, obj):
        # Allow read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        action = getattr(view, "action", None)
        if action == "cancel":
            return authorizer.can_cancel_request(request.user, obj)
        return authorizer.can_receive_request(request.user, obj)


class IsFulfillingFacilityUser(permissions.BasePermission):
    """
    Allows access only to supply staff who belong to the fulfilling facility.
    """

    def has_object_permission(self, request, view, obj):
        # Allow read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        action = getattr(view, "action", None)
        if action == "reject":
            return authorizer.can_reject_request(request.user, obj)
        if action == "ship":
            return authorizer.can_ship_request(request.user, obj)
        return authorizer.can_accept_request(request.user, obj)
