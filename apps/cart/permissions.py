from rest_framework.permissions import BasePermission
from .models import Cart


class IsAuthenticatedOrCartItemOwner(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return Cart.objects.filter(id=view.kwargs.get("cart_pk"), user=request.user).exists()
