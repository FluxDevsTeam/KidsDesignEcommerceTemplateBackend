# @swagger_helper(tags="Product", model="Product")
# def partial_update(self, request, *args, **kwargs):
#     instance = self.get_object()
#     serializer = self.get_serializer(instance, data=request.data, partial=True)
#     serializer.is_valid(raise_exception=True)
#
#     with transaction.atomic():
#         data = serializer.validated_data
#
#         # Reshuffle latest_item_position if provided
#         if 'latest_item_position' in data:
#             new_position = data['latest_item_position']
#             if new_position is not None:  # Only reshuffle for non-None positions
#                 Product.objects.filter(
#                     latest_item=True,
#                     latest_item_position__gte=new_position,
#                     latest_item_position__isnull=False
#                 ).exclude(
#                     id=instance.id
#                 ).update(
#                     latest_item_position=F('latest_item_position') + 1
#                 )
#                 # Limit to 8, set excess to None
#                 excess = Product.objects.filter(
#                     latest_item=True,
#                     latest_item_position__gt=8
#                 ).exclude(id=instance.id)
#                 if excess.exists():
#                     excess.update(latest_item_position=None, latest_item=False)
#             elif instance.latest_item_position is not None:
#                 # If setting to None, keep flag consistent
#                 data['latest_item'] = False
#
#         # Reshuffle top_selling_position if provided
#         if 'top_selling_position' in data:
#             new_position = data['top_selling_position']
#             if new_position is not None:
#                 Product.objects.filter(
#                     top_selling_items=True,
#                     top_selling_position__gte=new_position,
#                     top_selling_position__isnull=False
#                 ).exclude(
#                     id=instance.id
#                 ).update(
#                     top_selling_position=F('top_selling_position') + 1
#                 )
#                 excess = Product.objects.filter(
#                     top_selling_items=True,
#                     top_selling_position__gt=8
#                 ).exclude(id=instance.id)
#                 if excess.exists():
#                     excess.update(top_selling_position=None, top_selling_items=False)
#             elif instance.top_selling_position is not None:
#                 data['top_selling_items'] = False
#
#         # Save the updated instance
#         serializer.save()
#
#     return Response(serializer.data)
#
# @action(methods=['GET'], detail=False)
# def homepage(self, request):
#     all_products = Product.objects.select_related('sub_category__category').all()
#     categories = list(ProductCategory.objects.all())
#
#     def get_positioned_and_cycle(products, is_flag, position_field):
#         # Positioned items (up to 8, non-None positions)
#         positioned = sorted(
#             [p for p in products if getattr(p, is_flag) and getattr(p, position_field) is not None],
#             key=lambda x: getattr(x, position_field)
#         )[:8]
#         positioned_ids = {p.id for p in positioned}
#         remaining = [p for p in products if p.id not in positioned_ids]
#         by_category = {}
#         for p in remaining:
#             cat_id = p.sub_category.category.id if p.sub_category else None
#             if cat_id:
#                 if cat_id not in by_category:
#                     by_category[cat_id] = []
#                 by_category[cat_id].append(p)
#
#         cycle = []
#         used_ids = set(positioned_ids)
#         while any(by_category.get(cat.id, []) for cat in categories):
#             for category in categories:
#                 available = [
#                     p for p in by_category.get(category.id, [])
#                     if p.id not in used_ids
#                 ]
#                 if available:
#                     selected = random.sample(available, min(2, len(available)))
#                     cycle.extend(selected)
#                     used_ids.update(p.id for p in selected)
#         return positioned + cycle
#
#     latest_items = get_positioned_and_cycle(
#         all_products,
#         is_flag='latest_item',
#         position_field='latest_item_position'
#     )
#     top_selling_items = get_positioned_and_cycle(
#         all_products,
#         is_flag='top_selling_items',
#         position_field='top_selling_position'
#     )
#
#     latest_paginator = self.pagination_class()
#     top_selling_paginator = self.pagination_class()
#
#     latest_paginator.page_query_param = 'page_latest'
#     top_selling_paginator.page_query_param = 'page_top'
#     latest_paginator.page_size_query_param = 'page_size_latest'
#     top_selling_paginator.page_size_query_param = 'page_size_top'
#
#     page_latest = request.query_params.get('page_latest', 1)
#     page_top = request.query_params.get('page_top', 1)
#
#     latest_page = latest_paginator.paginate_queryset(latest_items, request, view=self)
#     top_selling_page = top_selling_paginator.paginate_queryset(top_selling_items, request, view=self)
#
#     latest_serializer = self.get_serializer(latest_page, many=True)
#     top_selling_serializer = self.get_serializer(top_selling_page, many=True)
#
#     return Response({
#         "latest_items": latest_paginator.get_paginated_response(latest_serializer.data).data,
#         "top_selling_items": top_selling_paginator.get_paginated_response(top_selling_serializer.data).data
#     })




# caching
# Configure Django Settings (settings.py):
#
# python
#
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         }
#     }
# }
#
# Updated views.py with Redis Caching
# Here’s your ApiProduct viewset with Redis caching added:
# python
#
# from rest_framework import viewsets
# from django.core.cache import cache
# import json
# from .models import Product
# from .serializers import ProductViewSerializer, ProductSerializer
# from .pagination import CustomPagination
# from rest_framework.response import Response
#
# class ApiProduct(viewsets.ModelViewSet):
#     http_method_names = ["get", "post", "patch", "delete", "head", "options"]
#     queryset = Product.objects.select_related('sub_category__category').all()
#     pagination_class = CustomPagination
#
#     def get_serializer_class(self):
#         if self.request.method == "GET":
#             return ProductViewSerializer
#         return ProductSerializer
#
#     @swagger_helper(tags="Product", model="Product")
#     def list(self, *args, **kwargs):
#         # Cache key based on query params
#         query_params = dict(self.request.query_params)
#         cache_key = f"product_list:{json.dumps(query_params, sort_keys=True)}"
#         cache_timeout = 300  # 5 minutes
#
#         # Check cache
#         cached_response = cache.get(cache_key)
#         if cached_response:
#             return Response(cached_response)
#
#         # Fetch from DB and cache
#         response = super().list(*args, **kwargs)
#         cache.set(cache_key, response.data, cache_timeout)
#         return response
#
#     @swagger_helper(tags="Product", model="Product")
#     def retrieve(self, *args, **kwargs):
#         # Cache key for individual product
#         cache_key = f"product_detail:{kwargs['pk']}"
#         cache_timeout = 3600  # 1 hour
#
#         # Check cache
#         cached_response = cache.get(cache_key)
#         if cached_response:
#             return Response(cached_response)
#
#         # Fetch from DB and cache
#         response = super().retrieve(*args, **kwargs)
#         cache.set(cache_key, response.data, cache_timeout)
#         return response
#
#     @swagger_helper(tags="Product", model="Product")
#     def create(self, *args, **kwargs):
#         # Create product
#         response = super().create(*args, **kwargs)
#         # Invalidate list cache
#         cache.delete_pattern("product_list:*")
#         return response
#
#     @swagger_helper(tags="Product", model="Product")
#     def destroy(self, *args, **kwargs):
#         # Delete product
#         response = super().destroy(*args, **kwargs)
#         # Invalidate caches
#         cache.delete(f"product_detail:{kwargs['pk']}")
#         cache.delete_pattern("product_list:*")
#         return response
#
#     @swagger_helper(tags="Product", model="Product")
#     def partial_update(self, *args, **kwargs):
#         # Update product
#         response = super().partial_update(*args, **kwargs)
#         # Invalidate caches
#         cache.delete(f"product_detail:{kwargs['pk']}")
#         cache.delete_pattern("product_list:*")
#         return response
#

# Where Else to Cache in an E-Commerce Site?
# Beyond the product list page, Redis can optimize various parts of an e-commerce application. Here’s a breakdown:
# 1. Product Detail Pages
# What: Individual product data (e.g., /products/1/ via retrieve).
#
# Why: Popular products are viewed repeatedly; caching avoids redundant DB hits.
#
# How: Cache serialized response (e.g., product_detail:{pk}).
#
# TTL: 1 hour (or until updated).
#
# Gain: ~1ms vs. 10–50ms per request.
#
# 2. Homepage/Featured Products
# What: Featured sections like latest_items and top_selling_items (your homepage action).
#
# Why: High read traffic, semi-static data (positioned items + random cycle).
#
# How: Cache paginated responses (e.g., homepage:latest:{params}, homepage:top:{params}).
#
# TTL: 5–15 minutes.
#
# Gain: Avoids sorting/randomization overhead, ~1ms vs. 50–200ms.
#
# 3. Category/Subcategory Listings
# What: Product lists by category (e.g., /products/?category=Clothing).
#
# Why: Common browsing pattern, stable within short timeframes.
#
# How: Cache filtered queryset (e.g., products:category:{category_id}:page:{page}).
#
# TTL: 15–30 minutes.
#
# Gain: Reduces join queries (e.g., sub_category__category).
#
# 4. Shopping Cart
# What: User’s cart contents.
#
# Why: Frequent reads during shopping, avoids DB hits per page load.
#
# How: Store as a Redis hash or list (e.g., cart:user:{user_id} with product IDs and quantities).
#
# TTL: Session duration or until checkout.
#
# Gain: ~1ms vs. 10–50ms, plus atomic updates (e.g., HINCRBY for quantity).
#
# 5. Inventory/Stock Levels
# What: Stock quantities (e.g., ProductSize.quantity).
#
# Why: High read/write during checkout; caching reduces contention.
#
# How: Redis integers (e.g., stock:product:{product_id}:size:{size_id}), sync with DB on miss.
#
# TTL: None (persistent), updated on stock changes.
#
# Gain: Atomic operations (DECR) in ~1ms vs. DB locks.
#
# 6. Pricing and Discounts
# What: Product prices, discount rules.
#
# Why: Avoids recalculating discounts or querying price tables.
#
# How: Cache as key-value pairs (e.g., price:product:{product_id}) or hashes.
#
# TTL: 1 hour or until price changes.
#
# Gain: ~1ms vs. 10–50ms for complex price logic.
#
# 7. User Recommendations
# What: Personalized product suggestions.
#
# Why: Computation-heavy (e.g., collaborative filtering); caching precomputed results speeds up delivery.
#
# How: Redis sorted sets (e.g., recommendations:user:{user_id} with scores).
#
# TTL: 1 day or until recalculated.
#
# Gain: ~1ms vs. seconds for real-time computation.
#
# 8. Static Data
# What: Categories (ProductCategory), subcategories (ProductSubCategory), site metadata.
#
# Why: Rarely changes, small datasets, frequent reads.
#
# How: Cache as JSON (e.g., categories:all, subcategories:{category_id}).
#
# TTL: 24 hours or until updated.
#
# Gain: ~1ms vs. 5–20ms for small table queries.
#
# 9. Order History
# What: User’s past orders (summary or list).
#
# Why: Frequent access for account pages, stable data.
#
# How: Cache as serialized JSON (e.g., orders:user:{user_id}:page:{page}).
#
# TTL: 1 day or until new order.
#
# Gain: ~1ms vs. 50–200ms for order joins.
#
# 10. Session Data
# What: User session state (e.g., login status, preferences).
#
# Why: Faster than Django’s default DB-backed sessions.
#
# How: Use Django’s Redis session backend (SESSION_ENGINE = 'django.contrib.sessions.backends.cache').
#
# TTL: Session duration.
#
# Gain: ~1ms vs. 10–20ms per request.
#
# Best Places to Cache in Your E-Commerce Site
# Area
#
# Cache Key Example
#
# TTL
#
# Benefit
#
# Product List
#
# product_list:{params}
#
# 5–15 min
#
# High-traffic page
#
# Product Detail
#
# product_detail:{pk}
#
# 1 hr
#
# Popular items
#
# Homepage
#
# homepage:latest:{params}
#
# 5–15 min
#
# Featured sections
#
# Categories
#
# products:category:{id}
#
# 30 min
#
# Browsing efficiency
#
# Cart
#
# cart:user:{user_id}
#
# Session
#
# Fast checkout
#
# Stock
#
# stock:product:{id}:size:{id}
#
# Persistent
#
# Inventory checks
#
# Recommendations
#
# recommendations:user:{id}
#
# 1 day
#
# Slow computation
#
# Static Data
#
# categories:all
#
# 24 hr
#
# Small, stable tables

