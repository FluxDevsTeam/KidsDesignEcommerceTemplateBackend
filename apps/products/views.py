import json
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
# from django.core.cache import cache
from .filters import ProductFilter
from .pagination import CustomPagination
from .permissions import IsAdminOrReadOnly
from .serializers import ProductCategorySerializer, ProductSubCategorySerializer, ProductSerializer, \
    ProductSizeSerializer, ProductViewSerializer, ProductSubCategoryViewSerializer, ProductCategoryDetailSerializer, \
    ProductSizeViewSerializer
from .models import Product, ProductSubCategory, ProductCategory, ProductSize
from rest_framework import viewsets, status
from .utils import swagger_helper
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F, Q, Case, When
from django.db import transaction
from itertools import chain


class ApiProductCategory(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = ProductCategory.objects.all()
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductCategoryDetailSerializer
        return ProductCategorySerializer

    @swagger_helper(tags="ProductCategory", model="Product category")
    def list(self, request, *args, **kwargs):
        # cache_timeout = 300
        # cache_params = dict(request.query_params)
        # cache_key = f"category_list:{json.dumps(cache_params, sort_keys=True)}"
        # cached_response = cache.get(cache_key)
        # if cached_response:
            # return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        # cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="ProductCategory", model="Product category")
    def retrieve(self, request, *args, **kwargs):
        # cache_timeout = 300
        # cache_key = f"category_detail:{kwargs['pk']}"
        # cached_response = cache.get(cache_key)
        # if cached_response:
        #     return Response(cached_response)

        response = super().retrieve(request, *args, **kwargs)
        # cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="ProductCategory", model="Product category")
    def create(self, *args, **kwargs):
        response = super().create(*args, **kwargs)
        # cache.delete("category_list:*")
        # cache.delete("category_detail:*")
        # cache.delete("subcategory_list:*")
        # cache.delete("subcategory_detail:*")
        # cache.delete("product_list:*")
        # cache.delete("search:*")
        # cache.delete("search_suggestions:*")
        return response

    @swagger_helper(tags="ProductCategory", model="Product category")
    def partial_update(self, *args, **kwargs):
        response = super().partial_update(*args, **kwargs)
        # cache.delete("category_list:*")
        # cache.delete(f"category_detail:{kwargs['pk']}")
        # cache.delete("subcategory_list:*")
        # cache.delete("subcategory_detail:*")
        # cache.delete("product_list:*")
        # cache.delete("search:*")
        # cache.delete("search_suggestions:*")
        return response

    @swagger_helper(tags="ProductCategory", model="Product category")
    def destroy(self, *args, **kwargs):
        response = super().destroy(*args, **kwargs)
        # cache.delete("category_list:*")
        # cache.delete(f"category_detail:{kwargs['pk']}")
        # cache.delete("subcategory_list:*")
        # cache.delete("subcategory_detail:*")
        # cache.delete("product_list:*")
        # cache.delete("search:*")
        # cache.delete("search_suggestions:*")
        return response


class ApiProductSubCategory(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = ProductSubCategory.objects.all()
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["category"]
    search_fields = ["name"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductSubCategoryViewSerializer
        return ProductSubCategorySerializer

    @swagger_helper(tags="ProductSubCategory", model="Product sub category")
    def list(self, request, *args, **kwargs):
        # cache_timeout = 300
        # cache_params = dict(request.query_params)
        # cache_key = f"subcategory_list:{json.dumps(cache_params, sort_keys=True)}"
        # cached_response = cache.get(cache_key)
        # if cached_response:
        #     return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        # cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="ProductSubCategory", model="Product sub category")
    def retrieve(self, request, *args, **kwargs):
        # cache_timeout = 300
        # cache_key = f"subcategory_detail:{kwargs['pk']}"
        # cached_response = cache.get(cache_key)
        # if cached_response:
        #     return Response(cached_response)

        response = super().retrieve(request, *args, **kwargs)
        # cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="ProductSubCategory", model="Product sub category")
    def create(self, *args, **kwargs):
        response = super().create(*args, **kwargs)
        # cache.delete("subcategory_list:*")
        # cache.delete("subcategory_detail:*")
        # cache.delete("product_list:*")
        # cache.delete("search:*")
        # cache.delete("search_suggestions:*")
        return response

    @swagger_helper(tags="ProductSubCategory", model="Product sub category")
    def partial_update(self, *args, **kwargs):
        response = super().partial_update(*args, **kwargs)
        # cache.delete("subcategory_list:*")
        # cache.delete(f"subcategory_detail:{kwargs['pk']}")
        # cache.delete("product_list:*")
        # cache.delete("search:*")
        # cache.delete("search_suggestions:*")
        return response

    @swagger_helper(tags="ProductSubCategory", model="Product sub category")
    def destroy(self, *args, **kwargs):
        response = super().destroy(*args, **kwargs)
        # cache.delete("subcategory_list:*")
        # cache.delete(f"subcategory_detail:{kwargs['pk']}")
        # cache.delete("product_list:*")
        # cache.delete("search:*")
        # cache.delete("search_suggestions:*")
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
        if self.request.method == "GET":
            return ProductViewSerializer
        return ProductSerializer

    @swagger_helper(tags="Product", model="Product")
    def list(self, request, *args, **kwargs):
        # cache_timeout = 300
        # cache_params = dict(request.query_params)
        # cache_key = f"product_list:{json.dumps(cache_params, sort_keys=True)}"
        # cached_response = cache.get(cache_key)
        # if cached_response:
        #     return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        # cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="Product", model="Product")
    def retrieve(self, request, *args, **kwargs):
        # cache_timeout = 300
        # cache_key = f"product_detail:{kwargs['pk']}"
        # cached_response = cache.get(cache_key)
        # if cached_response:
        #     return Response(cached_response)

        response = super().retrieve(request, *args, **kwargs)
        # cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="Product", model="Product")
    def create(self, *args, **kwargs):
        response = super().create(*args, **kwargs)
        # cache.delete("product_list:*")
        # cache.delete("search:*")
        # cache.delete("search_suggestions:*")
        # cache.delete("cart_list:*")
        # cache.delete("cart_item_list:*")
        # cache.delete("wishlist_list:*")
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

            # cache.delete("product_list:*")
            # cache.delete(f"product_detail:{kwargs['pk']}")
            # cache.delete("search:*")
            # cache.delete("search_suggestions:*")
            # cache.delete("cart_list:*")
            # cache.delete("cart_item_list:*")
            # cache.delete("wishlist_list:*")

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_helper(tags="Product", model="Product")
    def destroy(self, *args, **kwargs):
        response = super().destroy(*args, **kwargs)
        # cache.delete("product_list:*")
        # cache.delete(f"product_detail:{kwargs['pk']}")
        # cache.delete("search:*")
        # cache.delete("search_suggestions:*")
        # cache.delete("cart_list:*")
        # cache.delete("cart_item_list:*")
        # cache.delete("wishlist_list:*")
        return response

    @swagger_helper(tags="Product", model="Product")
    @action(methods=['GET'], detail=False)
    def homepage(self, request):
        # cache_timeout = 300
        # cache_params = dict(request.query_params)
        # cache_key = f"product_homepage:{json.dumps(cache_params, sort_keys=True)}"
        # cached_response = cache.get(cache_key)
        # if cached_response:
            # return Response(cached_response)

        products = Product.objects.select_related('sub_category__category')
        latest_prioritized = products.filter(Q(latest_item=True) & Q(latest_item_position__isnull=False)).order_by('latest_item_position')
        random_others = products.exclude(id__in=latest_prioritized.values_list('id', flat=True)).order_by('?')[:max(0, 20 - latest_prioritized.count())]
        latest_products = list(latest_prioritized) + list(random_others)

        top_selling_prioritized = products.filter(Q(top_selling_items=True) & Q(top_selling_position__isnull=False)).order_by('top_selling_position')
        other_latest = products.exclude(id__in=top_selling_prioritized.values_list('id', flat=True)).order_by('?')[:max(0, 20 - top_selling_prioritized.count())]
        top_selling_products = list(top_selling_prioritized) + list(other_latest)

        latest_paginator = self.pagination_class()
        top_selling_paginator = self.pagination_class()
        latest_paginator.page_query_param = 'page_latest'
        top_selling_paginator.page_query_param = 'page_top'

        latest_page = latest_paginator.paginate_queryset(latest_products, request, view=self)
        top_selling_page = top_selling_paginator.paginate_queryset(top_selling_products, request, view=self)

        latest_serializer = self.get_serializer(latest_page, many=True)
        top_selling_serializer = self.get_serializer(top_selling_page, many=True)

        response_data = {
            "latest_items": latest_paginator.get_paginated_response(latest_serializer.data).data,
            "top_selling_items": top_selling_paginator.get_paginated_response(top_selling_serializer.data).data
        }
        # cache.set(cache_key, response_data, cache_timeout)
        return Response(response_data)

    @swagger_auto_schema(manual_parameters=[openapi.Parameter('search', openapi.IN_QUERY, description="Search keyword", type=openapi.TYPE_STRING), openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER), openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page (max: 100)", type=openapi.TYPE_INTEGER)], operation_id="Search Products", operation_description="Search and paginate products", tags=["Product"])
    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request, *args, **kwargs):
        query = request.query_params.get("search", "").strip()
        # cache_timeout = 300
        # cache_params = dict(request.query_params)
        # cache_key = f"product_search:{json.dumps(cache_params, sort_keys=True)}"
        # cached_response = cache.get(cache_key)
        # if cached_response:
        #     return Response(cached_response)

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

        # cache.set(cache_key, response_data, cache_timeout)
        return Response(response_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(manual_parameters=[openapi.Parameter('query', openapi.IN_QUERY, description="autocomplete for search", type=openapi.TYPE_STRING), openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER), openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page (max: 100)", type=openapi.TYPE_INTEGER)], operation_id="Auocomplete Products", operation_description="Search products for autocomplete", tags=["Product"])
    @action(detail=False, methods=['get'], url_path='autocomplete')
    def autocomplete(self, request, *args, **kwargs):
        query = request.query_params.get('query', '').strip()
        if not query:
            return Response([])

        # cache_timeout = 300
        # cache_key = f"search_suggestions:{query}"
        # cached_response = cache.get(cache_key)
        # if cached_response:
        #     return Response(cached_response)

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
        # cache.set(cache_key, suggestions, cache_timeout)
        return Response(suggestions)


class ApiProductSize(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = ProductSize.objects.all()
    pagination_class = CustomPagination
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["product"]
    search_fields = ["size"]
    ordering_fields = ["quantity"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductSizeViewSerializer
        return ProductSizeSerializer

    @swagger_helper(tags="ProductSize", model="Product size")
    def list(self, request, *args, **kwargs):
        # cache_timeout = 300
        # cache_params = dict(request.query_params)
        # cache_key = f"product_size_list:{json.dumps(cache_params, sort_keys=True)}"
        # cached_response = cache.get(cache_key)
        # if cached_response:
        #     return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        # cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="ProductSize", model="Product size")
    def retrieve(self, request, *args, **kwargs):
        # cache_timeout = 300
        # cache_key = f"product_size_detail:{kwargs['pk']}"
        # cached_response = cache.get(cache_key)
        # if cached_response:
        #     return Response(cached_response)

        response = super().retrieve(request, *args, **kwargs)
        # cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper(tags="ProductSize", model="Product size")
    def create(self, *args, **kwargs):
        response = super().create(*args, **kwargs)
        # cache.delete("product_size_list:*")
        # cache.delete("product_size_detail:*")
        # cache.delete("product_list:*")
        # cache.delete("product_detail:*")
        # cache.delete("search:*")
        # cache.delete("search_suggestions:*")
        return response

    @swagger_helper(tags="ProductSize", model="Product size")
    def partial_update(self, *args, **kwargs):
        response = super().partial_update(*args, **kwargs)
        # cache.delete("product_size_list:*")
        # cache.delete(f"product_size_detail:{kwargs['pk']}")
        # cache.delete("product_list:*")
        # cache.delete("product_detail:*")
        # cache.delete("search:*")
        # cache.delete("search_suggestions:*")
        return response

    @swagger_helper(tags="ProductSize", model="Product size")
    def destroy(self, *args, **kwargs):
        response = super().destroy(*args, **kwargs)
        # cache.delete("product_size_list:*")
        # cache.delete(f"product_size_detail:{kwargs['pk']}")
        # cache.delete("product_list:*")
        # cache.delete("product_detail:*")
        # cache.delete("search:*")
        # cache.delete("search_suggestions:*")
        return response
