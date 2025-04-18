import datetime
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from apps.orders.models import Order
from apps.products.models import Product
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from rest_framework import viewsets, status
from datetime import date, timedelta

User = get_user_model()


class OrderDashboard(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(operation_id="order --admin only", operation_description="monthly order data", tags=["Order admin page"])
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