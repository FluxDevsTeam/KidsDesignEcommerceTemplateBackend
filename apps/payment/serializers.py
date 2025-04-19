from rest_framework import serializers
from ..cart.models import Cart, CartItem


class PaymentCartItemSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(source="product.price", max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ["quantity", "price"]


class PaymentCartSerializer(serializers.ModelSerializer):
    cart_items = PaymentCartItemSerializer(many=True, read_only=True, source="cartitem_cart")
    subtotal = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    provider = serializers.ChoiceField(choices=[("flutterwave", "Flutterwave"), ("paystack", "Paystack")], default="flutterwave", write_only=True)

    class Meta:
        model = Cart
        fields = ["delivery_fee", "cart_items", "subtotal", "total", "provider"]

    def get_subtotal(self, obj):
        return sum(item.product.price * item.quantity for item in obj.cartitem_cart.all())

    def get_total(self, obj):
        subtotal = self.get_subtotal(obj)
        delivery_fee = obj.delivery_fee if obj.delivery_fee is not None else 0
        return subtotal + delivery_fee


class InitiateSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=[("flutterwave", "Flutterwave"), ("paystack", "Paystack")], default="flutterwave", write_only=True)
