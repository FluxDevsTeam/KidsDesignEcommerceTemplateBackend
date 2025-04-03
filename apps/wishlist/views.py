from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from .serializers import WishlistViewSerializer, WishlistSerializer
from .models import Wishlist
from .pagination import CustomPagination
from .utils import swagger_helper


class ApiWishlist(ModelViewSet):
    http_method_names = ["get", "post", "delete", "head", "options", ]
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return WishlistViewSerializer
        return WishlistSerializer

    @swagger_helper("Wishlist", "wishlist")
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_helper("Wishlist", "wishlist")
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @swagger_helper("Wishlist", "wishlist")
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)

    @swagger_helper("Wishlist", "wishlist")
    def destroy(self, *args, **kwargs):
        return super().destroy(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

