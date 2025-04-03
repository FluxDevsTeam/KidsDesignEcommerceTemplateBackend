from .serializers import OrderSerializer, OrderItemSerializer, OrderItemSerializerView
from .models import Order, OrderItem
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .pagination import CustomPagination
from .utils import swagger_helper


class ApiOrder(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    pagination = CustomPagination
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    @swagger_helper("Order", "order")
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_helper("Order", "order")
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)

    @swagger_helper("Order", "order")
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @swagger_helper("Order", "order")
    def partial_update(self, *args, **kwargs):
        return super().partial_update(*args, **kwargs)

    @swagger_helper("Order", "order")
    def destroy(self, *args, **kwargs):
        return super().destroy(*args, **kwargs)


class ApiOrderItem(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    pagination = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return OrderItemSerializerView
        return OrderItemSerializer

    def get_queryset(self):
        return OrderItem.objects.filter(order=self.request.kwargs["pk"])

    @swagger_helper("OrderItem", "order item")
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_helper("OrderItem", "order item")
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)

    @swagger_helper("OrderItem", "order item")
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @swagger_helper("OrderItem", "order item")
    def partial_update(self, *args, **kwargs):
        return super().partial_update(*args, **kwargs)

    @swagger_helper("OrderItem", "order item")
    def destroy(self, *args, **kwargs):
        return super().destroy(*args, **kwargs)
