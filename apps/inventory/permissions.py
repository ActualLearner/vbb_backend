from rest_framework import permissions


class IsRequestingFacilityUser(permissions.BasePermission):
    """
    Allows access only to users who belong to the requesting facility.
    """

    def has_object_permission(self, request, view, obj):
        # Allow read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the user from the requesting facility.
        return obj.requesting_facility == request.user.facility


class IsFulfillingFacilityUser(permissions.BasePermission):
    """
    Allows access only to users who belong to the fulfilling facility.
    """

    def has_object_permission(self, request, view, obj):
        # Allow read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the user from the fulfilling facility.
        return obj.fulfilling_facility == request.user.facility
