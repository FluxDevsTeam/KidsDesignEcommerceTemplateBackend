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


class ProductSimpleViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ["id", "name", "image1", "discounted_price", "price"]
        read_only_fields = ["id"]


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
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user", "first_name", "last_name", "email", "state", "city", "delivery_address", "phone_number",
                  "estimated_delivery", "cart_items", "total"]
        read_only_fields = ["id", "user"]

    def get_total(self, obj):
        total = obj.cartitem_cart.aggregate(total=Sum(Case(When(product__discounted_price__isnull=False, product__discounted_price__lt=F("product__price"), then=F("product__discounted_price") * F("quantity")),default=F("product__price") * F("quantity"), output_field=DecimalField(max_digits=10, decimal_places=2))))["total"] or 0
        return total
