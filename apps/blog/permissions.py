from rest_framework import permissions


class IsAdminOrAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to edit it.
    Read permissions are allowed to any request.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner or admin
        return obj.author == request.user or request.user.is_staff


class IsAdminOrReadOnly(permissions.IsAdminUser):
    def has_permission(self, request, view):
        admin_permission = super().has_permission(request, view)
        return request.method in permissions.SAFE_METHODS or admin_permission