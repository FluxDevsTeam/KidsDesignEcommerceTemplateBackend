from django.db.models import Sum, Min
from rest_framework import serializers
from .models import InventoryItem, InventorySubCategory, InventoryCategory, ProductSize


class InventoryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryCategory
        fields = ["id", "name", "index", "created_by", "edited_by", "edited_at"]
        read_only_fields = ["id"]


class InventorySubCategoryViewSerializer(serializers.ModelSerializer):
    category = InventoryCategorySerializer()

    class Meta:
        model = InventorySubCategory
        fields = ["id", "category", "name"]
        read_only_fields = ["id"]


class InventorySubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventorySubCategory
        fields = ["id", "category", "name"]
        read_only_fields = ["id"]


class InventoryCategoryDetailSerializer(serializers.ModelSerializer):
    sub_categories = InventorySubCategorySerializer(many=True, read_only=True, source="subcategories")

    class Meta:
        model = InventoryCategory
        fields = ["id", "name", "sub_categories"]
        read_only_fields = ["id"]


class InventoryItemSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    undiscounted_price = serializers.SerializerMethodField()

    class Meta:
        model = InventoryItem
        fields = '__all__'
        read_only_fields = ["id", "date_created", "date_updated"]

    def get_price(self, obj):
        min_price_size = obj.sizes.filter(price__gt=0).order_by("price").first()
        return min_price_size.price if min_price_size else 0

    def get_undiscounted_price(self, obj):
        min_price_size = obj.sizes.filter(price__gt=0).order_by("price").first()
        return min_price_size.undiscounted_price if min_price_size and min_price_size.undiscounted_price is not None else 0


class InventoryItemViewSerializer(serializers.ModelSerializer):
    sub_category = InventorySubCategoryViewSerializer()
    total_quantity = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    undiscounted_price = serializers.SerializerMethodField()
    default_size_id = serializers.SerializerMethodField()

    class Meta:
        model = InventoryItem
        fields = ["id", "name", "sub_category", "description", "image", "image1", "image2", "image3", "colour", "stock", "cost_price", "selling_price", "dimensions", "archived", "operation_type", "is_available", "latest_item", "latest_item_position", "top_selling_items", "top_selling_position", "unlimited", "production_days", "weight", "dimensional_size", "created_by", "edited_by", "edited_at", "date_created", "date_updated", "total_quantity", "price", "undiscounted_price", "default_size_id"]
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


class InventoryItemSimpleViewSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    undiscounted_price = serializers.SerializerMethodField()

    class Meta:
        model = InventoryItem
        fields = ["id", "name", "image1", "price", "undiscounted_price", "unlimited", "category", "sub_category", "description", "image", "image2", "image3", "colour", "stock", "cost_price", "selling_price", "dimensions", "archived", "operation_type", "is_available", "latest_item", "latest_item_position", "top_selling_items", "top_selling_position", "production_days", "weight", "dimensional_size", "created_by", "edited_by", "edited_at", "date_created", "date_updated"]
        read_only_fields = ["id", "name", "image1", "price", "undiscounted_price"]

    def get_price(self, obj):
        min_price_size = obj.sizes.filter(price__gt=0).order_by("price").first()
        return min_price_size.price if min_price_size else 0

    def get_undiscounted_price(self, obj):
        min_price_size = obj.sizes.filter(price__gt=0).order_by("price").first()
        return min_price_size.undiscounted_price if min_price_size and min_price_size.undiscounted_price is not None else 0


class InventoryItemWishlistViewSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    undiscounted_price = serializers.SerializerMethodField()
    sub_category = InventorySubCategoryViewSerializer()
    
    class Meta:
        model = InventoryItem
        fields = ["id", "name", "image1", "price", "undiscounted_price", "sub_category", "unlimited", "category", "description", "image", "image2", "image3", "colour", "stock", "cost_price", "selling_price", "dimensions", "archived", "operation_type", "is_available", "latest_item", "latest_item_position", "top_selling_items", "top_selling_position", "production_days", "weight", "dimensional_size", "created_by", "edited_by", "edited_at", "date_created", "date_updated"]
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
        fields = ["id", "product", "size", "stock", "quantity", "price", "undiscounted_price", "price_adjustment", "is_available", "created_by", "edited_by", "edited_at", "date_created", "date_updated"]


class ProductSizeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = ["id", "name", "image1", "unlimited", "category", "sub_category", "description", "image", "image2", "image3", "colour", "stock", "cost_price", "selling_price", "dimensions", "archived", "operation_type", "is_available", "latest_item", "latest_item_position", "top_selling_items", "top_selling_position", "production_days", "weight", "dimensional_size", "created_by", "edited_by", "edited_at", "date_created", "date_updated"]
        read_only_fields = ["id", "name", "image1", "price", "undiscounted_price"]


class ProductSizeViewSerializer(serializers.ModelSerializer):
    product = ProductSizeDetailSerializer()

    class Meta:
        model = ProductSize
        fields = ["id", "product", "size", "quantity", "undiscounted_price", "price", "stock", "price_adjustment", "is_available", "created_by", "edited_by", "edited_at", "date_created", "date_updated"]


class SimpleProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ["id", "size", "quantity", "undiscounted_price", "price", "stock", "price_adjustment", "is_available", "created_by", "edited_by", "edited_at", "date_created", "date_updated"]


class InventoryItemDetailViewSerializer(serializers.ModelSerializer):
    sub_category = InventorySubCategoryViewSerializer()
    total_quantity = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    undiscounted_price = serializers.SerializerMethodField()
    default_size_id = serializers.SerializerMethodField()
    sizes = SimpleProductSizeSerializer(many=True, read_only=True)

    class Meta:
        model = InventoryItem
        fields = ["id", "name", "description", "total_quantity", "sub_category", "colour", "image1", "image2", "image3", "undiscounted_price", "price", "default_size_id", "is_available", "latest_item", "latest_item_position", "dimensional_size", "weight", "top_selling_items", "top_selling_position", "date_created", "date_updated", "unlimited", "production_days", "sizes", "category", "image", "stock", "cost_price", "selling_price", "dimensions", "archived", "operation_type", "created_by", "edited_by", "edited_at"]
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
