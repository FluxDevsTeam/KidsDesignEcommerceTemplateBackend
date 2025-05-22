import json

from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.cache import cache
from .filters import ProductFilter
from .pagination import CustomPagination
from .permissions import IsAdminOrReadOnly
from .serializers import ProductCategorySerializer, ProductSubCategorySerializer, ProductSerializer, \
    ProductSizeSerializer, ProductViewSerializer, ProductSubCategoryViewSerializer, ProductCategoryDetailSerializer, \
    ProductSizeViewSerializer, ProductDetailViewSerializer
from .models import Product, ProductSubCategory, ProductCategory, ProductSize
from rest_framework import viewsets, status
from .utils import swagger_helper
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F, Q, Case, When, Value, BooleanField
from django.db import transaction
from itertools import chain
import random

TIMEOUT = int(settings.CACHE_TIMEOUT)


class ApiProductCategory(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = ProductCategory.objects.all()
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name"]
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductCategoryDetailSerializer
        return ProductCategorySerializer

    @swagger_helper(tags="ProductCategory", model="Product category")
    def list(self, request, *args, **kwargs):
        cache_timeout = TIMEOUT
        cache_params = dict(request.query_params)
        cache_key = f"category_list:{json.dumps(cache_params, sort_keys=True)}"
        if cached_response := cache.get(cache_key):
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="ProductCategory", model="Product category")
    def retrieve(self, request, *args, **kwargs):
        cache_timeout = TIMEOUT
        cache_key = f"category_detail:{kwargs['pk']}"
        if cached_response := cache.get(cache_key):
            return Response(cached_response)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="ProductCategory", model="Product category")
    def create(self, *args, **kwargs):
        response = super().create(*args, **kwargs)
        cache.delete_pattern("category_list:*")
        cache.delete_pattern("category_detail:*")
        cache.delete_pattern("subcategory_list:*")
        cache.delete_pattern("subcategory_detail:*")
        cache.delete_pattern("product_list:*")
        cache.delete_pattern("product_detail:*")
        cache.delete_pattern("product_size_list:*")
        cache.delete_pattern("search:*")
        cache.delete_pattern("search_suggestions:*")
        cache.delete_pattern("product_suggestions:*")
        cache.delete_pattern("product_homepage:*")
        return response

    @swagger_helper(tags="ProductCategory", model="Product category")
    def partial_update(self, *args, **kwargs):
        response = super().partial_update(*args, **kwargs)
        cache.delete_pattern("category_list:*")
        cache.delete_pattern(f"category_detail:{kwargs['pk']}")
        cache.delete_pattern("subcategory_list:*")
        cache.delete_pattern("subcategory_detail:*")
        cache.delete_pattern("product_list:*")
        cache.delete_pattern("product_detail:*")
        cache.delete_pattern("product_size_list:*")
        cache.delete_pattern("search:*")
        cache.delete_pattern("search_suggestions:*")
        cache.delete_pattern("product_suggestions:*")
        cache.delete_pattern("product_homepage:*")
        return response

    @swagger_helper(tags="ProductCategory", model="Product category")
    def destroy(self, *args, **kwargs):
        response = super().destroy(*args, **kwargs)
        cache.delete_pattern("category_list:*")
        cache.delete_pattern(f"category_detail:{kwargs['pk']}")
        cache.delete_pattern("subcategory_list:*")
        cache.delete_pattern("subcategory_detail:*")
        cache.delete_pattern("product_list:*")
        cache.delete_pattern("product_detail:*")
        cache.delete_pattern("product_size_list:*")
        cache.delete_pattern("search:*")
        cache.delete_pattern("search_suggestions:*")
        cache.delete_pattern("product_suggestions:*")
        cache.delete_pattern("product_homepage:*")
        return response


class ApiProductSubCategory(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = ProductSubCategory.objects.all()
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["category"]
    search_fields = ["name"]
    ordering = ['name']

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductSubCategoryViewSerializer
        return ProductSubCategorySerializer

    @swagger_helper(tags="ProductSubCategory", model="Product sub category")
    def list(self, request, *args, **kwargs):
        cache_timeout = TIMEOUT
        cache_params = dict(request.query_params)
        cache_key = f"subcategory_list:{json.dumps(cache_params, sort_keys=True)}"
        if cached_response := cache.get(cache_key):
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="ProductSubCategory", model="Product sub category")
    def retrieve(self, request, *args, **kwargs):
        cache_timeout = TIMEOUT
        cache_key = f"subcategory_detail:{kwargs['pk']}"
        if cached_response := cache.get(cache_key):
            return Response(cached_response)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="ProductSubCategory", model="Product sub category")
    def create(self, *args, **kwargs):
        response = super().create(*args, **kwargs)
        cache.delete_pattern("subcategory_list:*")
        cache.delete_pattern("subcategory_detail:*")
        cache.delete_pattern("product_list:*")
        cache.delete_pattern("product_detail:*")
        cache.delete_pattern("product_size_list:*")
        cache.delete_pattern("search:*")
        cache.delete_pattern("search_suggestions:*")
        cache.delete_pattern("product_suggestions:*")
        cache.delete_pattern("product_homepage:*")
        return response

    @swagger_helper(tags="ProductSubCategory", model="Product sub category")
    def partial_update(self, *args, **kwargs):
        response = super().partial_update(*args, **kwargs)
        cache.delete_pattern("subcategory_list:*")
        cache.delete_pattern(f"subcategory_detail:{kwargs['pk']}")
        cache.delete_pattern("product_list:*")
        cache.delete_pattern("product_detail:*")
        cache.delete_pattern("product_size_list:*")
        cache.delete_pattern("search:*")
        cache.delete_pattern("search_suggestions:*")
        cache.delete_pattern("product_suggestions:*")
        cache.delete_pattern("product_homepage:*")
        return response

    @swagger_helper(tags="ProductSubCategory", model="Product sub category")
    def destroy(self, *args, **kwargs):
        response = super().destroy(*args, **kwargs)
        cache.delete_pattern("subcategory_list:*")
        cache.delete_pattern(f"subcategory_detail:{kwargs['pk']}")
        cache.delete_pattern("product_list:*")
        cache.delete_pattern("product_detail:*")
        cache.delete_pattern("product_size_list:*")
        cache.delete_pattern("search:*")
        cache.delete_pattern("search_suggestions:*")
        cache.delete_pattern("product_suggestions:*")
        cache.delete_pattern("product_homepage:*")
        return response


class ApiProduct(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = Product.objects.all()
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    ordering_fields = ["price", "date_created", "is_available", "latest_item", "top_selling_items"]
    filterset_class = ProductFilter
    ordering = ["top_selling_items", "latest_item"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailViewSerializer
        if self.request.method == "GET":
            return ProductViewSerializer
        return ProductSerializer

    @swagger_helper(tags="Product", model="Product")
    def list(self, request, *args, **kwargs):
        cache_timeout = TIMEOUT
        cache_params = dict(request.query_params)
        cache_key = f"product_list:{json.dumps(cache_params, sort_keys=True)}"
        if cached_response := cache.get(cache_key):
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="Product", model="Product")
    def retrieve(self, request, *args, **kwargs):
        cache_timeout = TIMEOUT
        cache_key = f"product_detail:{kwargs['pk']}"
        if cached_response := cache.get(cache_key):
            return Response(cached_response)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="Product", model="Product")
    def create(self, *args, **kwargs):
        response = super().create(*args, **kwargs)
        cache.delete_pattern("product_list:*")
        cache.delete_pattern("product_detail:*")
        cache.delete_pattern("product_size_list:*")
        cache.delete_pattern("search:*")
        cache.delete_pattern("search_suggestions:*")
        cache.delete_pattern("cart_list:*")
        cache.delete_pattern("cart_item_list:*")
        cache.delete_pattern("wishlist_list:*")
        cache.delete_pattern("product_suggestions:*")
        cache.delete_pattern("product_homepage:*")
        return response

    @swagger_helper(tags="Product", model="Product")
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            with transaction.atomic():
                validated_data = serializer.validated_data
                max_position = 20

                if "latest_item_position" in validated_data:
                    new_position = validated_data["latest_item_position"]
                    self.get_queryset().filter(
                        latest_item=True,
                        latest_item_position__gte=new_position,
                        latest_item_position__isnull=False
                    ).exclude(id=instance.id).select_for_update().update(
                        latest_item_position=Case(
                            When(latest_item_position__gt=max_position, then=None),
                            default=F("latest_item_position") + 1
                        ),
                        latest_item=Case(
                            When(latest_item_position__gt=max_position, then=False),
                            default=True
                        )
                    )

                if "top_selling_position" in validated_data:
                    new_selling_position = validated_data["top_selling_position"]
                    self.get_queryset().filter(
                        top_selling_items=True,
                        top_selling_position__gte=new_selling_position,
                        top_selling_position__isnull=False
                    ).exclude(id=instance.id).select_for_update().update(
                        top_selling_position=Case(
                            When(top_selling_position__gt=max_position, then=None),
                            default=F("top_selling_position") + 1
                        ),
                        top_selling_items=Case(
                            When(top_selling_position__gt=max_position, then=False),
                            default=True
                        )
                    )
                serializer.save()

            cache.delete_pattern("product_list:*")
            cache.delete_pattern(f"product_detail:{kwargs['pk']}")
            cache.delete_pattern(f"product_size_list:{kwargs['pk']}:*")
            cache.delete_pattern("search:*")
            cache.delete_pattern("search_suggestions:*")
            cache.delete_pattern("cart_list:*")
            cache.delete_pattern("cart_item_list:*")
            cache.delete_pattern("wishlist_list:*")
            cache.delete_pattern("product_suggestions:*")
            cache.delete_pattern("product_homepage:*")
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_helper(tags="Product", model="Product")
    def destroy(self, *args, **kwargs):
        response = super().destroy(*args, **kwargs)
        cache.delete_pattern("product_list:*")
        cache.delete_pattern(f"product_detail:{kwargs['pk']}")
        cache.delete_pattern(f"product_size_list:{kwargs['pk']}:*")
        cache.delete_pattern("search:*")
        cache.delete_pattern("search_suggestions:*")
        cache.delete_pattern("cart_list:*")
        cache.delete_pattern("cart_item_list:*")
        cache.delete_pattern("wishlist_list:*")
        cache.delete_pattern("product_suggestions:*")
        cache.delete_pattern("product_homepage:*")
        return response

    @swagger_helper(tags="Product", model="Product")
    @action(methods=['GET'], detail=False)
    def homepage(self, request):
        cache_timeout = TIMEOUT
        cache_params = dict(request.query_params)
        cache_key = f"product_homepage:{json.dumps(cache_params, sort_keys=True)}"
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)

        products = Product.objects.select_related('sub_category__category')
        latest_prioritized = products.filter(Q(latest_item=True) & Q(latest_item_position__isnull=False), is_available=True).order_by('latest_item_position')
        latest_prioritized_list = list(latest_prioritized)
        random_others = products.exclude(id__in=[item.id for item in latest_prioritized_list]).order_by('?').filter(is_available=True)
        latest_products = latest_prioritized_list + list(random_others)

        top_selling_prioritized = products.filter(Q(top_selling_items=True) & Q(top_selling_position__isnull=False), is_available=True).order_by('top_selling_position')
        top_selling_prioritized_list = list(top_selling_prioritized)
        other_latest = products.exclude(id__in=[item.id for item in top_selling_prioritized_list]).order_by('?').filter(is_available=True)
        top_selling_products = top_selling_prioritized_list + list(other_latest)

        paginator = self.pagination_class()

        if 'page_size' in request.query_params:
            page_size = int(request.query_params['page_size'])
        else:
            page_size = 12

        paginator.page_size = page_size

        latest_page = paginator.paginate_queryset(latest_products, request, view=self)
        top_selling_page = paginator.paginate_queryset(top_selling_products, request, view=self)

        latest_serializer = self.get_serializer(latest_page, many=True)
        top_selling_serializer = self.get_serializer(top_selling_page, many=True)

        response_data = {
            "latest_items": paginator.get_paginated_response(latest_serializer.data).data,
            "top_selling_items": paginator.get_paginated_response(top_selling_serializer.data).data
        }
        cache.set(cache_key, response_data, cache_timeout)
        return Response(response_data)

    @swagger_auto_schema(manual_parameters=[openapi.Parameter('search', openapi.IN_QUERY, description="Search keyword", type=openapi.TYPE_STRING), openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER), openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page (max: 100)", type=openapi.TYPE_INTEGER)], operation_id="Search Products", operation_description="Search and paginate products", tags=["Product"])
    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request, *args, **kwargs):
        query = request.query_params.get("search", "").strip()
        cache_timeout = TIMEOUT
        cache_params = dict(request.query_params)
        cache_key = f"product_search:{json.dumps(cache_params, sort_keys=True)}"
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)

        if not query:
            return Response({"count": 0, "next": None, "previous": None, "results": []})

        search_data = self.get_queryset().filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sizes__size__icontains=query) |
            Q(sub_category__name__icontains=query) |
            Q(sub_category__category__name__icontains=query),
            is_available=True
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

    # admin search also searches for unavailable products. that's the only difference
    @swagger_auto_schema(manual_parameters=[openapi.Parameter('search', openapi.IN_QUERY, description="Search keyword", type=openapi.TYPE_STRING), openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER), openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page (max: 100)", type=openapi.TYPE_INTEGER)], operation_id="Admin Search Products", operation_description="Search and paginate products", tags=["Product"])
    @action(detail=False, methods=['get'], url_path='admin-search')
    def admin_search(self, request, *args, **kwargs):
        query = request.query_params.get("search", "").strip()
        cache_timeout = TIMEOUT
        cache_params = dict(request.query_params)
        cache_key = f"product_search:{json.dumps(cache_params, sort_keys=True)}"
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)

        if not query:
            return Response({"count": 0, "next": None, "previous": None, "results": []})

        search_data = self.get_queryset().filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sizes__size__icontains=query) |
            Q(sub_category__name__icontains=query) |
            Q(sub_category__category__name__icontains=query),
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

    @swagger_auto_schema(manual_parameters=[openapi.Parameter('query', openapi.IN_QUERY, description="autocomplete for search", type=openapi.TYPE_STRING), openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER), openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page (max: 100)", type=openapi.TYPE_INTEGER)], operation_id="Auocomplete Products", operation_description="Search products for autocomplete", tags=["Product"])
    @action(detail=False, methods=['get'], url_path='autocomplete')
    def autocomplete(self, request, *args, **kwargs):
        query = request.query_params.get('query', '').strip()
        if not query:
            return Response([])

        cache_timeout = TIMEOUT
        cache_key = f"search_suggestions:{query}"
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)

        products = self.get_queryset().filter(
            Q(name__istartswith=query) |
            Q(sub_category__name__istartswith=query) |
            Q(sub_category__category__name__istartswith=query) |
            Q(sizes__size__istartswith=query) |
            Q(name__icontains=query) & ~Q(name__istartswith=query) |
            Q(sub_category__name__icontains=query) & ~Q(sub_category__name__istartswith=query) |
            Q(sub_category__category__name__icontains=query) & ~Q(sub_category__category__name__istartswith=query) |
            Q(sizes__size__icontains=query) & ~Q(sizes__size__istartswith=query),
            is_available=True
        ).values('name', 'sub_category__name', 'sub_category__category__name', 'sizes__size').distinct()[:40]

        starts_with = set()
        contains = set()
        query_lower = query.lower()
        for value in chain.from_iterable(row.values() for row in products):
            if value:
                value_lower = value.lower()
                if value_lower.startswith(query_lower):
                    starts_with.add(value)
                elif query_lower in value_lower:
                    contains.add(value)
            if len(starts_with) + len(contains) >= 20:
                break

        suggestions = (sorted(starts_with) + sorted(contains))[:20]
        cache.set(cache_key, suggestions, cache_timeout)
        return Response(suggestions)

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('sub_category_id', openapi.IN_QUERY, description="Primary Subcategory ID for suggestions", type=openapi.TYPE_INTEGER),
        openapi.Parameter('second_sub_category_id', openapi.IN_QUERY, description="Secondary Subcategory ID for suggestions", type=openapi.TYPE_INTEGER),
        openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
        openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page (max: 20)", type=openapi.TYPE_INTEGER),], operation_id="Product Suggestions", operation_description="Get product suggestions based on subcategory priority, with optional secondary subcategory", tags=["Product"])
    @action(detail=False, methods=['get'], url_path='suggestions')
    def suggestions(self, request, *args, **kwargs):
        cache_timeout = TIMEOUT
        cache_params = dict(request.query_params)
        cache_key = f"product_suggestions:{json.dumps(cache_params, sort_keys=True)}"
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)

        sub_category_id = request.query_params.get('sub_category_id')
        second_sub_category_id = request.query_params.get('second_sub_category_id')
        products = Product.objects.select_related('sub_category__category').filter(is_available=True)
        max_items = 20

        ordering = [
            Case(When(top_selling_items=True, then=Value(0)), default=Value(1), output_field=BooleanField()),
            Case(When(latest_item=True, then=Value(0)), default=Value(1), output_field=BooleanField()),
        ]

        if not sub_category_id and not second_sub_category_id:
            all_products = products.order_by("top_selling_position", "latest_item_position")[:max_items]
            final_products = list(all_products)

        else:
            try:
                priority_pools = []
                used_category_ids = set()
                selected_product_ids = set()

                if sub_category_id:
                    sub_category_id = int(sub_category_id)
                    target_subcategory = ProductSubCategory.objects.get(id=sub_category_id)
                    target_category = target_subcategory.category
                    used_category_ids.add(target_category.id)
                    priority_pools.append({
                        'products': list(products.filter(sub_category_id=sub_category_id).order_by(*ordering)),
                        'weight': 0.4
                    })
                    priority_pools.append({
                        'products': list(products.filter(sub_category__category=target_category)
                                         .exclude(sub_category_id=sub_category_id).order_by(*ordering)),
                        'weight': 0.2
                    })

                if second_sub_category_id:
                    second_sub_category_id = int(second_sub_category_id)
                    if sub_category_id and sub_category_id == second_sub_category_id:
                        second_sub_category_id = None
                    else:
                        second_target_subcategory = ProductSubCategory.objects.get(id=second_sub_category_id)
                        second_target_category = second_target_subcategory.category
                        used_category_ids.add(second_target_category.id)
                        priority_pools.append({
                            'products': list(
                                products.filter(sub_category_id=second_sub_category_id).order_by(*ordering)),
                            'weight': 0.25
                        })
                        priority_pools.append({
                            'products': list(products.filter(sub_category__category=second_target_category)
                                             .exclude(sub_category_id=second_sub_category_id).order_by(*ordering)),
                            'weight': 0.1
                        })

                priority_pools.append({
                    'products': list(
                        products.exclude(sub_category__category__in=used_category_ids).order_by(*ordering)),
                    'weight': 0.05
                })

                priority_pools = [pool for pool in priority_pools if pool['products']]
                total_weight = sum(pool['weight'] for pool in priority_pools)
                if total_weight > 0:
                    for pool in priority_pools:
                        pool['weight'] /= total_weight

                final_products = []
                while len(final_products) < max_items and any(pool['products'] for pool in priority_pools):
                    rand = random.random()
                    cumulative_weight = 0
                    selected_pool = None
                    for pool in priority_pools:
                        if not pool['products']:
                            continue
                        cumulative_weight += pool['weight']
                        if rand <= cumulative_weight:
                            selected_pool = pool
                            break
                    if not selected_pool:
                        selected_pool = next((pool for pool in priority_pools if pool['products']), None)
                    if not selected_pool:
                        break

                    selected_pool['products'] = [p for p in selected_pool['products'] if
                                                 p.id not in selected_product_ids]
                    if not selected_pool['products']:
                        continue

                    product = selected_pool['products'].pop(0)
                    selected_product_ids.add(product.id)
                    final_products.append(product)

                if len(final_products) < max_items:
                    remaining_products = list(
                        products.exclude(id__in=selected_product_ids).order_by('?')[:max_items - len(final_products)])
                    final_products.extend(remaining_products)

                final_products = final_products[:max_items]

            except (ProductSubCategory.DoesNotExist, ValueError):
                final_products = list(products.order_by('?')[:max_items])

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(final_products, request, view=self)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = paginator.get_paginated_response(serializer.data).data
        else:
            serializer = self.get_serializer(final_products, many=True)
            response_data = serializer.data

        cache.set(cache_key, response_data, cache_timeout)
        return Response(response_data, status=status.HTTP_200_OK)


class ApiProductSize(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["product"]
    search_fields = ["size"]
    ordering_fields = ["quantity"]

    def get_queryset(self):
        product_id = self.kwargs.get('item_pk')
        return ProductSize.objects.filter(product=product_id)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductSizeViewSerializer
        return ProductSizeSerializer

    @swagger_helper(tags="ProductSize", model="Product size")
    def list(self, request, *args, **kwargs):
        item_pk = self.kwargs.get('item_pk')
        cache_timeout = TIMEOUT
        cache_params = dict(request.query_params)
        cache_key = f"product_size_list:{item_pk}:{json.dumps(cache_params, sort_keys=True)}"
        if cached_response := cache.get(cache_key):
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="ProductSize", model="Product size")
    def retrieve(self, request, *args, **kwargs):
        cache_timeout = TIMEOUT
        cache_key = f"product_size_detail:{kwargs['pk']}"
        if cached_response := cache.get(cache_key):
            return Response(cached_response)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="ProductSize", model="Product size")
    def create(self, *args, **kwargs):
        response = super().create(*args, **kwargs)
        item_pk = self.kwargs.get('item_pk')
        cache.delete_pattern(f"product_size_list:{item_pk}:*")
        cache.delete_pattern(f"product_detail:{item_pk}")
        cache.delete_pattern("product_list:*")
        cache.delete_pattern("product_detail:*")
        cache.delete_pattern("search:*")
        cache.delete_pattern("search_suggestions:*")
        cache.delete_pattern("product_suggestions:*")
        cache.delete_pattern("product_homepage:*")
        return response

    @swagger_helper(tags="ProductSize", model="Product size")
    def partial_update(self, *args, **kwargs):
        response = super().partial_update(*args, **kwargs)
        item_pk = self.kwargs.get('item_pk')
        cache.delete_pattern(f"product_size_list:{item_pk}:*")
        cache.delete_pattern(f"product_size_detail:{kwargs['pk']}")
        cache.delete_pattern(f"product_size_list:{item_pk}:*")
        cache.delete_pattern(f"product_detail:{item_pk}")
        cache.delete_pattern("product_list:*")
        cache.delete_pattern("product_detail:*")
        cache.delete_pattern("search:*")
        cache.delete_pattern("search_suggestions:*")
        cache.delete_pattern("product_suggestions:*")
        cache.delete_pattern("product_homepage:*")
        return response

    @swagger_helper(tags="ProductSize", model="Product size")
    def destroy(self, *args, **kwargs):
        item_pk = self.kwargs.get('item_pk')
        response = super().destroy(*args, **kwargs)
        cache.delete_pattern(f"product_size_detail:{kwargs['pk']}")
        cache.delete_pattern(f"product_size_list:{item_pk}:*")
        cache.delete_pattern(f"product_detail:{item_pk}")
        cache.delete_pattern("product_list:*")
        cache.delete_pattern("product_detail:*")
        cache.delete_pattern("search:*")
        cache.delete_pattern("search_suggestions:*")
        cache.delete_pattern("product_suggestions:*")
        cache.delete_pattern("product_homepage:*")
        return response

    def perform_create(self, serializer):
        product_id = self.kwargs.get('item_pk')
        product = get_object_or_404(Product, pk=product_id)
        serializer.save(product=product)

    def perform_update(self, serializer):
        product_id = self.kwargs.get('item_pk')
        product = get_object_or_404(Product, pk=product_id)
        serializer.save(product=product)
