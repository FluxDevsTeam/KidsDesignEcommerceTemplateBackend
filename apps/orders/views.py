from django.db.models import Sum, F, Count, Case, When, IntegerField, Q
from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from .serializers import OrderSerializer, OrderItemSerializerView, PatchOrderSerializer
from .models import Order, OrderItem
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import viewsets, status, filters
from .pagination import CustomPagination
from .utils import swagger_helper
from .permissions import IsAuthenticatedAndOrderItemOwner
from .filters import OrderFilter


class ApiOrder(viewsets.ModelViewSet):
    http_method_names = ["get", "head", "options"]
    pagination_class = CustomPagination
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ['order_date', 'total_amount']
    ordering = ['-order_date']
    filterset_fields = ["status"]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    @swagger_helper("Order", "order")
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_helper("Order", "order")
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    # temporary feature only for development. user cant edit or delete orders

    # @swagger_helper("Order", "order")
    # def create(self, *args, **kwargs):
    #     serializer = self.get_serializer(data=self.request.data)
    #     if serializer.is_valid():
    #         user = self.request.user
    #         serializer.save(user=user)
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # @swagger_helper("Order", "order")
    # def partial_update(self, *args, **kwargs):
    #     return super().partial_update(*args, **kwargs)
    #
    # @swagger_helper("Order", "order")
    # def destroy(self, *args, **kwargs):
    #     return super().destroy(*args, **kwargs)


class ApiAdminOrder(viewsets.ModelViewSet):
    http_method_names = ["get", "patch", "head", "options"]
    pagination_class = CustomPagination
    permission_classes = [IsAdminUser]
    filterset_class = OrderFilter
    ordering_fields = ['order_date', 'total_amount', 'delivery_date']
    ordering = ['-order_date']
    search_fields = ["id", "user"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return OrderSerializer
        return PatchOrderSerializer

    def get_queryset(self):
        return Order.objects.all()

    @swagger_helper("Order admin page", "order")
    def list(self, *args, **kwargs):
        # Get filtered queryset
        queryset = self.filter_queryset(self.get_queryset())

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_data = self.get_paginated_response(serializer.data).data
        else:
            serializer = self.get_serializer(queryset, many=True)
            paginated_data = {
                "count": queryset.count(),
                "next": None,
                "previous": None,
                "results": serializer.data
            }

        # Optimize status counts with a single query
        status_counts = queryset.aggregate(
            total_orders=Count('id'),
            delivered_orders=Count(Case(When(status="DELIVERED", then=1), output_field=IntegerField())),
            returned_orders=Count(Case(When(status="REFUNDED", then=1), output_field=IntegerField())),
            # Using REFUNDED instead of RETURNED
            pending_orders=Count(
                Case(When(~Q(status__in=["DELIVERED", "REFUNDED", "CANCELLED"]), then=1), output_field=IntegerField()))
        )

        # Compute payment aggregates
        delivered_orders = queryset.filter(status="DELIVERED")
        refunded_orders = queryset.filter(status="REFUNDED")

        aggregate_data = {
            "total_orders": status_counts["total_orders"],
            "delivered_orders": status_counts["delivered_orders"],
            "pending_orders": status_counts["pending_orders"],
            "returned_orders": status_counts["returned_orders"],
            "refunded_payment": refunded_orders.aggregate(total=Sum("total_amount"))["total"] or 0,
            "successful_payment": delivered_orders.aggregate(total=Sum("total_amount"))["total"] or 0,
            "total_payment": queryset.aggregate(total=Sum("total_amount"))["total"] or 0
        }

        # Structure response
        response_data = {
            "count": paginated_data["count"],
            "next": paginated_data["next"],
            "previous": paginated_data["previous"],
            "aggregate": aggregate_data,
            "results": paginated_data["results"]
        }

        return Response(response_data)

    @swagger_helper("Order admin page", "order")
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @swagger_helper("Order admin page", "order")
    def partial_update(self, *args, **kwargs):
        return super().partial_update(*args, **kwargs)

# temporary feature for only development
# class ApiOrderItem(viewsets.ModelViewSet):
#     http_method_names = ["get", "post", "patch", "delete", "head", "options"]
#     pagination_class = CustomPagination
#     permission_classes = [IsAuthenticatedAndOrderItemOwner]
#
#     def get_serializer_class(self):
#         if self.request.method == "GET":
#             return OrderItemSerializerView
#         return OrderItemSerializer
#
#     def get_queryset(self):
#         return OrderItem.objects.filter(order=self.kwargs.get("order_pk"), order__user=self.request.user)
#
#     @swagger_helper("OrderItem", "order item")
#     def list(self, *args, **kwargs):
#         return super().list(*args, **kwargs)
#
#     @swagger_helper("OrderItem", "order item")
#     def create(self, *args, **kwargs):
#         serializer = self.get_serializer(data=self.request.data)
#
#         if serializer.is_valid():
#             order_id = self.kwargs.get("order_pk")
#             order = get_object_or_404(Order, id=order_id)
#             size = self.request.data.get("size")
#             if not size:
#                 return Response({"error": "Size is required."}, status=status.HTTP_400_BAD_REQUEST)
#
#             serializer.save(order=order, size=size)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     @swagger_helper("OrderItem", "order item")
#     def retrieve(self, *args, **kwargs):
#         return super().retrieve(*args, **kwargs)
#
#     @swagger_helper("OrderItem", "order item")
#     def partial_update(self, *args, **kwargs):
#         return super().partial_update(*args, **kwargs)
#
#     @swagger_helper("OrderItem", "order item")
#     def destroy(self, *args, **kwargs):
#         return super().destroy(*args, **kwargs)
