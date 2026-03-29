from rest_framework import serializers
from .models import Wishlist
from ..products.serializers import InventoryItemWishlistViewSerializer


class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ["id", "product", "date"]
        read_only_fields = ["id"]


class WishlistViewSerializer(serializers.ModelSerializer):
    product = InventoryItemWishlistViewSerializer()

    class Meta:
        model = Wishlist
        fields = ["id", "product", "date"]
        read_only_fields = ["id"]
