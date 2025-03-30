from django.shortcuts import render
from .serializers import ProductCategorySerializer, ProductSubCategorySerializer, ProductSerializer, ProductSizeSerializer
from .models import Product, ProductSubCategory, ProductCategory, ProductSize
from rest_framework import viewsets


class ApiProductCategory(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
