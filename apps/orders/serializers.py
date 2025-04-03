from rest_framework.serializers import ModelSerializer
from .models import Order, OrderItem
from ..products.serializers import ProductSimpleViewSerializer


class OrderSerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "user", "first_name", "last_name", "email", "state", "city", "delivery_address", "phone_number"]
        read_only_fields = ["id", "user"]


class SimpleOrderSerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "user", ]
        read_only_fields = ["id", "user"]


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product", "order", "quantity", "name", "description", "colour", "image1", "price"]
        read_only_fields = ["id", "order"]


class OrderItemSerializerView(ModelSerializer):
    product = ProductSimpleViewSerializer()
    order = SimpleOrderSerializer()

    class Meta:
        model = OrderItem
        fields = ["id", "product", "order", "quantity", "name", "description", "colour", "image1", "price"]
        read_only_fields = ["id"]
