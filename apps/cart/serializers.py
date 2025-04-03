from rest_framework import serializers
from .models import Cart, CartItem
from ..products.serializers import ProductSimpleViewSerializer


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ["id", "user", "first_name", "last_name", "email", "state", "city", "delivery_address", "phone_number"]
        read_only_fields = ["id", "user"]


class SimpleCartSerializerView(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ["id", "user",]
        read_only_fields = ["id"]


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["id", "product", "cart", "quantity"]
        read_only_fields = ["id"]


class CartItemSerializerView(serializers.ModelSerializer):
    product = ProductSimpleViewSerializer()
    cart = SimpleCartSerializerView()

    class Meta:
        model = CartItem
        fields = ["id", "product", "cart", "quantity"]
        read_only_fields = ["id"]
