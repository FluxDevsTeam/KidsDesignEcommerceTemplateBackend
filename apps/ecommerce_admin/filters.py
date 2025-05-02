from django_filters.rest_framework import FilterSet, BooleanFilter
from django.utils import timezone
from ..orders.models import Order


class OrderFilter(FilterSet):
    due = BooleanFilter(method='filter_due')

    class Meta:
        model = Order
        fields = ['status', 'due']

    def filter_due(self, queryset, name, value):
        if value:
            today = timezone.now().date()
            return queryset.filter(delivery_date__lte=today)
        return queryset
