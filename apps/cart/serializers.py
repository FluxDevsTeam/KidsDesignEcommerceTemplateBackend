from rest_framework import serializers
from .models import Cart, CartItem
from ..products.serializers import ProductSimpleViewSerializer, SimpleProductSizeSerializer


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ["id", "user", "first_name", "last_name", "email", "state", "city", "delivery_address", "phone_number", "estimated_delivery"]
        read_only_fields = ["id", "user"]


class SimpleCartSerializerView(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ["id", "user",]
        read_only_fields = ["id"]


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["id", "product", "cart", "size", "quantity"]
        read_only_fields = ["id", "cart"]


class CartItemSerializerView(serializers.ModelSerializer):
    product = ProductSimpleViewSerializer()
    cart = SimpleCartSerializerView()
    size = SimpleProductSizeSerializer()

    class Meta:
        model = CartItem
        fields = ["id", "product", "cart", "size", "quantity"]
        read_only_fields = ["id"]


class CartSerializerView(serializers.ModelSerializer):
    cart_items = CartItemSerializerView(many=True, read_only=True, source="cartitem_cart")

    class Meta:
        model = Cart
        fields = ["id", "user", "first_name", "last_name", "email", "state", "city", "delivery_address", "phone_number",
                  "estimated_delivery", "cart_items"]
        read_only_fields = ["id", "user"]
