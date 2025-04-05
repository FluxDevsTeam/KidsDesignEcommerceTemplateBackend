from rest_framework.permissions import BasePermission
from .models import Order


class IsAuthenticatedAndOrderItemOwner(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return Order.objects.filter(id=view.kwargs.get("order_pk"), user=request.user).exists()
