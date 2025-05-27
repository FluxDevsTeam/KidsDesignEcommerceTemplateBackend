from rest_framework import serializers
from ..cart.models import Cart, CartItem


class PaymentCartSerializer(serializers.ModelSerializer):
    subtotal = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    provider = serializers.ChoiceField(choices=[("flutterwave", "Flutterwave"), ("paystack", "Paystack")], default="flutterwave", write_only=True)
    include_delivery_fee = serializers.BooleanField(required=False)

    class Meta:
        model = Cart
        fields = ["delivery_fee", "subtotal", "total", "provider", "include_delivery_fee"]

    def get_subtotal(self, obj):
        return sum(item.size.price * item.quantity for item in obj.cartitem_cart.all())

    def get_total(self, obj):
        subtotal = self.get_subtotal(obj)
        delivery_fee = obj.delivery_fee if obj.delivery_fee is not None else 0
        if obj.include_delivery_fee:
            return subtotal + delivery_fee
        return subtotal


class InitiateSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=[("flutterwave", "Flutterwave"), ("paystack", "Paystack")], default="flutterwave", write_only=True)
