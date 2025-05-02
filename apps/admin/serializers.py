from rest_framework import serializers
from .models import Order, OrderItem
from ..products.serializers import ProductSimpleViewSerializer


class PatchOrderSerializer(serializers.ModelSerializer):
    delivery_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=[('PAID', 'Paid'), ('SHIPPED', 'Shipped'), ('DELIVERED', 'Delivered'), ('CANCELLED', 'Cancelled')], write_only=True)

    class Meta:
        model = Order
        fields = ["status", "delivery_date"]