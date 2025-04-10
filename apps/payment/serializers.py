from rest_framework import serializers
from ..cart.models import Cart, CartItem
from django.conf import settings
from decimal import Decimal


def calculate_delivery_fee(cart):
    subtotal = sum(item.product.price * item.quantity for item in cart.cartitem_cart.all())
    return Decimal("15.00") if subtotal > 0 else Decimal("0.00")


class PaymentCartItemSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(source="product.price", max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ["quantity", "price"]


class PaymentCartSerializer(serializers.ModelSerializer):
    cart_items = PaymentCartItemSerializer(many=True, read_only=True, source="cartitem_cart")
    subtotal = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    provider = serializers.ChoiceField(
        choices=[("flutterwave", "Flutterwave"), ("paystack", "Paystack")],
        default="flutterwave",
        write_only=True
    )
    redirect_url = serializers.URLField(write_only=True, default=settings.PAYMENT_SUCCESS_URL)

    class Meta:
        model = Cart
        fields = ["delivery_fee", "cart_items", "subtotal", "total", "provider", "redirect_url"]

    def get_subtotal(self, obj):
        return sum(item.product.price * item.quantity for item in obj.cartitem_cart.all())

    def get_total(self, obj):
        subtotal = self.get_subtotal(obj)
        delivery_fee = obj.delivery_fee if obj.delivery_fee is not None else calculate_delivery_fee(obj)
        return subtotal + delivery_fee
