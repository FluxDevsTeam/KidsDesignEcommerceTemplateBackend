from rest_framework import serializers
from .models import Wishlist
from ..products.serializers import ProductSimpleViewSerializer


class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ["id", "product", "date"]
        read_only_fields = ["id"]


class WishlistViewSerializer(serializers.ModelSerializer):
    product = ProductSimpleViewSerializer()

    class Meta:
        model = Wishlist
        fields = ["id", "product", "date"]
        read_only_fields = ["id"]
