from django.db import transaction
from django.db.models import Sum, F, Count, Case, When, IntegerField, Q
from django.core.cache import cache
from .serializers import PatchOrderSerializer
from ..orders.serializers import OrderSerializer
from ..orders.models import Order
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework import viewsets, status
from .pagination import CustomPagination
from .utils import swagger_helper, initiate_refund, notify_user_for_shipped_order, notify_user_for_delivered_order
from .filters import OrderFilter
from ..products.models import ProductSize
from django.utils import timezone
from pytz import timezone as pytz_timezone
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from apps.products.models import Product
from django.db.models.functions import TruncMonth
from rest_framework import viewsets
from datetime import date, timedelta

User = get_user_model()


class OrderDashboard(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(operation_id="Admin dashboard page", operation_description="monthly operational data", tags=["Admin"])
    def retrieve(self, *args, **kwargs):
        year = date.today().year
        query = self.get_queryset()
        total_sales_this_year = query.filter(delivery_date__year__gte=year).count()
        total_payments_this_year = query.filter(delivery_date__year__gte=year).aggregate(total=Sum("total_amount"))["total"] or 0.00
        total_products = Product.objects.filter(is_available=True).count()
        total_users = User.objects.filter(is_verified=True).count()

        today = date.today()
        start_year = year - 1 if today.month < 12 else year
        start_month = today.month + 1 if today.month < 12 else 1
        start_date = date(start_year, start_month, 1)
        next_month = today.month % 12 + 1
        next_year = today.year + (today.month // 12)
        end_date = date(next_year, next_month, 1) - timedelta(days=1)

        monthly_query = query.filter(delivery_date__range=(start_date, end_date)).annotate(
            month=TruncMonth('delivery_date')
        ).values('month').annotate(
            total_payments=Sum('total_amount')
        ).order_by('month')

        monthly_data = []
        current_date = start_date
        while current_date <= end_date:
            monthly_data.append({
                'month': current_date.strftime('%b %Y'),
                'total': 0.0
            })
            next_month = current_date.month % 12 + 1
            next_year = current_date.year + (current_date.month // 12)
            current_date = date(next_year, next_month, 1)

        for entry in monthly_query:
            month_date = entry['month']
            month_str = month_date.strftime('%b %Y')
            for data in monthly_data:
                if data['month'] == month_str:
                    data['total'] = float(entry['total_payments'] or 0.0)
                    break

        return Response({
            "data": {
                "total_sales_this_year": total_sales_this_year,
                "total_available_products": total_products,
                "total_users": total_users,
                "total_payments_this_year": total_payments_this_year,
                "monthly_data": monthly_data
            }
        })


class ApiAdminOrder(viewsets.ModelViewSet):
    http_method_names = ["get", "patch", "head", "options"]
    pagination_class = CustomPagination
    # permission_classes = [IsAdminUser]
    permission_classes = [AllowAny]
    filterset_class = OrderFilter
    ordering_fields = ['order_date', 'total_amount', 'delivery_date']
    ordering = ['-order_date', '-created_at']
    search_fields = ["id", "status", "payment_provider"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return OrderSerializer
        return PatchOrderSerializer

    def get_queryset(self):
        return Order.objects.all()

    @swagger_helper("Admin", "Admin Orders page")
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

    @swagger_helper("Admin", "Admin Orders page")
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @swagger_helper("Admin", "Admin Orders page")
    def partial_update(self, *args, **kwargs):
        order = self.get_object()
        serializer = self.get_serializer(order, data=self.request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get('status') == 'CANCELLED' and order.status != 'REFUNDED':
            if not order.transaction_id or not order.payment_provider:
                return Response({"error": "Refund cannot be processed. Contact support."}, status=400)
            refund_success = initiate_refund(order)
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

            else:
                return Response({"error": "Refund processing failed."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        elif serializer.validated_data.get('status') == 'SHIPPED' and order.status != "SHIPPED":
            order.status = 'SHIPPED'
            order.save()
            notify_user_for_shipped_order(order)

        elif serializer.validated_data.get('status') == 'DELIVERED' and order.status != "DELIVERED":
            order.status = 'DELIVERED'
            current_time = timezone.now()
            lagos_tz = pytz_timezone('Africa/Lagos')
            lagos_time = current_time.astimezone(lagos_tz)
            order.delivery_date = lagos_time.date()
            order.save()
            notify_user_for_delivered_order(order)
        else:
            serializer.save()
        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data)