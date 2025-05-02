from rest_framework import serializers
from ..orders.models import Order


class PatchOrderSerializer(serializers.ModelSerializer):
    delivery_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=[('PAID', 'Paid'), ('SHIPPED', 'Shipped'), ('DELIVERED', 'Delivered'), ('CANCELLED', 'Cancelled')], write_only=True)

    class Meta:
        model = Order
        fields = ["status", "delivery_date"]