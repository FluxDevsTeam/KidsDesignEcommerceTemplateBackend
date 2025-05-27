from rest_framework import serializers
from .models import Wishlist
from ..products.serializers import ProductWishlistViewSerializer


class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ["id", "product", "date"]
        read_only_fields = ["id"]


class WishlistViewSerializer(serializers.ModelSerializer):
    product = ProductWishlistViewSerializer()

    class Meta:
        model = Wishlist
        fields = ["id", "product", "date"]
        read_only_fields = ["id"]
