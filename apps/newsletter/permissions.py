from rest_framework import permissions


class IsAdminOrReadOnly(permissions.IsAdminUser):
    def has_permission(self, request, view):
        admin_permission = super().has_permission(request, view)
        return request.method in permissions.SAFE_METHODS or admin_permission