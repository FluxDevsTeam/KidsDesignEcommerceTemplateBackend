from rest_framework.serializers import ModelSerializer
from .models import Order, OrderItem
from ..products.serializers import ProductSimpleViewSerializer


class OrderItemSerializerView(ModelSerializer):
    product = ProductSimpleViewSerializer()

    class Meta:
        model = OrderItem
        fields = ["id", "product", "order", "quantity", "name", "size", "description", "colour", "image1", "price"]
        read_only_fields = ["id"]


class OrderSerializer(ModelSerializer):
    order_items = OrderItemSerializerView(many=True, read_only=True, source='orderitem_order')

    class Meta:
        model = Order
        fields = ["id", "user", "order_date", "status", "delivery_fee", "first_name", "last_name", "email", "state", "city", "delivery_address", "phone_number", "delivery_date", "estimated_delivery", "order_items"]
        read_only_fields = ["id", "user", "order_date"]

# temporary feature for only development

# class OrderItemSerializer(ModelSerializer):
#     class Meta:
#         model = OrderItem
#         fields = ["id", "product", "order", "quantity", "name", "size", "description", "colour", "image1", "price"]
#         read_only_fields = ["id", "order"]



