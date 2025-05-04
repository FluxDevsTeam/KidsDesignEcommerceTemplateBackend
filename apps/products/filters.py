from django_filters import ModelChoiceFilter
from django_filters.rest_framework import FilterSet, NumberFilter, BooleanFilter
from .models import Product, ProductCategory
from django.db.models import Min, Q
from django.db import models


class ProductFilter(FilterSet):
    min_price = NumberFilter(method='filter_min_price')
    max_price = NumberFilter(method='filter_max_price')
    discount = BooleanFilter(method='filter_discount')
    category = ModelChoiceFilter(field_name='sub_category__category', queryset=ProductCategory.objects.all())

    class Meta:
        model = Product
        fields = ['category', 'sub_category', 'date_created', 'min_price', 'max_price', 'is_available', 'latest_item', 'top_selling_items']

    def filter_min_price(self, queryset, name, value):
        return queryset.annotate(min_size_price=Min('sizes__price')).filter(min_size_price__gte=value)

    def filter_max_price(self, queryset, name, value):
        return queryset.annotate(min_size_price=Min('sizes__price')).filter(min_size_price__lte=value)

    def filter_discount(self, queryset, name, value):
        if value:
            return queryset.filter(sizes__undiscounted_price__gt=models.F('sizes__price'), sizes__undiscounted_price__isnull=False).distinct()
        return queryset

# /?sub_category=2&min_price=100&max_price=500
