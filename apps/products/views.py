from django.shortcuts import render
from .pagination import CustomPagination
from .serializers import ProductCategorySerializer, ProductSubCategorySerializer, ProductSerializer, \
    ProductSizeSerializer, ProductViewSerializer, ProductSubCategoryViewSerializer, ProductCategoryDetailSerializer, \
    ProductSizeViewSerializer
from .models import Product, ProductSubCategory, ProductCategory, ProductSize
from rest_framework import viewsets
from drf_yasg.utils import swagger_auto_schema


class ApiProductCategory(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = ProductCategory.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductCategoryDetailSerializer
        return ProductCategorySerializer

    @swagger_auto_schema(operation_id="list product category", operation_description="retrieve a list of product categories", tags=["ProductCategory"])
    def list(self, *args, **kwargs):
        return super().list(self, *args, **kwargs)

    @swagger_auto_schema(operation_id="retrieve product category", operation_desciption="Retrieves details of a specific product category", tags=["ProductCategory"])
    def retrieve(self, *args, **kwargs):
        return super().create(self, *args, **kwargs)

    @swagger_auto_schema(operation_id="create product category", operation_desciption="Create a new product category", tags=["ProductCategory"])
    def create(self, *args, **kwargs):
        return super().create(self, *args, **kwargs)

    @swagger_auto_schema(operation_id="update product category", operation_description="update a product category", tags=["ProductCategory"])
    def partial_update(self, *args, **kwargs):
        return super().partial_update(self, *args, **kwargs)

    @swagger_auto_schema(operation_id="delete product category", operation_description="delete a product category", tags=["ProductCategory"])
    def destroy(self, *args, **kwargs):
        return super().destroy(self, *args, **kwargs)


class ApiProductSubCategory(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = ProductSubCategory.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductSubCategoryViewSerializer
        return ProductSubCategorySerializer

    @swagger_auto_schema(operation_id="list product sub-category", operation_description="retrieve a list of product sub-category", tags=["ProductSubCategory"])
    def list(self, *args, **kwargs):
        return super().list(self, *args, **kwargs)

    @swagger_auto_schema(operation_id="retrieve product sub-category", operation_desciption="Retrieves details of a specific product sub-category", tags=["ProductSubCategory"])
    def retrieve(self, *args, **kwargs):
        return super().create(self, *args, **kwargs)

    @swagger_auto_schema(operation_id="create product sub-category", operation_desciption="Create a new product sub-category", tags=["ProductSubCategory"])
    def create(self, *args, **kwargs):
        return super().create(self, *args, **kwargs)

    @swagger_auto_schema(operation_id="update product sub-category", operation_description="update a product sub-category", tags=["ProductSubCategory"])
    def partial_update(self, *args, **kwargs):
        return super().partial_update(self, *args, **kwargs)

    @swagger_auto_schema(operation_id="delete product sub-category", operation_description="delete a product sub-category", tags=["ProductSubCategory"])
    def destroy(self, *args, **kwargs):
        return super().destroy(self, *args, **kwargs)


class ApiProduct(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = Product.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductViewSerializer
        return ProductSerializer


class ApiProductSize(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = ProductSize.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductSizeViewSerializer
        return ProductSizeSerializer

