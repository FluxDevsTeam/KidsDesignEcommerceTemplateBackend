import json
from urllib import request

from django.core.cache import cache
from django.shortcuts import render
from .pagination import CustomPagination
from .serializers import ProductCategorySerializer, ProductSubCategorySerializer, ProductSerializer, \
    ProductSizeSerializer, ProductViewSerializer, ProductSubCategoryViewSerializer, ProductCategoryDetailSerializer, \
    ProductSizeViewSerializer
from .models import Product, ProductSubCategory, ProductCategory, ProductSize
from rest_framework import viewsets
from .utils import swagger_helper
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F
from django.db import transaction
import random


class ApiProductCategory(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = ProductCategory.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductCategoryDetailSerializer
        return ProductCategorySerializer

    @swagger_helper(tags="ProductCategory", model="Product category")
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_helper(tags="ProductCategory", model="Product category")
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @swagger_helper(tags="ProductCategory", model="Product category")
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)

    @swagger_helper(tags="ProductCategory", model="Product category")
    def partial_update(self, *args, **kwargs):
        return super().partial_update(*args, **kwargs)

    @swagger_helper(tags="ProductCategory", model="Product category")
    def destroy(self, *args, **kwargs):
        return super().destroy(*args, **kwargs)


class ApiProductSubCategory(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = ProductSubCategory.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductSubCategoryViewSerializer
        return ProductSubCategorySerializer

    @swagger_helper(tags="ProductSubCategory", model="Product sub category")
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_helper(tags="ProductSubCategory", model="Product sub category")
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @swagger_helper(tags="ProductSubCategory", model="Product sub category")
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)

    @swagger_helper(tags="ProductSubCategory", model="Product sub category")
    def partial_update(self, *args, **kwargs):
        return super().partial_update(*args, **kwargs)

    @swagger_helper(tags="ProductSubCategory", model="Product sub category")
    def destroy(self, *args, **kwargs):
        return super().destroy(*args, **kwargs)


class ApiProduct(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = Product.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductViewSerializer
        return ProductSerializer

    @swagger_helper(tags="Product", model="Product")
    def list(self, request, *args, **kwargs):
        query_params = dict(request.query_params)
        cache_key = f"product_list:{json.dumps(query_params, sort_keys=True)}"
        cache_timeout = 300

        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="Product", model="Product")
    def retrieve(self, request, *args, **kwargs):
        query_params = dict(request.query_params)
        product_pk = kwargs["pk"]
        cache_key = f"product_detail:{product_pk}:{json.dumps(query_params, sort_keys=True)}"
        cache_timeout = 300

        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)

        response = super().retrieve(*args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="Product", model="Product")
    def create(self, *args, **kwargs):
        response = super().create(*args, **kwargs)
        cache.delete(f"product_list:*")
        return response

    @swagger_helper(tags="Product", model="Product")
    def destroy(self, *args, **kwargs):
        response = super().destroy(*args, **kwargs)
        cache.delete(f"product_list:*")
        cache.delete(f"product_detail:{kwargs["pk"]}")
        return response

    @swagger_helper(tags="Product", model="Product")
    def partial_update(self, *args, **kwargs):
        response = super().partial_update(*args, **kwargs)
        cache.delete(f"product_list:*")
        cache.delete(f"product_detail:{kwargs["pk"]}")
        return response

    @swagger_helper(tags="Product", model="Product")
    @action(methods=['GET'], detail=False)
    def homepage(self, request):
        pass

    @action(detail=False, methods=['get'], url_path='search')
    @swagger_helper(tags="Search", model="Product")
    def search(self, request, *args, **kwargs):
        query = request.query_params.get("search", "").strip()


class ApiProductSize(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = ProductSize.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductSizeViewSerializer
        return ProductSizeSerializer

    @swagger_helper(tags="ProductSize", model="Product size")
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_helper(tags="ProductSize", model="Product size")
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @swagger_helper(tags="ProductSize", model="Product size")
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)

    @swagger_helper(tags="ProductSize", model="Product size")
    def partial_update(self, *args, **kwargs):
        return super().partial_update(*args, **kwargs)

    @swagger_helper(tags="ProductSize", model="Product size")
    def destroy(self, *args, **kwargs):
        return super().destroy(*args, **kwargs)