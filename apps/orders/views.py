from django.db import transaction
from django.db.models import Sum, F, Count, Case, When, IntegerField, Q
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from django.core.cache import cache
from .serializers import OrderSerializer, OrderItemSerializerView, PatchOrderSerializer, UserPatchOrderSerializer
from .models import Order, OrderItem
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework import viewsets, status, filters
from .pagination import CustomPagination
from .utils import swagger_helper, initiate_refund
from .filters import OrderFilter
from datetime import datetime, timedelta
from django.utils import timezone
from .tasks import is_celery_healthy, refund_confirmation_email
from ..products.models import ProductSize


class ApiOrder(viewsets.ModelViewSet):
    http_method_names = ["get", "patch", "head", "options"]
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]
    ordering_fields = ['order_date', 'total_amount']
    ordering = ['-order_date']
    filterset_fields = ["status"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return OrderSerializer
        return UserPatchOrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    @swagger_helper("Order", "order")
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_helper("Order", "order")
    def partial_update(self, *args, **kwargs):
        order = self.get_object()
        serializer = self.get_serializer(order, data=self.request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get('status') == 'CANCELLED' and order.status != 'REFUNDED':
            time_limit = order.created_at + timedelta(hours=6)
            if timezone.now() > time_limit:
                return Response({"error": "Cancellations are only allowed within 6 hours of purchase."}, status=403)

            if not order.transaction_id or not order.payment_provider:
                return Response({"error": "Refund cannot be processed. Contact support."}, status=400)

            refund_success = initiate_refund(order)

            if refund_success:
                order.status = 'REFUNDED'
                order.save()

                # returning items to store
                with transaction.atomic():
                    order_items = order.orderitem_order.select_related('product').all()
                    product_ids = set()

                    for item in order_items:
                        product_size = ProductSize.objects.filter(
                            product=item.product,
                            size=item.size
                        ).select_for_update().first()

                        if product_size:
                            product_size.quantity += item.quantity
                            product_size.save()
                            product_ids.add(product_size.product.id)
                        else:
                            return Response({"error": "Product size not found."}, status=status.HTTP_400_BAD_REQUEST)

                    cache.delete_pattern("product_list:*")
                    for product_id in product_ids:
                        cache.delete_pattern(f"product_detail:{product_id}")
                    cache.delete_pattern("product_suggestions:*")
                    cache.delete_pattern("search:*")
                    cache.delete_pattern("search_suggestions:*")

                try:
                    if not is_celery_healthy():
                        refund_confirmation_email(
                            order_id=str(order.id),
                            user_email=order.email,
                            first_name=order.first_name,
                            total_amount=str(order.total_amount),
                            refund_date=datetime.now().date()
                        )
                    else:
                        from .tasks import refund_confirmation_email as refund_task
                        refund_task.apply_async(
                            kwargs={
                                'order_id': str(order.id),
                                'user_email': order.email,
                                'first_name': order.first_name,
                                'total_amount': str(order.total_amount),
                                'refund_date': datetime.now().date()
                            }
                        )
                except Exception:
                    pass
            else:
                return Response({"error": "Refund processing failed. Admin has been notified."}, status=503)

            response_serializer = OrderSerializer(order)
            return Response(response_serializer.data)

        serializer.save()
        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data)

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

    #
    # @swagger_helper("Order", "order")
    # def destroy(self, *args, **kwargs):
    #     return super().destroy(*args, **kwargs)


class ApiAdminOrder(viewsets.ModelViewSet):
    http_method_names = ["get", "patch", "head", "options"]
    pagination_class = CustomPagination
    # permission_classes = [IsAdminUser]
    permission_classes = [AllowAny]
    filterset_class = OrderFilter
    ordering_fields = ['order_date', 'total_amount', 'delivery_date']
    ordering = ['-order_date']
    search_fields = ["id", "status", "payment_provider"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return OrderSerializer
        return PatchOrderSerializer

    def get_queryset(self):
        return Order.objects.all()

    @swagger_helper("Order admin page", "order")
    def list(self, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

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

        status_counts = queryset.aggregate(
            total_orders=Count('id'),
            delivered_orders=Count(Case(When(status="DELIVERED", then=1), output_field=IntegerField())),
            returned_orders=Count(Case(When(status="REFUNDED", then=1), output_field=IntegerField())),
            pending_orders=Count(
                Case(When(~Q(status__in=["DELIVERED", "REFUNDED", "CANCELLED"]), then=1), output_field=IntegerField()))
        )

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
        order = self.get_object()
        serializer = self.get_serializer(order, data=self.request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get('status') == 'CANCELLED' and order.status != 'REFUNDED':
            if not order.transaction_id or not order.payment_provider:
                return Response({"error": "Refund cannot be processed. Contact support."}, status=400)
            refund_success = initiate_refund(order, is_admin=True)
            if refund_success:
                order.status = 'REFUNDED'
                order.save()

                with transaction.atomic():
                    order_items = order.orderitem_order.select_related('product').all()
                    product_ids = set()

                    for item in order_items:
                        product_size = ProductSize.objects.filter(
                            product=item.product,
                            size=item.size
                        ).select_for_update().first()

                        if product_size:
                            product_size.quantity += item.quantity
                            product_size.save()
                            product_ids.add(product_size.product.id)
                        else:
                            return Response({"error": "Product size not found."}, status=status.HTTP_400_BAD_REQUEST)

                    cache.delete_pattern("product_list:*")
                    for product_id in product_ids:
                        cache.delete_pattern(f"product_detail:{product_id}")
                    cache.delete_pattern("product_suggestions:*")
                    cache.delete_pattern("search:*")
                    cache.delete_pattern("search_suggestions:*")

                if not is_celery_healthy():
                    refund_confirmation_email(
                        order_id=str(order.id),
                        user_email=order.email,
                        first_name=order.first_name,
                        total_amount=str(order.total_amount),
                        refund_date=datetime.now().date()
                    )
                else:
                    from .tasks import refund_confirmation_email as refund_task
                    refund_task.apply_async(
                        kwargs={
                            'order_id': str(order.id),
                            'user_email': order.email,
                            'first_name': order.first_name,
                            'total_amount': str(order.total_amount),
                            'refund_date': datetime.now().date()
                        }
                    )

            else:
                return Response({"error": "Refund processing failed."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        elif serializer.validated_data.get('status') == 'DELIVERED':
            order.status = 'DELIVERED'
            order.delivery_date = timezone.now().date()
            order.save()
        else:
            serializer.save()
        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data)

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
