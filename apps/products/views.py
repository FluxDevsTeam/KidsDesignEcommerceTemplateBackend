import json
from urllib import request
from drf_yasg.utils import swagger_auto_schema
from rest_framework.pagination import PageNumberPagination
from drf_yasg import openapi
from django.core.cache import cache
from django.shortcuts import render
from .pagination import CustomPagination
from .serializers import ProductCategorySerializer, ProductSubCategorySerializer, ProductSerializer, \
    ProductSizeSerializer, ProductViewSerializer, ProductSubCategoryViewSerializer, ProductCategoryDetailSerializer, \
    ProductSizeViewSerializer
from .models import Product, ProductSubCategory, ProductCategory, ProductSize
from rest_framework import viewsets, status
from .utils import swagger_helper
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F, Q
from django.db import transaction
import random
from itertools import chain

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
        cache.delete(f"search:*")
        return response

    @swagger_helper(tags="Product", model="Product")
    def destroy(self, *args, **kwargs):
        response = super().destroy(*args, **kwargs)
        cache.delete(f"product_list:*")
        cache.delete(f"product_detail:{kwargs["pk"]}")
        cache.delete(f"search:*")
        return response

    @swagger_helper(tags="Product", model="Product")
    def partial_update(self, *args, **kwargs):
        response = super().partial_update(*args, **kwargs)
        cache.delete(f"product_list:*")
        cache.delete(f"product_detail:{kwargs["pk"]}")
        cache.delete(f"search:*")
        return response

    @swagger_helper(tags="Product", model="Product")
    @action(methods=['GET'], detail=False)
    def homepage(self, request):
        pass

    @swagger_auto_schema(manual_parameters=[openapi.Parameter('search', openapi.IN_QUERY, description="Search keyword", type=openapi.TYPE_STRING), openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER), openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page (max: 100)", type=openapi.TYPE_INTEGER)], operation_id="GET products", operation_description="Search and paginate products", tags=["Product"])
    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request, *args, **kwargs):
        query = request.query_params.get("search", "").strip()

        query_params = dict(request.query_params)
        cache_key = f"product_search:{json.dumps(query_params, sort_keys=True)}"
        cache_timeout = 300

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        if not query:
            return Response({"count": 0, "next": None, "previous": None, "results": []})

        search_data = self.get_queryset().filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sizes__size__icontains=query) |
            Q(sub_category__name__icontains=query) |
            Q(sub_category__category__name__icontains=query)
        ).distinct()

        page = self.paginate_queryset(search_data)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data).data
        else:
            serializer = self.get_serializer(search_data, many=True)
            response_data = serializer.data

        cache.set(cache_key, response_data, cache_timeout)
        return Response(response_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(manual_parameters=[openapi.Parameter('query', openapi.IN_QUERY, description="autocomplete for search", type=openapi.TYPE_STRING), openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER), openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page (max: 100)", type=openapi.TYPE_INTEGER)], operation_id="GET products", operation_description="Search products for autocomplete", tags=["Product"])
    @action(detail=False, methods=['get'], url_path='autocomplete')
    def autocomplete(self, request, *args, **kwargs):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response([])

        cache_key = f"search_suggestions:{query}"
        cache_timeout = 300

        cached_suggestions = cache.get(cache_key)
        if cached_suggestions:
            return Response(cached_suggestions)

        products = self.get_queryset().filter(
            Q(name__istartswith=query) |
            Q(sub_category__name__istartswith=query) |
            Q(sub_category__category__name__istartswith=query) |
            Q(sizes__size__istartswith=query) |
            Q(name__icontains=query) & ~Q(name__istartswith=query) |
            Q(sub_category__name__icontains=query) & ~Q(sub_category__name__istartswith=query) |
            Q(sub_category__category__name__icontains=query) & ~Q(sub_category__category__name__istartswith=query) |
            Q(sizes__size__icontains=query) & ~Q(sizes__size__istartswith=query)
        ).values('name', 'sub_category__name', 'sub_category__category__name', 'sizes__size').distinct()[:40]

        results = set()
        for value in chain.from_iterable(row.values() for row in products):
            if value and (value.startswith(query) or query.lower() in value.lower()):
                results.add(value)
                if len(results) >= 20:
                    break
        suggestions = sorted(results)[:20]
        cache.set(cache_key, suggestions, cache_timeout)
        return Response(suggestions)


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