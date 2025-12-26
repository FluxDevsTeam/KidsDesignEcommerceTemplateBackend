from rest_framework import permissions


class IsAdminOrOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to access/modify it.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user for their own objects
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user or request.user.is_staff

        # Write permissions are only allowed to the owner or admin
        return obj.user == request.user or request.user.is_staff


class IsAdminOrReadOnly(permissions.IsAdminUser):
    def has_permission(self, request, view):
        admin_permission = super().has_permission(request, view)
        return request.method in permissions.SAFE_METHODS or admin_permission