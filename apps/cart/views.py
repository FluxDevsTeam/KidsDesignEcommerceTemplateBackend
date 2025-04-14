import json
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.cache import cache
from .models import Cart, CartItem
from .permissions import IsAuthenticatedOrCartItemOwner
from .serializers import CartSerializer, CartItemSerializer, CartItemSerializerView, CartSerializerView, PatchCartSerializer
from rest_framework import viewsets, status
from .pagination import CustomPagination
from .utils import swagger_helper
from ..products.models import Product, ProductSize


class ApiCart(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CartSerializerView
        if self.request.method == "PATCH":
            return PatchCartSerializer
        return CartSerializer

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    @swagger_helper("Cart", "cart")
    def list(self, request, *args, **kwargs):
        cache_timeout = 300
        cache_params = dict(request.query_params)
        cache_key = f"cart_list:{request.user.id}:{json.dumps(cache_params, sort_keys=True)}"
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper("Cart", "cart")
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        cache.delete_pattern(f"cart_list:{request.user.id}:*")
        return response

    @swagger_helper("Cart", "cart")
    def retrieve(self, request, *args, **kwargs):
        cache_timeout = 300
        cache_key = f"cart_detail:{request.user.id}:{kwargs['pk']}"
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper("Cart", "cart")
    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        cache.delete_pattern(f"cart_list:{request.user.id}:*")
        cache.delete_pattern(f"cart_detail:{request.user.id}:{kwargs['pk']}")
        return response

    @swagger_helper("Cart", "cart")
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        cache.delete_pattern(f"cart_list:{request.user.id}:*")
        cache.delete_pattern(f"cart_detail:{request.user.id}:{kwargs['pk']}")
        return response

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

    def perform_update(self, serializer):
        user = self.request.user
        serializer.save(user=user)


class ApiCartItem(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticatedOrCartItemOwner]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CartItemSerializerView
        return CartItemSerializer

    def get_queryset(self):
        return CartItem.objects.filter(cart=self.kwargs.get("cart_pk"), cart__user=self.request.user)

    @swagger_helper("CartItem", "cart item")
    def list(self, request, *args, **kwargs):
        cache_timeout = 300
        cache_params = dict(request.query_params)
        cache_key = f"cart_item_list:{request.user.id}:{self.kwargs.get('cart_pk')}:{json.dumps(cache_params, sort_keys=True)}"
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper("CartItem", "cart item")
    def create(self, request, *args, **kwargs):
        product_id = request.data.get("product")
        size_id = request.data.get("size")
        quantity = int(request.data.get("quantity"))
        cart_id = self.kwargs.get("cart_pk")
        cart = get_object_or_404(Cart, id=cart_id)
        size = get_object_or_404(ProductSize, id=size_id)
        product = get_object_or_404(Product, id=product_id)

        if product != size.product:
            return Response({"error": "Selected size does not belong to the chosen product."}, status=status.HTTP_400_BAD_REQUEST)

        if CartItem.objects.filter(product=product, size=size, cart=cart).exists():
            return Response({"error": "This item is already in your cart."}, status=status.HTTP_400_BAD_REQUEST)

        database_quantity = size.quantity
        if database_quantity < 1:
            return Response({"error": "The selected size is out of stock."}, status=status.HTTP_400_BAD_REQUEST)

        if quantity > database_quantity > 0:
            quantity = database_quantity

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(quantity=quantity, cart=cart)
            cache.delete_pattern(f"cart_item_list:{request.user.id}:*")
            cache.delete_pattern(f"cart_list:{request.user.id}:*")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_helper("CartItem", "cart item")
    def retrieve(self, request, *args, **kwargs):
        cache_timeout = 300
        cache_key = f"cart_item_detail:{request.user.id}:{kwargs['pk']}"
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper("CartItem", "cart item")
    def partial_update(self, request, *args, **kwargs):
        size_id = request.data.get("size")
        quantity = request.data.get("quantity")
        cart_item = self.get_object()
        original_size = cart_item.size
        original_quantity = cart_item.quantity

        if quantity is not None:
            try:
                quantity = int(quantity)
            except ValueError:
                return Response({"error": "Quantity must be a valid number."}, status=status.HTTP_400_BAD_REQUEST)

        size = get_object_or_404(ProductSize, id=size_id) if size_id else original_size

        response_messages = []
        updated = False

        if size != original_size:
            if size.quantity <= 0:
                return Response({"error": "The selected size is out of stock."}, status=status.HTTP_400_BAD_REQUEST)

            if quantity is None:
                quantity = original_quantity

            if quantity > size.quantity:
                cart_item.quantity = size.quantity
                response_messages.append(f"Requested quantity exceeds stock for selected size. Quantity adjusted to {size.quantity}.")
            else:
                cart_item.quantity = quantity

            cart_item.size = size
            response_messages.append(f"Size updated to {size.size}.")

        if quantity and quantity != cart_item.quantity:
            if cart_item.quantity <= 0:
                return Response({"error": "The selected size is out of stock."}, status=status.HTTP_400_BAD_REQUEST)
            if quantity > size.quantity:
                cart_item.quantity = size.quantity
                response_messages.append(f"Not enough stock. Requested {quantity}, but only {size.quantity} left. Quantity updated to {size.quantity}.")
            else:
                cart_item.quantity = quantity
                response_messages.append(f"Quantity updated successfully to {quantity}.")

        if response_messages:
            cart_item.save()
            cache.delete_pattern(f"cart_item_list:{request.user.id}:*")
            cache.delete_pattern(f"cart_item_detail:{request.user.id}:{kwargs['pk']}")
            cache.delete_pattern(f"cart_list:{request.user.id}:*")
            return Response({"message": " ".join(response_messages)}, status=status.HTTP_200_OK)

        return Response({"message": "No changes made."}, status=status.HTTP_200_OK)

    @swagger_helper("CartItem", "cart item")
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(*args, **kwargs)
        cache.delete_pattern(f"cart_item_list:{request.user.id}:*")
        cache.delete_pattern(f"cart_item_detail:{request.user.id}:{kwargs['pk']}")
        cache.delete_pattern(f"cart_list:{request.user.id}:*")
        return response
