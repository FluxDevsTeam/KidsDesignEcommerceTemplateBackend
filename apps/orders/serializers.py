from rest_framework import serializers
from .models import Order, OrderItem
from ..products.serializers import ProductSimpleViewSerializer


class OrderItemSerializerView(serializers.ModelSerializer):
    product = ProductSimpleViewSerializer()

    class Meta:
        model = OrderItem
        fields = ["id", "product", "order", "quantity", "name", "size", "description", "colour", "image1", "price"]
        read_only_fields = ["id"]


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializerView(many=True, read_only=True, source='orderitem_order')

    class Meta:
        model = Order
        fields = ["id", "payment_provider", "transaction_id", "user", "order_date", "created_at", "status", "delivery_fee", "total_amount", "first_name", "last_name", "email", "state", "city", "delivery_address", "phone_number", "delivery_date", "estimated_delivery", "order_items"]
        read_only_fields = ["id", "user", "order_date"]


class PatchOrderSerializer(serializers.ModelSerializer):
    delivery_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=[('PAID', 'Paid'), ('SHIPPED', 'Shipped'), ('DELIVERED', 'Delivered'), ('CANCELLED', 'Cancelled')], write_only=True)

    class Meta:
        model = Order
        fields = ["status", "delivery_date"]


class UserPatchOrderSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=[('CANCELLED', 'Cancelled')], write_only=True)

    class Meta:
        model = Order
        fields = ['status']

# temporary feature for only development

# class OrderItemSerializer(ModelSerializer):
#     class Meta:
#         model = OrderItem
#         fields = ["id", "product", "order", "quantity", "name", "size", "description", "colour", "image1", "price"]
#         read_only_fields = ["id", "order"]



