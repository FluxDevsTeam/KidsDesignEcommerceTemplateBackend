from django.db import transaction
from rest_framework.response import Response
from django.core.cache import cache
from .serializers import OrderSerializer, UserPatchOrderSerializer
from .models import Order
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from .pagination import CustomPagination
from .utils import swagger_helper, initiate_refund
from datetime import timedelta
from ..products.models import ProductSize
from django.utils import timezone


class ApiOrder(viewsets.ModelViewSet):
    http_method_names = ["get", "patch", "head", "options"]
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]
    ordering_fields = ['order_date', 'total_amount']
    ordering = ['-order_date', '-created_at']
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
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

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

            else:
                return Response({"error": "Refund processing failed. Admin has been notified."}, status=503)

        else:
            serializer.save()
        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data)
