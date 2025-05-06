from django.db.models import Sum, Min
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
    price = serializers.SerializerMethodField()
    undiscounted_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "description", "sub_category", "colour", "image1", "image2", "image3", "undiscounted_price", "price", "is_available", "latest_item",
                  "latest_item_position", "dimensional_size", "weight", "top_selling_items", "top_selling_position", "date_created", "date_updated", "unlimited", "production_days"]
        read_only_fields = ["id", "date_created", "date_updated"]

    def get_price(self, obj):
        min_price_size = obj.sizes.filter(price__gt=0).order_by("price").first()
        return min_price_size.price if min_price_size else 0

    def get_undiscounted_price(self, obj):
        min_price_size = obj.sizes.filter(price__gt=0).order_by("price").first()
        return min_price_size.undiscounted_price if min_price_size and min_price_size.undiscounted_price is not None else 0


class ProductViewSerializer(serializers.ModelSerializer):
    sub_category = ProductSubCategoryViewSerializer()
    total_quantity = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    undiscounted_price = serializers.SerializerMethodField()
    default_size_id = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "description", "total_quantity", "sub_category", "colour", "image1", "image2", "image3", "undiscounted_price", "price", "default_size_id", "is_available", "latest_item",
                  "latest_item_position", "dimensional_size", "weight", "top_selling_items", "top_selling_position", "date_created", "date_updated", "unlimited", "production_days"]
        read_only_fields = ["id", "date_created", "date_updated"]

    def get_total_quantity(self, obj):
        return obj.sizes.aggregate(total=Sum("quantity"))["total"] or None

    def get_price(self, obj):
        min_price_size = obj.sizes.filter(price__gt=0).order_by("price").first()
        return min_price_size.price if min_price_size else None

    def get_undiscounted_price(self, obj):
        min_price_size = obj.sizes.filter(price__gt=0).order_by("price").first()
        return min_price_size.undiscounted_price if min_price_size and min_price_size.undiscounted_price is not None else None

    def get_default_size_id(self, obj):
        min_price_size = obj.sizes.filter(price__gt=0).order_by("price").first()
        return min_price_size.id if min_price_size and min_price_size.id is not None else None


class ProductSimpleViewSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    undiscounted_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "image1", "price", "undiscounted_price", "price", "unlimited"]
        read_only_fields = ["id", "name", "image1", "price", "undiscounted_price"]

    def get_price(self, obj):
        min_price_size = obj.sizes.filter(price__gt=0).order_by("price").first()
        return min_price_size.price if min_price_size else 0

    def get_undiscounted_price(self, obj):
        min_price_size = obj.sizes.filter(price__gt=0).order_by("price").first()
        return min_price_size.undiscounted_price if min_price_size and min_price_size.undiscounted_price is not None else 0


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ["id", "size", "quantity", "undiscounted_price", "price"]


class ProductSizeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "image1", "unlimited"]
        read_only_fields = ["id", "name", "image1", "price", "undiscounted_price"]


class ProductSizeViewSerializer(serializers.ModelSerializer):
    product = ProductSizeDetailSerializer()

    class Meta:
        model = ProductSize
        fields = ["id", "product", "size", "quantity", "undiscounted_price", "price"]


class SimpleProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ["id", "size", "quantity", "undiscounted_price", "price"]


class ProductDetailViewSerializer(serializers.ModelSerializer):
    sub_category = ProductSubCategoryViewSerializer()
    total_quantity = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    undiscounted_price = serializers.SerializerMethodField()
    default_size_id = serializers.SerializerMethodField()
    sizes = SimpleProductSizeSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "total_quantity", "sub_category", "colour", "image1", "image2", "image3", "undiscounted_price", "price", "default_size_id", "is_available", "latest_item",
                  "latest_item_position", "dimensional_size", "weight", "top_selling_items", "top_selling_position", "date_created", "date_updated", "unlimited", "production_days", "sizes"]
        read_only_fields = ["id", "date_created", "date_updated"]

    def get_total_quantity(self, obj):
        return obj.sizes.aggregate(total=Sum("quantity"))["total"] or None

    def get_price(self, obj):
        min_price_size = obj.sizes.filter(price__gt=0).order_by("price").first()
        return min_price_size.price if min_price_size else None

    def get_undiscounted_price(self, obj):
        min_price_size = obj.sizes.filter(price__gt=0).order_by("price").first()
        return min_price_size.undiscounted_price if min_price_size and min_price_size.undiscounted_price is not None else None

    def get_default_size_id(self, obj):
        min_price_size = obj.sizes.filter(price__gt=0).order_by("price").first()
        return min_price_size.id if min_price_size and min_price_size.id is not None else None
