from django_filters.rest_framework import FilterSet, NumberFilter, BooleanFilter
from .models import Product
from django.db import models


class ProductFilter(FilterSet):
    min_price = NumberFilter(field_name="price", lookup_expr='gte')
    max_price = NumberFilter(field_name="price", lookup_expr='lte')
    discount = BooleanFilter(method='filter_discount')
    class Meta:
        model = Product
        fields = ['sub_category', 'sub_category__category', 'price', 'date_created', 'min_price', 'max_price', "is_available", "latest_item", "top_selling_items"]

    def filter_discount(self, queryset, name, value):
        if value:
            return queryset.filter(discounted_price__lt=models.F('price'))
        return queryset

# /?sub_category=2&min_price=100&max_price=500
