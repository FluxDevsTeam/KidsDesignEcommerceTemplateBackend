from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthenticatedOrIsUser(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            return obj.cart__user == request.user
