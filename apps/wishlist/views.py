from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from .serializers import WishlistViewSerializer, WishlistSerializer
from .models import Wishlist
from .pagination import CustomPagination
from .utils import swagger_helper
from django.core.cache import cache
import json


class ApiWishlist(ModelViewSet):
    http_method_names = ["get", "post", "delete", "head", "options"]
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return WishlistViewSerializer
        return WishlistSerializer

    @swagger_helper("Wishlist", "wishlist")
    def list(self, request, *args, **kwargs):
        cache_timeout = 300
        cache_params = dict(request.query_params)
        cache_key = f"wishlist_list:{request.user.id}:{json.dumps(cache_params, sort_keys=True)}"

        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper("Wishlist", "wishlist")
    def retrieve(self, request, *args, **kwargs):
        cache_timeout = 300
        wishlist_pk = kwargs["pk"]
        cache_key = f"wishlist_detail:{request.user.id}:{wishlist_pk}"

        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, cache_timeout)
        return response

    @swagger_helper("Wishlist", "wishlist")
    def create(self, *args, **kwargs):
        response = super().create(*args, **kwargs)
        cache.delete_pattern(f"wishlist_list:{self.request.user.id}:*")
        return response

    @swagger_helper("Wishlist", "wishlist")
    def destroy(self, *args, **kwargs):
        response = super().destroy(*args, **kwargs)
        cache.delete_pattern(f"wishlist_list:{self.request.user.id}:*")
        return response

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)