from rest_framework import serializers
from .models import Product, ProductSubCategory, ProductCategory, ProductSize


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["id", "name"]
        read_only_fields = ["id"]


class ProductSubCategoryViewSerializer(serializers.ModelSerializer):
    category = ProductCategorySerializer()

    class Meta:
        model = ProductSubCategory
        fields = ["id", "category", "name"]
        read_only_fields = ["id"]


class ProductSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSubCategory
        fields = ["id", "category", "name"]
        read_only_fields = ["id"]


class ProductCategoryDetailSerializer(serializers.ModelSerializer):
    sub_categories = ProductSubCategorySerializer(many=True, read_only=True, source="subcategories")

    class Meta:
        model = ProductCategory
        fields = ["id", "name", "sub_categories"]
        read_only_fields = ["id"]


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ["id", "name", "description", "sub_category", "colour", "image1", "image2", "image3", "discounted_price", "price", "is_available"]
        read_only_fields = ["id"]


class ProductViewSerializer(serializers.ModelSerializer):
    sub_category = ProductSubCategoryViewSerializer()

    class Meta:
        model = Product
        fields = ["id", "name", "description", "sub_category", "colour", "image1", "image2", "image3", "discounted_price", "price", "is_available"]
        read_only_fields = ["id"]


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ["id", "product", "size", "quantity"]
