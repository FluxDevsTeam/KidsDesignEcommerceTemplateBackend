from django.shortcuts import render
from .serializers import ProductCategorySerializer, ProductSubCategorySerializer, ProductSerializer, \
    ProductSizeSerializer, ProductViewSerializer, ProductSubCategoryViewSerializer, ProductCategoryDetailSerializer
from .models import Product, ProductSubCategory, ProductCategory, ProductSize
from rest_framework import viewsets


class ApiProductCategory(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductCategoryDetailSerializer
        return ProductCategorySerializer


class ApiProductSubCategory(viewsets.ModelViewSet):
    queryset = ProductSubCategory.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductSubCategoryViewSerializer
        return ProductSubCategorySerializer


class ApiProduct(viewsets.ModelViewSet):
    queryset = Product.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductViewSerializer
        return ProductSerializer


class ApiProductSize(viewsets.ModelViewSet):
    queryset = ProductSize.objects.all()
    serializer_class = ProductSizeSerializer

