from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from .models import Cart, CartItem
from .permissions import IsAuthenticatedOrCartOwner, IsAuthenticatedOrCartItemOwner
from .serializers import CartSerializer, CartItemSerializer, CartItemSerializerView
from rest_framework import viewsets
from .pagination import CustomPagination
from .utils import swagger_helper


class ApiCart(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    pagination = CustomPagination
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticatedOrCartOwner]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    @swagger_helper("Cart", "cart")
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_helper("Cart", "cart")
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)

    @swagger_helper("Cart", "cart")
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @swagger_helper("Cart", "cart")
    def partial_update(self, *args, **kwargs):
        return super().partial_update(*args, **kwargs)

    @swagger_helper("Cart", "cart")
    def destroy(self, *args, **kwargs):
        return super().destroy(*args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

    def perform_update(self, serializer):
        user = self.request.user
        serializer.save(user=user)


class ApiCartItem(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    pagination = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CartItemSerializerView
        return CartItemSerializer

    def get_queryset(self):
        return CartItem.objects.filter(cart=self.kwargs.get("cart_pk"), cart__user=self.request.user)

    @swagger_helper("CartItem", "cart item")
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_helper("CartItem", "cart item")
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)

    @swagger_helper("CartItem", "cart item")
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @swagger_helper("CartItem", "cart item")
    def partial_update(self, *args, **kwargs):
        return super().partial_update(*args, **kwargs)

    @swagger_helper("CartItem", "cart item")
    def destroy(self, *args, **kwargs):
        return super().destroy(*args, **kwargs)

    def perform_create(self, serializer):
        cart = get_object_or_404(Cart, id=self.kwargs.get("cart_pk"))
        serializer.save(cart=cart)

    def perform_update(self, serializer):
        cart_id = self.kwargs.get("cart_pk")
        cart = get_object_or_404(Cart, id=cart_id)
        serializer.save(cart=cart)
