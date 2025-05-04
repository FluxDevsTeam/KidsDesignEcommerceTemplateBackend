from django.db.models import Sum, Case, When, F, DecimalField
from rest_framework import serializers
from .models import Cart, CartItem
from ..products.models import Product
from ..products.serializers import SimpleProductSizeSerializer


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ["id", "user", "first_name", "last_name", "email", "state", "city", "delivery_address", "phone_number", "estimated_delivery"]
        read_only_fields = ["id", "user"]


class PatchCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ["first_name", "last_name", "email", "state", "city", "delivery_address", "phone_number", "estimated_delivery"]


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


class CartProductViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "image1"]
        read_only_fields = ["id"]


class CartItemSerializerView(serializers.ModelSerializer):
    product = CartProductViewSerializer()
    cart = SimpleCartSerializerView()
    size = SimpleProductSizeSerializer()

    class Meta:
        model = CartItem
        fields = ["id", "product", "cart", "size", "quantity"]
        read_only_fields = ["id"]


class CartSerializerView(serializers.ModelSerializer):
    cart_items = CartItemSerializerView(many=True, read_only=True, source="cartitem_cart")
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user", "first_name", "last_name", "email", "state", "city", "delivery_address", "phone_number","estimated_delivery", "cart_items", "total"]
        read_only_fields = ["id", "user"]

    def get_total(self, obj):
        total = obj.cartitem_cart.aggregate(total=Sum(F("size__price") * F("quantity"), output_field=DecimalField(max_digits=10, decimal_places=2)))["total"] or 0
        return total
